"""CLI for user-owned Specadia RAG collections."""

import json
from pathlib import Path
import shutil

import typer
from rich import print

from .knowledge_base import (
    DEFAULT_COLLECTION,
    DEFAULT_INDEX_DIR,
    KnowledgeBaseError,
    build_file_collection,
    collection_dir,
    collection_status,
    ingest_sqlite,
    list_collections,
    make_collection_retriever,
)

app = typer.Typer(help="Build and inspect persistent domain knowledge-base collections.")


def _fail(error: Exception) -> None:
  print(f"[red]Error: {error}[/red]")
  raise typer.Exit(1)


@app.command("build")
def build(
    sources: list[Path] = typer.Argument(..., help="Document files or directories to ingest."),
    collection: str = typer.Option(DEFAULT_COLLECTION, "--collection", "-c"),
    index_dir: Path = typer.Option(DEFAULT_INDEX_DIR, "--index-dir"),
    rebuild: bool = typer.Option(False, "--rebuild", help="Discard the existing collection."),
    chunk_size: int = typer.Option(1000, "--chunk-size", min=100),
    chunk_overlap: int = typer.Option(150, "--chunk-overlap", min=0),
):
  """Add Markdown, text, PDF, or JSON documents to a collection."""
  try:
    result = build_file_collection(
        sources,
        collection=collection,
        index_dir=index_dir,
        rebuild=rebuild,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
  except (KnowledgeBaseError, OSError) as error:
    _fail(error)
  print(
      f"[green]Collection '{result.collection}' ready:[/green] {result.documents} source(s), "
      f"{result.chunks} chunk(s) at {result.collection_dir}"
  )


@app.command("database")
def database(
    sqlite_path: Path = typer.Argument(..., help="Path to a local SQLite database."),
    table: str | None = typer.Option(None, "--table", help="Read every row from this table."),
    query: str | None = typer.Option(None, "--query", help="One bounded SELECT or WITH query."),
    collection: str = typer.Option(DEFAULT_COLLECTION, "--collection", "-c"),
    index_dir: Path = typer.Option(DEFAULT_INDEX_DIR, "--index-dir"),
    rebuild: bool = typer.Option(False, "--rebuild"),
    max_rows: int = typer.Option(10_000, "--max-rows", min=1, max=10_000),
):
  """Add bounded rows from a SQLite database opened read-only."""
  try:
    result = ingest_sqlite(
        sqlite_path,
        table=table,
        query=query,
        collection=collection,
        index_dir=index_dir,
        rebuild=rebuild,
        max_rows=max_rows,
    )
  except (KnowledgeBaseError, OSError) as error:
    _fail(error)
  print(
      f"[green]Collection '{result.collection}' ready:[/green] {result.documents} source(s), "
      f"{result.chunks} chunk(s) at {result.collection_dir}"
  )


@app.command("list")
def list_command(
    index_dir: Path = typer.Option(DEFAULT_INDEX_DIR, "--index-dir"),
    json_output: bool = typer.Option(False, "--json"),
):
  """List local knowledge-base collections."""
  collections = list_collections(index_dir)
  if json_output:
    typer.echo(json.dumps(collections, indent=2))
  elif not collections:
    print("No RAG collections found.")
  else:
    for item in collections:
      print(f"{item['collection']}\t{item['documents']} source(s)\t{item['chunks']} chunk(s)")


@app.command("status")
def status(
    collection: str = typer.Argument(DEFAULT_COLLECTION),
    index_dir: Path = typer.Option(DEFAULT_INDEX_DIR, "--index-dir"),
):
  """Print a collection manifest (credentials and SQL text are never stored)."""
  try:
    typer.echo(json.dumps(collection_status(collection, index_dir), indent=2))
  except (KnowledgeBaseError, OSError) as error:
    _fail(error)


@app.command("query")
def query(
    text: str = typer.Argument(...),
    collection: str = typer.Option(DEFAULT_COLLECTION, "--collection", "-c"),
    index_dir: Path = typer.Option(DEFAULT_INDEX_DIR, "--index-dir"),
    top_k: int = typer.Option(5, "--top-k", min=1, max=20),
):
  """Inspect deterministic retrieval results without running an agent."""
  try:
    results = make_collection_retriever(collection, index_dir, top_k=top_k)(text)
  except (KnowledgeBaseError, OSError) as error:
    _fail(error)
  for index, value in enumerate(results, 1):
    print(f"[cyan]{index}.[/cyan] {value}")


@app.command("clear")
def clear(
    collection: str = typer.Argument(...),
    index_dir: Path = typer.Option(DEFAULT_INDEX_DIR, "--index-dir"),
    yes: bool = typer.Option(False, "--yes", help="Confirm permanent collection deletion."),
):
  """Delete one exact collection."""
  try:
    path = collection_dir(collection, index_dir)
  except KnowledgeBaseError as error:
    _fail(error)
  if not path.exists():
    _fail(KnowledgeBaseError(f"Collection '{collection}' does not exist."))
  if not yes and not typer.confirm(f"Delete RAG collection '{collection}' at {path}?"):
    raise typer.Abort()
  shutil.rmtree(path)
  print(f"[green]Deleted collection '{collection}'.[/green]")
