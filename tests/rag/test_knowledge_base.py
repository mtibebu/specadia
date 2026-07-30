import json
import sqlite3
import sys
from types import SimpleNamespace

import pytest

from rag.knowledge_base import (
    KnowledgeBaseError,
    build_file_collection,
    chunk_text,
    collection_status,
    discover_files,
    ingest_sqlite,
    list_collections,
    make_collection_retriever,
    read_document,
    validate_read_only_sql,
)


def test_discovers_supported_files_recursively_in_stable_order(tmp_path):
  (tmp_path / "nested").mkdir()
  (tmp_path / "z.txt").write_text("z")
  (tmp_path / "nested" / "a.md").write_text("a")
  (tmp_path / "ignored.csv").write_text("no")

  files = discover_files([tmp_path])

  assert [path.name for path in files] == ["a.md", "z.txt"]


def test_discovery_rejects_explicit_symlink_and_skips_nested_symlink(tmp_path):
  outside = tmp_path / "secret.txt"
  outside.write_text("secret")
  source = tmp_path / "docs"
  source.mkdir()
  nested_link = source / "linked-secret.txt"
  nested_link.symlink_to(outside)

  assert discover_files([source]) == []
  with pytest.raises(KnowledgeBaseError, match="Symbolic-link"):
    discover_files([nested_link])


def test_reads_json_deterministically(tmp_path):
  source = tmp_path / "domain.json"
  source.write_text('{"z": 2, "a": 1}')

  assert read_document(source).index('"a"') < read_document(source).index('"z"')


def test_extracts_text_from_pdf(tmp_path, monkeypatch):
  source = tmp_path / "manual.pdf"
  source.write_bytes(b"%PDF mocked")
  reader = SimpleNamespace(
      pages=[
          SimpleNamespace(extract_text=lambda: "First page"),
          SimpleNamespace(extract_text=lambda: "Second page"),
      ]
  )
  monkeypatch.setitem(sys.modules, "pypdf", SimpleNamespace(PdfReader=lambda _: reader))

  assert read_document(source) == "First page\n\nSecond page"


def test_chunking_is_bounded_and_overlapping():
  text = " ".join(f"word-{index}" for index in range(200))

  chunks = chunk_text(text, chunk_size=120, chunk_overlap=20)

  assert len(chunks) > 2
  assert all(len(chunk) <= 120 for chunk in chunks)


def test_build_incremental_status_and_retrieval(tmp_path):
  source = tmp_path / "docs"
  source.mkdir()
  (source / "policy.md").write_text(
      "# Settlement\nOrbital claims require a xenon escrow certificate before launch."
  )
  (source / "rules.txt").write_text(
      "Underwater permits require a coral impact review and pressure audit."
  )
  index_dir = tmp_path / "indexes"

  first = build_file_collection([source], collection="space-law", index_dir=index_dir)
  second = build_file_collection([source], collection="space-law", index_dir=index_dir)
  results = make_collection_retriever("space-law", index_dir)("xenon launch escrow")

  assert first.documents == 2
  assert second.added_sources == 0
  assert second.unchanged_sources == 2
  assert "xenon escrow certificate" in results[0]
  assert collection_status("space-law", index_dir)["embedding"]["provider"] == "local"
  assert list_collections(index_dir)[0]["collection"] == "space-law"


def test_build_rejects_symlinked_collection_destination(tmp_path):
  source = tmp_path / "facts.txt"
  source.write_text("Safe fact.")
  index_dir = tmp_path / "indexes"
  index_dir.mkdir()
  outside = tmp_path / "outside"
  outside.mkdir()
  (index_dir / "facts").symlink_to(outside, target_is_directory=True)

  with pytest.raises(KnowledgeBaseError, match="symbolic link"):
    build_file_collection([source], collection="facts", index_dir=index_dir)
  assert list(outside.iterdir()) == []


@pytest.mark.parametrize("artifact", ["index.faiss", "chunks.json"])
def test_retriever_rejects_tampered_collection_artifacts(tmp_path, artifact):
  source = tmp_path / "facts.txt"
  source.write_text("Trusted fact.")
  index_dir = tmp_path / "indexes"
  build_file_collection([source], collection="facts", index_dir=index_dir)
  path = index_dir / "facts" / artifact
  path.write_bytes(path.read_bytes() + b"tampered")

  with pytest.raises(KnowledgeBaseError, match="integrity"):
    make_collection_retriever("facts", index_dir)("trusted")


def test_retriever_rejects_collection_without_integrity_metadata(tmp_path):
  source = tmp_path / "facts.txt"
  source.write_text("Trusted fact.")
  index_dir = tmp_path / "indexes"
  build_file_collection([source], collection="facts", index_dir=index_dir)
  manifest_path = index_dir / "facts" / "manifest.json"
  manifest = json.loads(manifest_path.read_text())
  manifest.pop("artifacts")
  manifest_path.write_text(json.dumps(manifest))

  with pytest.raises(KnowledgeBaseError, match="predates integrity"):
    make_collection_retriever("facts", index_dir)("trusted")


def test_changed_file_replaces_old_chunks(tmp_path):
  source = tmp_path / "facts.txt"
  source.write_text("Mercury protocol alpha.")
  index_dir = tmp_path / "indexes"
  build_file_collection([source], collection="facts", index_dir=index_dir)
  source.write_text("Neptune protocol beta.")

  build_file_collection([source], collection="facts", index_dir=index_dir)
  chunks = json.loads((index_dir / "facts" / "chunks.json").read_text())

  assert len(chunks) == 1
  assert "Neptune" in chunks[0]["chunk"]
  assert "Mercury" not in chunks[0]["chunk"]


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM facts",
        "PRAGMA table_info(facts)",
        "SELECT * FROM facts; DROP TABLE facts",
        "SELECT * FROM facts -- comment",
    ],
)
def test_rejects_non_read_only_sql(query):
  with pytest.raises(KnowledgeBaseError, match="read-only"):
    validate_read_only_sql(query)


def test_ingests_sqlite_read_only_without_storing_query_or_path(tmp_path):
  database = tmp_path / "private.sqlite"
  connection = sqlite3.connect(database)
  connection.execute("CREATE TABLE policies (topic TEXT, rule TEXT)")
  connection.executemany(
      "INSERT INTO policies VALUES (?, ?)",
      [
          ("aviation", "Runway drones require beacon telemetry."),
          ("maritime", "Cargo manifests require harbor signatures."),
      ],
  )
  connection.commit()
  connection.close()
  index_dir = tmp_path / "indexes"

  result = ingest_sqlite(
      database,
      table="policies",
      collection="regulations",
      index_dir=index_dir,
  )
  manifest_text = (index_dir / "regulations" / "manifest.json").read_text()
  results = make_collection_retriever("regulations", index_dir)("runway beacon drone")

  assert result.documents == 1
  assert "Runway drones require beacon telemetry" in results[0]
  assert str(database) not in manifest_text
  assert "SELECT *" not in manifest_text


def test_sqlite_row_limit_is_enforced(tmp_path):
  database = tmp_path / "rows.sqlite"
  connection = sqlite3.connect(database)
  connection.execute("CREATE TABLE facts (value TEXT)")
  connection.executemany("INSERT INTO facts VALUES (?)", [("a",), ("b",)])
  connection.commit()
  connection.close()

  with pytest.raises(KnowledgeBaseError, match="row limit"):
    ingest_sqlite(database, table="facts", index_dir=tmp_path / "index", max_rows=1)
