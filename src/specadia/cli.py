"""Primary core-only Specadia command-line interface."""

import typer

from specadia import __version__
from specadia._contracts.cli import generate_contract
from specadia.diagnostics.doctor import doctor

app = typer.Typer(help="Convert READ-MAS requirements and designs into coding-agent contracts.")
app.command("contract")(generate_contract)
app.command("doctor")(doctor)


def _version_callback(value: bool) -> None:
  if value:
    typer.echo(f"specadia {__version__}")
    raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True, help="Show version and exit."
    ),
):
  """Convert READ-MAS artifacts into implementation-ready contracts."""

__all__ = ["app"]
