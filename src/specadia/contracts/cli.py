"""Primary Specadia contract CLI."""

import typer

from specadia import __version__
from specadia._contracts.cli import generate_contract

app = typer.Typer(
    help="Convert requirements and designs into coding-agent contracts.",
    invoke_without_command=True,
)
app.command("generate")(generate_contract)


@app.callback()
def contract_cli(
    version: bool = typer.Option(False, "--version", is_eager=True, help="Show version and exit."),
) -> None:
  """Convert approved design artifacts into coding-agent contracts."""
  if version:
    typer.echo(f"specadia {__version__}")
    raise typer.Exit()

__all__ = ["app"]
