import sqlite3

from typer.testing import CliRunner

from main import app

runner = CliRunner()


def test_rag_document_cli_lifecycle(tmp_path):
  source = tmp_path / "manual.txt"
  source.write_text("A lunar freight invoice requires a crater-zone identifier.")
  index_dir = tmp_path / "rag"

  built = runner.invoke(
      app,
      ["rag", "build", str(source), "--collection", "logistics", "--index-dir", str(index_dir)],
  )
  listed = runner.invoke(app, ["rag", "list", "--index-dir", str(index_dir), "--json"])
  queried = runner.invoke(
      app,
      [
          "rag",
          "query",
          "lunar invoice",
          "--collection",
          "logistics",
          "--index-dir",
          str(index_dir),
      ],
  )

  assert built.exit_code == 0, built.output
  assert '"collection": "logistics"' in listed.output
  assert "crater-zone identifier" in queried.output


def test_rag_database_cli(tmp_path):
  database = tmp_path / "kb.sqlite"
  connection = sqlite3.connect(database)
  connection.execute("CREATE TABLE glossary (term TEXT, meaning TEXT)")
  connection.execute("INSERT INTO glossary VALUES ('quasar', 'priority incident class')")
  connection.commit()
  connection.close()

  result = runner.invoke(
      app,
      [
          "rag",
          "database",
          str(database),
          "--table",
          "glossary",
          "--index-dir",
          str(tmp_path / "rag"),
      ],
  )

  assert result.exit_code == 0, result.output
  assert "Collection 'default' ready" in result.output


def test_run_help_exposes_collection_selection():
  result = runner.invoke(app, ["run", "--help"])

  assert result.exit_code == 0
  assert "--rag-collection" in result.output
  assert "--rag-index-dir" in result.output
