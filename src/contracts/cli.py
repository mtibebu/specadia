"""CLI implementation for converting READ-MAS artifacts into contracts."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich import print
from specadia import __version__
from specadia._constants import DEFAULT_MODEL_NAME

from .generator import ContractGenerator
from .context import inspect_repository
from .models import Harness
from .session_store import SessionStore
from .workflow import ApprovalAction
from .workflow import ApprovalDecision
from .workflow import ContractWorkflow
from .workflow import WorkflowCancelled
from .validation import QualityReport
from .writer import write_bundles

app = typer.Typer(help="Generate coding-agent contracts from READ-MAS requirements and designs.")

DEFAULT_SESSIONS_DIR = Path(".specadia/sessions")

__all__ = ["app", "generate_contract", "generate_from_intent", "list_runs"]


def _session_store(root: Path) -> SessionStore:
  return SessionStore(root)


def _version_callback(value: bool) -> None:
  if value:
    typer.echo(f"specadia {__version__}")
    raise typer.Exit()


@app.callback()
def contract_cli(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the Specadia version and exit.",
    ),
):
  """Generate coding-agent contracts from READ-MAS requirements and designs."""


@app.command("generate")
def generate_contract(
    spec: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Software requirements specification in Markdown.",
    ),
    design: Optional[Path] = typer.Option(
        None,
        "--design",
        "-d",
        exists=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Optional Specadia design document in Markdown.",
    ),
    harness: list[Harness] = typer.Option(
        [Harness.CODEX],
        "--harness",
        "-H",
        help="Target harness. Repeat for multiple outputs.",
    ),
    output_dir: Path = typer.Option(
        Path(".specadia/contracts"),
        "--output-dir",
        "-o",
        help="Directory for contracts and the traceability manifest.",
    ),
    project_name: Optional[str] = typer.Option(
        None,
        "--project-name",
        help="Override the project name inferred from the SRS title.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing generated contract files.",
    ),
):
  """Generate implementation contracts for coding harnesses."""
  generator = ContractGenerator()
  try:
    targets = list(dict.fromkeys(harness))
    bundles = [
        generator.generate(
            spec_path=spec,
            design_path=design,
            harness=target,
            output_dir=output_dir,
            project_name=project_name,
        )
        for target in targets
    ]
    written = write_bundles(bundles, force=force)
  except (ValueError, FileExistsError, OSError) as error:
    print(f"[red]Error: {error}[/red]")
    raise typer.Exit(1) from error

  for path in written:
    print(f"[green]Generated:[/green] {path}")


class ConsoleApprovalGate:
  """Interactive Collector approval for terminal users."""

  def review(self, draft: dict[str, object], attempt: int) -> ApprovalDecision:
    print(f"\n[bold]Collector draft {attempt}[/bold]")
    print_json = json.dumps(draft, indent=2, default=str)
    print(print_json)
    action = typer.prompt(
        "Choose [approve/refine/cancel]",
        default=ApprovalAction.APPROVE.value,
    ).lower()
    try:
      selected = ApprovalAction(action)
    except ValueError as error:
      raise ValueError("Choose must be approve, refine, or cancel") from error
    if selected == ApprovalAction.REFINE:
      feedback = typer.prompt("Refinement feedback")
      return ApprovalDecision(ApprovalAction.REFINE, feedback)
    return ApprovalDecision(selected)


class ConsoleQualityGate:
  """Offer another Collector refinement when generated documents fail checks."""

  def __call__(self, report: QualityReport) -> ApprovalDecision:
    print("\n[bold red]Generated document quality checks failed[/bold red]")
    for issue in report.issues:
      print(f"- {issue.document}/{issue.code}: {issue.message}")
    if not typer.confirm("Refine requirements and regenerate?", default=True):
      return ApprovalDecision(ApprovalAction.CANCEL)
    return ApprovalDecision(
        ApprovalAction.REFINE,
        typer.prompt("Refinement feedback"),
    )


def _progress(stage: str, status: str) -> None:
  print(f"[cyan]{stage}[/cyan]: {status}")


def _missing_agent_extras_hint() -> None:
  typer.secho(
      "Natural-language intent-to-contract requires the agent extras. "
      'Install with: pip install "specadia[full]"',
      fg=typer.colors.RED,
  )


@app.command("from-intent")
def generate_from_intent(
    intent: str = typer.Argument(..., help="Initial product or system intent."),
    harness: list[Harness] = typer.Option(
        [Harness.CODEX],
        "--harness",
        "-H",
        help="Target harness. Repeat for multiple outputs.",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help=(
            "Directory for generated sources, contracts, and manifest. Defaults to "
            ".specadia/contracts, or the checkpoint's recorded directory when resuming."
        ),
    ),
    llm_model_name: str = typer.Option(
        DEFAULT_MODEL_NAME,
        "--llm-model-name",
        "-m",
        help="Model used by the Specadia agents.",
    ),
    rag: bool = typer.Option(False, "--rag", help="Enable requirement retrieval."),
    rag_collection: str = typer.Option(
        "default",
        "--rag-collection",
        help="Named collection created with `specadia rag build`.",
    ),
    rag_index_dir: Path = typer.Option(
        Path(".specadia/rag"), "--rag-index-dir", help="Root directory for user collections."
    ),
    project_name: Optional[str] = typer.Option(None, "--project-name"),
    max_refinements: int = typer.Option(
        5,
        "--max-refinements",
        min=0,
        help="Maximum human-requested Collector revisions.",
    ),
    force: bool = typer.Option(False, "--force"),
    repo: Optional[Path] = typer.Option(
        None,
        "--repo",
        exists=True,
        file_okay=False,
        resolve_path=True,
        help="Existing repository whose structure and conventions constrain the design.",
    ),
    run_id: Optional[str] = typer.Option(None, "--run-id", help="Stable checkpoint identifier."),
    resume: bool = typer.Option(False, "--resume", help="Resume a saved HITL run."),
    sessions_dir: Path = typer.Option(
        DEFAULT_SESSIONS_DIR,
        "--sessions-dir",
        help="Directory containing durable run checkpoints.",
    ),
    stage_timeout: float = typer.Option(
        300,
        "--stage-timeout",
        min=1,
        help="Timeout in seconds for each agent stage.",
    ),
    fallback_model: list[str] = typer.Option(
        [],
        "--fallback-model",
        help="Fallback agent model. Repeat to define an ordered fallback chain.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Confirm sending repository context to a hosted model.",
    ),
):
  """Generate SRS/design with HITL, then emit coding-agent contracts."""
  from .specadia_pipeline import SpecadiaPipeline
  from specadia.providers import is_local_model

  effective_intent = intent
  if repo:
    context = inspect_repository(repo)
    hosted = not is_local_model(llm_model_name)
    if (
        hosted
        and not yes
        and not typer.confirm(
            f"Send bounded metadata and convention files from {repo} to {llm_model_name}?"
        )
    ):
      raise typer.Exit(2)
    effective_intent = f"{intent}\n\n{context.to_prompt()}"

  try:
    pipeline = SpecadiaPipeline(
        llm_model_name=llm_model_name,
        rag=rag,
        rag_collection=rag_collection,
        rag_index_dir=rag_index_dir,
        stage_timeout=stage_timeout,
    )
    if resume and not run_id:
      print("[red]Error: --resume requires --run-id.[/red]")
      raise typer.Exit(1)
    store = _session_store(sessions_dir)
    if output_dir is None:
      output_dir = (
          Path(store.load(run_id).output_dir) if resume and run_id else Path(".specadia/contracts")
      )
    fallback_pipelines = [
        SpecadiaPipeline(
            model,
            rag=rag,
            rag_collection=rag_collection,
            rag_index_dir=rag_index_dir,
            stage_timeout=stage_timeout,
        )
        for model in fallback_model
    ]
    workflow = ContractWorkflow(
        collect_draft=pipeline.collect,
        generate_documents=pipeline.generate_documents,
        approval_gate=ConsoleApprovalGate(),
        session_store=store,
        progress=_progress,
        collector_fallbacks=[fallback.collect for fallback in fallback_pipelines],
        document_fallbacks=[fallback.generate_documents for fallback in fallback_pipelines],
        quality_gate=ConsoleQualityGate(),
    )
    try:
      result = asyncio.run(
          workflow.run(
              effective_intent,
              harness,
              output_dir,
              project_name=project_name,
              max_refinements=max_refinements,
              force=force,
              run_id=run_id,
              resume=resume,
              stage_timeout=stage_timeout,
              metadata={
                  "model": llm_model_name,
                  "fallback_models": fallback_model,
                  "rag": rag,
                  "rag_collection": rag_collection,
                  "repository_context": bool(repo),
                  "stage_timeout": stage_timeout,
              },
          )
      )
    except WorkflowCancelled as error:
      print(f"[yellow]{error}[/yellow]")
      raise typer.Exit(2) from error
    except (ValueError, FileExistsError, OSError) as error:
      print(f"[red]Error: {error}[/red]")
      raise typer.Exit(1) from error
  except ImportError:
    _missing_agent_extras_hint()
    raise typer.Exit(1)
  except RuntimeError as error:
    cause = error.__cause__ or error.__context__
    if isinstance(cause, ImportError):
      _missing_agent_extras_hint()
      raise typer.Exit(1)
    raise

  print(f"[green]Approved after {result.refinement_count} refinement(s).[/green]")
  for path in result.written_paths:
    print(f"[green]Generated:[/green] {path}")


@app.command("runs")
def list_runs(
    sessions_dir: Path = typer.Option(DEFAULT_SESSIONS_DIR, "--sessions-dir"),
):
  """List durable HITL runs available for resume."""
  runs = _session_store(sessions_dir).list_runs()
  if not runs:
    print("No saved runs.")
    return
  for run in runs:
    print(f"{run.run_id}\t{run.status}\t{run.stage}\t{run.updated_at}")


if __name__ == "__main__":
  app()
