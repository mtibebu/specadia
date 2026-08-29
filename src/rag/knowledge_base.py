"""Build and query user-owned, persistent Specadia knowledge-base collections."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import time
from typing import Any

SUPPORTED_SUFFIXES = frozenset({".md", ".txt", ".pdf", ".json"})
DEFAULT_INDEX_DIR = Path(".specadia/rag")
DEFAULT_COLLECTION = "default"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150
DEFAULT_MAX_FILE_BYTES = 25 * 1024 * 1024
DEFAULT_MAX_ROWS = 10_000
DEFAULT_MAX_CELL_CHARS = 20_000
DEFAULT_SQL_TIMEOUT_SECONDS = 5.0
HASH_DIMENSION = 768
_COLLECTION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_TOKEN_RE = re.compile(r"[\w][\w.-]*", re.UNICODE)
_READ_ONLY_SQL_RE = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)
_FORBIDDEN_SQL_RE = re.compile(
    r"\b(ATTACH|DETACH|PRAGMA|INSERT|UPDATE|DELETE|REPLACE|CREATE|ALTER|DROP|VACUUM|REINDEX)\b",
    re.IGNORECASE,
)


class KnowledgeBaseError(ValueError):
  """Raised when an index or source is invalid."""


@dataclass(frozen=True)
class BuildResult:
  collection: str
  documents: int
  chunks: int
  added_sources: int
  unchanged_sources: int
  collection_dir: Path


def collection_dir(
    collection: str = DEFAULT_COLLECTION, index_dir: Path = DEFAULT_INDEX_DIR
) -> Path:
  """Resolve a validated collection below the configured index root."""
  if not _COLLECTION_RE.fullmatch(collection):
    raise KnowledgeBaseError(
        "Collection names must be 1-64 letters, numbers, dots, underscores, or hyphens."
    )
  root = Path(index_dir).expanduser().resolve()
  destination = root / collection
  if destination.is_symlink():
    raise KnowledgeBaseError(
        f"Collection '{collection}' must not be a symbolic link: {destination}"
    )
  if destination.exists() and destination.resolve().parent != root:
    raise KnowledgeBaseError(f"Collection '{collection}' escapes the configured index directory.")
  return destination


def discover_files(sources: Iterable[Path]) -> list[Path]:
  """Return supported real files without following symbolic links."""
  discovered: set[Path] = set()
  for raw_source in sources:
    supplied = Path(raw_source).expanduser()
    if supplied.is_symlink():
      raise KnowledgeBaseError(f"Symbolic-link sources are not allowed: {supplied}")
    source = supplied.resolve()
    if not source.exists():
      raise KnowledgeBaseError(f"Source does not exist: {source}")
    if source.is_file():
      if source.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise KnowledgeBaseError(
            f"Unsupported file type {source.suffix or '(none)'}: {source}. "
            f"Supported types: {', '.join(sorted(SUPPORTED_SUFFIXES))}"
        )
      discovered.add(source)
    else:
      for path in source.rglob("*"):
        if path.is_symlink() or not path.is_file():
          continue
        resolved_path = path.resolve()
        if (
            resolved_path.is_relative_to(source)
            and resolved_path.suffix.lower() in SUPPORTED_SUFFIXES
        ):
          discovered.add(resolved_path)
  return sorted(discovered, key=lambda path: path.as_posix())


def read_document(path: Path, *, max_file_bytes: int = DEFAULT_MAX_FILE_BYTES) -> str:
  """Extract bounded text from a supported document."""
  if path.stat().st_size > max_file_bytes:
    raise KnowledgeBaseError(f"File exceeds the {max_file_bytes:,}-byte ingestion limit: {path}")
  suffix = path.suffix.lower()
  if suffix in {".md", ".txt"}:
    return path.read_text(encoding="utf-8", errors="replace")
  if suffix == ".json":
    try:
      value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
      raise KnowledgeBaseError(f"Invalid JSON in {path}: {error}") from error
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
  if suffix == ".pdf":
    try:
      from pypdf import PdfReader
    except ImportError as error:
      raise KnowledgeBaseError(
          "PDF ingestion requires the RAG extra: pip install 'specadia[rag]'"
      ) from error
    try:
      return "\n\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)
    except Exception as error:
      raise KnowledgeBaseError(f"Could not extract PDF text from {path}: {error}") from error
  raise KnowledgeBaseError(f"Unsupported file type: {path}")


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
  """Split text into bounded, overlapping chunks on natural boundaries when possible."""
  if chunk_size < 100:
    raise KnowledgeBaseError("Chunk size must be at least 100 characters.")
  if chunk_overlap < 0 or chunk_overlap >= chunk_size:
    raise KnowledgeBaseError("Chunk overlap must be non-negative and smaller than chunk size.")
  normalized = re.sub(r"\r\n?", "\n", text).strip()
  if not normalized:
    return []
  chunks: list[str] = []
  start = 0
  while start < len(normalized):
    end = min(start + chunk_size, len(normalized))
    if end < len(normalized):
      boundary = max(
          normalized.rfind("\n\n", start + chunk_size // 2, end),
          normalized.rfind("\n", start + chunk_size // 2, end),
          normalized.rfind(" ", start + chunk_size // 2, end),
      )
      if boundary > start:
        end = boundary
    value = normalized[start:end].strip()
    if value:
      chunks.append(value)
    if end >= len(normalized):
      break
    start = max(start + 1, end - chunk_overlap)
  return chunks


def _hash_embedding(text: str, dimension: int = HASH_DIMENSION) -> list[float]:
  vector = [0.0] * dimension
  for token in _TOKEN_RE.findall(text.casefold()):
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    bucket = int.from_bytes(digest[:4], "big") % dimension
    sign = 1.0 if digest[4] & 1 else -1.0
    vector[bucket] += sign
  norm = math.sqrt(sum(value * value for value in vector))
  return [value / norm for value in vector] if norm else vector


def _source_fingerprint(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for block in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(block)
  return digest.hexdigest()


def _file_sha256(path: Path) -> str:
  return _source_fingerprint(path)


def _document_chunks(
    path: Path,
    source_key: str,
    *,
    chunk_size: int,
    chunk_overlap: int,
    max_file_bytes: int,
) -> list[dict[str, Any]]:
  text = read_document(path, max_file_bytes=max_file_bytes)
  fingerprint = _source_fingerprint(path)
  return [
      {
          "chunk": value,
          "source_type": "file",
          "source": source_key,
          "source_id": fingerprint,
          "chunk_index": index,
      }
      for index, value in enumerate(
          chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
      )
  ]


def _require_rag_dependencies():
  try:
    import faiss
    import numpy as np
  except ImportError as error:
    raise KnowledgeBaseError(
        "Knowledge-base indexing requires the RAG extra: pip install 'specadia[rag]'"
    ) from error
  return faiss, np


def _write_collection(
    destination: Path,
    collection: str,
    chunks: list[dict[str, Any]],
    source_manifest: dict[str, dict[str, Any]],
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> None:
  faiss, np = _require_rag_dependencies()
  if not chunks:
    raise KnowledgeBaseError("No readable text was found in the supplied sources.")
  matrix = np.asarray([_hash_embedding(item["chunk"]) for item in chunks], dtype=np.float32)
  index = faiss.IndexFlatIP(HASH_DIMENSION)
  index.add(matrix)
  destination.mkdir(parents=True, exist_ok=True)
  index_path = destination / "index.faiss"
  chunks_path = destination / "chunks.json"
  faiss.write_index(index, str(index_path))
  chunks_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
  manifest = {
      "schema_version": 1,
      "collection": collection,
      "created_at": datetime.now(timezone.utc).isoformat(),
      "embedding": {
          "provider": "local",
          "model": "specadia-hashing-v1",
          "dimension": HASH_DIMENSION,
      },
      "chunking": {"size": chunk_size, "overlap": chunk_overlap},
      "documents": len(source_manifest),
      "chunks": len(chunks),
      "sources": source_manifest,
      "artifacts": {
          "index.faiss": {
              "sha256": _file_sha256(index_path),
              "bytes": index_path.stat().st_size,
          },
          "chunks.json": {
              "sha256": _file_sha256(chunks_path),
              "bytes": chunks_path.stat().st_size,
          },
      },
  }
  (destination / "manifest.json").write_text(
      json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
  )


def build_file_collection(
    sources: Iterable[Path],
    *,
    collection: str = DEFAULT_COLLECTION,
    index_dir: Path = DEFAULT_INDEX_DIR,
    rebuild: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> BuildResult:
  """Add document sources to a collection, replacing changed sources by fingerprint."""
  files = discover_files(sources)
  if not files:
    raise KnowledgeBaseError("No supported documents were found.")
  source_keys = [f"file:{path.name}" for path in files]
  if len(set(source_keys)) != len(source_keys):
    raise KnowledgeBaseError(
        "Source filenames must be unique within a collection so private directory paths "
        "do not need to be stored."
    )
  destination = collection_dir(collection, index_dir)
  existing_chunks: list[dict[str, Any]] = []
  existing_sources: dict[str, dict[str, Any]] = {}
  if not rebuild and (destination / "manifest.json").exists():
    existing_chunks = json.loads((destination / "chunks.json").read_text(encoding="utf-8"))
    existing_sources = json.loads((destination / "manifest.json").read_text(encoding="utf-8")).get(
        "sources", {}
    )

  # Drop manifests created by older versions that stored absolute paths. They will be
  # replaced by privacy-safe identifiers during this build.
  existing_chunks = [
      item
      for item in existing_chunks
      if str(item.get("source", "")).startswith(("file:", "sqlite:"))
  ]
  existing_sources = {
      key: value
      for key, value in existing_sources.items()
      if key.startswith(("file:", "sqlite:"))
  }
  input_paths = set(source_keys)
  kept_chunks = [item for item in existing_chunks if item.get("source") not in input_paths]
  source_manifest = {
      key: value for key, value in existing_sources.items() if key not in input_paths
  }
  added = unchanged = 0
  for path, source_key in zip(files, source_keys):
    fingerprint = _source_fingerprint(path)
    if existing_sources.get(source_key, {}).get("sha256") == fingerprint:
      kept_chunks.extend(item for item in existing_chunks if item.get("source") == source_key)
      source_manifest[source_key] = existing_sources[source_key]
      unchanged += 1
      continue
    new_chunks = _document_chunks(
        path,
        source_key,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        max_file_bytes=max_file_bytes,
    )
    kept_chunks.extend(new_chunks)
    source_manifest[source_key] = {
        "type": "file",
        "sha256": fingerprint,
        "bytes": path.stat().st_size,
        "chunks": len(new_chunks),
    }
    added += 1
  _write_collection(
      destination,
      collection,
      kept_chunks,
      source_manifest,
      chunk_size=chunk_size,
      chunk_overlap=chunk_overlap,
  )
  return BuildResult(
      collection, len(source_manifest), len(kept_chunks), added, unchanged, destination
  )


def validate_read_only_sql(query: str) -> str:
  """Validate a single read-only SELECT/CTE query."""
  cleaned = query.strip()
  if (
      not _READ_ONLY_SQL_RE.match(cleaned)
      or _FORBIDDEN_SQL_RE.search(cleaned)
      or ";" in cleaned.rstrip(";")
      or "--" in cleaned
      or "/*" in cleaned
  ):
    raise KnowledgeBaseError("Database query must be one read-only SELECT or WITH statement.")
  return cleaned.rstrip(";").strip()


def _sqlite_uri(path: Path) -> str:
  return f"file:{path.expanduser().resolve().as_posix()}?mode=ro"


def ingest_sqlite(
    database: Path,
    *,
    query: str | None = None,
    table: str | None = None,
    collection: str = DEFAULT_COLLECTION,
    index_dir: Path = DEFAULT_INDEX_DIR,
    rebuild: bool = False,
    max_rows: int = DEFAULT_MAX_ROWS,
    max_cell_chars: int = DEFAULT_MAX_CELL_CHARS,
    sql_timeout_seconds: float = DEFAULT_SQL_TIMEOUT_SECONDS,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> BuildResult:
  """Index bounded rows from a SQLite database opened in read-only mode."""
  database = Path(database).expanduser().resolve()
  if not database.is_file():
    raise KnowledgeBaseError(f"SQLite database does not exist: {database}")
  if max_rows < 1 or max_rows > DEFAULT_MAX_ROWS:
    raise KnowledgeBaseError(f"max_rows must be between 1 and {DEFAULT_MAX_ROWS:,}.")
  if sql_timeout_seconds <= 0 or sql_timeout_seconds > DEFAULT_SQL_TIMEOUT_SECONDS:
    raise KnowledgeBaseError(
        f"sql_timeout_seconds must be greater than 0 and no more than "
        f"{DEFAULT_SQL_TIMEOUT_SECONDS:g}."
    )
  if bool(query) == bool(table):
    raise KnowledgeBaseError("Provide exactly one of query or table.")
  if table:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
      raise KnowledgeBaseError(
          "SQLite table names may contain only letters, numbers, and underscores."
      )
    query = f'SELECT * FROM "{table}"'
  safe_query = validate_read_only_sql(query or "")
  connection = sqlite3.connect(_sqlite_uri(database), uri=True)
  deadline = time.monotonic() + sql_timeout_seconds
  connection.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1_000)
  try:
    connection.execute("PRAGMA query_only = ON")
    cursor = connection.execute(safe_query)
    columns = [column[0] for column in cursor.description or []]
    rows = cursor.fetchmany(max_rows + 1)
  except sqlite3.OperationalError as error:
    if "interrupted" in str(error).lower():
      raise KnowledgeBaseError(
          f"SQLite query exceeded the {sql_timeout_seconds:g}-second execution budget."
      ) from error
    raise KnowledgeBaseError(f"SQLite read failed: {error}") from error
  except sqlite3.Error as error:
    raise KnowledgeBaseError(f"SQLite read failed: {error}") from error
  finally:
    connection.close()
  if len(rows) > max_rows:
    raise KnowledgeBaseError(
        f"Query returned more than the configured {max_rows:,}-row limit. Narrow the query."
    )
  row_texts = [
      json.dumps(
          {
              column: str(value)[:max_cell_chars] if value is not None else None
              for column, value in zip(columns, row)
          },
          ensure_ascii=False,
          sort_keys=True,
      )
      for row in rows
  ]
  source_key = f"sqlite:{database.name}:{hashlib.sha256(safe_query.encode()).hexdigest()[:12]}"
  source_id = hashlib.sha256("\n".join(row_texts).encode("utf-8")).hexdigest()
  new_chunks = [
      {
          "chunk": chunk,
          "source_type": "sqlite",
          "source": source_key,
          "source_id": source_id,
          "chunk_index": index,
      }
      for index, chunk in enumerate(
          chunk_text("\n".join(row_texts), chunk_size=chunk_size, chunk_overlap=chunk_overlap)
      )
  ]
  destination = collection_dir(collection, index_dir)
  existing_chunks: list[dict[str, Any]] = []
  existing_sources: dict[str, dict[str, Any]] = {}
  if not rebuild and (destination / "manifest.json").exists():
    existing_chunks = json.loads((destination / "chunks.json").read_text(encoding="utf-8"))
    existing_sources = json.loads((destination / "manifest.json").read_text(encoding="utf-8")).get(
        "sources", {}
    )
  chunks = [item for item in existing_chunks if item.get("source") != source_key] + new_chunks
  sources = {key: value for key, value in existing_sources.items() if key != source_key}
  sources[source_key] = {
      "type": "sqlite",
      "database": database.name,
      "query_sha256": hashlib.sha256(safe_query.encode()).hexdigest(),
      "rows": len(rows),
      "chunks": len(new_chunks),
  }
  unchanged = int(existing_sources.get(source_key, {}).get("sha256") == source_id)
  sources[source_key]["sha256"] = source_id
  _write_collection(
      destination,
      collection,
      chunks,
      sources,
      chunk_size=chunk_size,
      chunk_overlap=chunk_overlap,
  )
  return BuildResult(
      collection, len(sources), len(chunks), 0 if unchanged else 1, unchanged, destination
  )


def collection_status(
    collection: str = DEFAULT_COLLECTION, index_dir: Path = DEFAULT_INDEX_DIR
) -> dict[str, Any]:
  path = collection_dir(collection, index_dir)
  manifest_path = path / "manifest.json"
  if not manifest_path.exists():
    raise KnowledgeBaseError(f"Collection '{collection}' does not exist below {Path(index_dir)}.")
  return json.loads(manifest_path.read_text(encoding="utf-8"))


def list_collections(index_dir: Path = DEFAULT_INDEX_DIR) -> list[dict[str, Any]]:
  root = Path(index_dir).expanduser().resolve()
  if not root.exists():
    return []
  result = []
  for manifest in sorted(root.glob("*/manifest.json")):
    try:
      data = json.loads(manifest.read_text(encoding="utf-8"))
      result.append({
          "collection": data["collection"],
          "documents": data.get("documents", 0),
          "chunks": data.get("chunks", 0),
          "created_at": data.get("created_at"),
      })
    except (KeyError, json.JSONDecodeError):
      continue
  return result


def make_collection_retriever(
    collection: str = DEFAULT_COLLECTION,
    index_dir: Path = DEFAULT_INDEX_DIR,
    *,
    top_k: int = 5,
) -> Callable[[str], list[str]]:
  """Create a lazy persistent retriever for a named user collection."""
  destination = collection_dir(collection, index_dir)
  index = chunks = None

  def retrieve(query: str) -> list[str]:
    nonlocal index, chunks
    faiss, np = _require_rag_dependencies()
    if index is None:
      try:
        manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
        index_path = destination / "index.faiss"
        chunks_path = destination / "chunks.json"
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict):
          raise KnowledgeBaseError(
              f"RAG collection '{collection}' predates integrity metadata. Rebuild it."
          )
        for path in (index_path, chunks_path):
          expected = artifacts.get(path.name, {})
          if (
              not isinstance(expected, dict)
              or expected.get("sha256") != _file_sha256(path)
              or expected.get("bytes") != path.stat().st_size
          ):
            raise KnowledgeBaseError(
                f"RAG collection '{collection}' failed integrity validation. Rebuild it."
            )
        chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
        if not isinstance(chunks, list) or any(
            not isinstance(item, dict) or not isinstance(item.get("chunk"), str) for item in chunks
        ):
          raise KnowledgeBaseError(
              f"RAG collection '{collection}' contains invalid chunk data. Rebuild it."
          )
        index = faiss.read_index(str(index_path))
        if (
            index.d != HASH_DIMENSION
            or index.ntotal != len(chunks)
            or manifest.get("chunks") != len(chunks)
        ):
          raise KnowledgeBaseError(
              f"RAG collection '{collection}' has inconsistent index metadata. Rebuild it."
          )
      except KnowledgeBaseError:
        raise
      except (OSError, RuntimeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise KnowledgeBaseError(
            f"RAG collection '{collection}' is missing or invalid. "
            f"Build it with: specadia rag build <source> --collection {collection}"
        ) from error
    vector = np.asarray([_hash_embedding(query)], dtype=np.float32)
    _, indices = index.search(vector, min(top_k, index.ntotal))
    return [chunks[position]["chunk"] for position in indices[0] if position >= 0]

  return retrieve
