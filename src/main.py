import asyncio
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich import print
from rich.console import Console
from specadia import __version__

from contracts.cli import generate_contract
from contracts.cli import generate_from_intent
from contracts.cli import list_runs
from diagnostics.doctor import doctor
from rag.cli import app as rag_app
from utils import DEFAULT_MODEL_NAME
from utils.constants import AgentRunMode
from utils.logger import get_run_id
from utils.logger import setup_logging

app = typer.Typer(help="Specadia CLI for automated software design")
app.command("contract")(generate_contract)
app.command("contract-from-intent")(generate_from_intent)
app.command("contract-runs")(list_runs)
app.command("doctor")(doctor)
app.add_typer(rag_app, name="rag")


def _version_callback(value: bool) -> None:
  if value:
    typer.echo(f"specadia {__version__}")
    raise typer.Exit()


@app.callback()
def main_cli(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True, help="Show version and exit."
    ),
):
  """Specadia CLI for automated software design."""


@app.command()
def run(
    run_id: str = typer.Option(
        lambda: get_run_id(),
        "--run-id",
        "-i",
        help="Unique run identifier",
    ),
    agent_type: Optional[str] = typer.Option(
        "single_agent",
        "--agent-type",
        "-t",
        help="Single or Multi-agent option.",
    ),
    query: Optional[str] = typer.Option(
        None,
        "--query",
        "-q",
        help="User's input query",
    ),
    llm_model_name: Optional[str] = typer.Option(
        DEFAULT_MODEL_NAME,
        "--llm-model-name",
        "-m",
        help="LLM model name",
    ),
    rag: Optional[bool] = typer.Option(
        False,
        "--rag",
        "-r",
        help="Indicates if the agents use RAG",
    ),
    rag_collection: str = typer.Option(
        "default",
        "--rag-collection",
        help="Named collection created with `specadia rag build`.",
    ),
    rag_index_dir: Path = typer.Option(
        Path(".specadia/rag"),
        "--rag-index-dir",
        help="Root directory containing user RAG collections.",
    ),
):
  """Run the Specadia automation with specified configuration."""
  try:
    from orchestrator.orchestrator import get_agent_response
  except ImportError as error:
    Console().print(
        "[red]Agent dependencies are not installed. "
        "Install Specadia with `pip install 'specadia\\[agents]'`.[/red]"
    )
    raise typer.Exit(1) from error

  setup_logging(run_id, "cli")
  logger.info(f"Starting run with ID: {run_id}")

  try:
    logger.info(
        f"Input params: agent-type - {agent_type}, query - {query}, model - {llm_model_name},"
        f" rag - {rag}"
    )

    response = asyncio.run(
        get_agent_response(
            query,
            llm_model_name,
            agent_type,
            run_mode=AgentRunMode.MAIN,
            rag=rag,
            rag_source=rag_collection,
            rag_index_dir=rag_index_dir,
        )
    )
    logger.info(f"Response: {response}")
    # Also print the actual agent output to stdout (in addition to logs),
    # so users see the design/SRS content directly.
    print(response)
  except Exception as e:
    logger.error(f"Error during execution: {str(e)}")
    print(f"[red]Error: {str(e)}[/red]")
    raise typer.Exit(1)


if __name__ == "__main__":
  app(prog_name="specadia")
