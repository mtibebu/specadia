"""Provider and environment preflight checks."""

import importlib.util
import json
import os
import socket
import sys
import tempfile
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.table import Table
from specadia import __version__
from utils import DEFAULT_MODEL_NAME
from agents.local_providers import local_provider_for, provider_host_port


@dataclass(frozen=True)
class CheckResult:
  name: str
  ok: bool
  required: bool
  message: str


@dataclass(frozen=True)
class DoctorReport:
  checks: list[CheckResult]

  @property
  def ok(self) -> bool:
    return all(check.ok or not check.required for check in self.checks)

  def to_dict(self) -> dict[str, object]:
    return {"ok": self.ok, "checks": [asdict(check) for check in self.checks]}


def run_checks(
    model: str,
    output_dir: Path,
    *,
    rag: bool = False,
    check_network: bool = True,
    environ: dict[str, str] | None = None,
) -> DoctorReport:
  """Run deterministic checks, with optional provider reachability."""
  env = environ if environ is not None else dict(os.environ)
  checks = [
      CheckResult(
          "python",
          sys.version_info >= (3, 12),
          True,
          f"Python {sys.version_info.major}.{sys.version_info.minor}; requires >=3.12",
      ),
      _provider_check(model, env),
      _output_check(output_dir),
  ]
  if model.lower().startswith("ollama"):
    checks.append(_ollama_check(env, check_network))
  elif provider := local_provider_for(model):
    checks.append(_local_provider_check(provider, env, check_network))
  if rag:
    checks.extend(
        [
            _module_check("faiss", "faiss-cpu", required=True),
            _module_check("pypdf", "pypdf", required=True),
            CheckResult(
                "rag-google-key",
                bool(env.get("GOOGLE_API_KEY")),
                True,
                "GOOGLE_API_KEY is set"
                if env.get("GOOGLE_API_KEY")
                else "GOOGLE_API_KEY is required for current RAG embeddings",
            ),
        ]
    )
  return DoctorReport(checks)


def _provider_check(model: str, env: dict[str, str]) -> CheckResult:
  normalized = model.lower()
  if normalized.startswith("ollama"):
    return CheckResult("provider-credentials", True, True, "Ollama uses local authentication")
  if provider := local_provider_for(model):
    if not provider.base_url(env):
      return CheckResult(
          "provider-credentials",
          False,
          True,
          f"{provider.base_url_env} is required for model {model}",
      )
    return CheckResult(
        "provider-credentials",
        True,
        True,
        f"{provider.name} uses a local OpenAI-compatible endpoint",
    )
  provider_keys = {
      "openai": "OPENAI_API_KEY",
      "anthropic": "ANTHROPIC_API_KEY",
      "gemini": "GOOGLE_API_KEY",
      "google": "GOOGLE_API_KEY",
  }
  for provider, key in provider_keys.items():
    if provider in normalized:
      present = bool(env.get(key))
      return CheckResult(
          "provider-credentials",
          present,
          True,
          f"{key} is set" if present else f"{key} is required for model {model}",
      )
  return CheckResult(
      "provider-credentials",
      False,
      True,
      f"Cannot infer credentials for model {model}; use a provider-qualified model name",
  )


def _output_check(output_dir: Path) -> CheckResult:
  target = output_dir.expanduser()
  probe_parent = target if target.exists() else target.parent
  try:
    probe_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=probe_parent, prefix=".specadia-doctor-"):
      pass
  except OSError as error:
    return CheckResult("output-directory", False, True, f"Not writable: {error}")
  return CheckResult("output-directory", True, True, f"Writable: {probe_parent.resolve()}")


def _ollama_check(env: dict[str, str], check_network: bool) -> CheckResult:
  url = env.get("OLLAMA_BASE_URL", "http://localhost:11434")
  if not check_network:
    return CheckResult("ollama", True, True, f"Reachability skipped for {url}")
  parsed = urlparse(url)
  host = parsed.hostname or "localhost"
  port = parsed.port or 11434
  try:
    with socket.create_connection((host, port), timeout=1):
      pass
  except OSError as error:
    return CheckResult("ollama", False, True, f"Cannot reach {host}:{port}: {error}")
  return CheckResult("ollama", True, True, f"Reachable at {host}:{port}")


def _local_provider_check(provider, env: dict[str, str], check_network: bool) -> CheckResult:
  endpoint = provider_host_port(provider, env)
  if endpoint is None:
    return CheckResult(
        provider.name,
        False,
        True,
        f"{provider.base_url_env} is required",
    )
  host, port, url = endpoint
  if not check_network:
    return CheckResult(provider.name, True, True, f"Reachability skipped for {url}")
  try:
    with socket.create_connection((host, port), timeout=1):
      pass
  except OSError as error:
    return CheckResult(
        provider.name,
        False,
        True,
        f"Cannot reach {host}:{port}: {error}",
    )
  return CheckResult(provider.name, True, True, f"Reachable at {host}:{port}")


def _module_check(module: str, package: str, *, required: bool) -> CheckResult:
  found = importlib.util.find_spec(module) is not None
  return CheckResult(
      f"module-{module}",
      found,
      required,
      f"{package} is installed" if found else f"Install the optional package {package}",
  )


app = typer.Typer(help="Validate Specadia provider and runtime prerequisites.")


@app.command()
def doctor(
    model: str = typer.Option(DEFAULT_MODEL_NAME, "--model", "-m"),
    output_dir: Path = typer.Option(Path(".specadia"), "--output-dir", "-o"),
    rag: bool = typer.Option(False, "--rag"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
    no_network: bool = typer.Option(False, "--no-network"),
    version: bool = typer.Option(
        False, "--version", is_eager=True, help="Show the Specadia version and exit."
    ),
):
  """Check the environment before starting an agent run."""
  if version:
    typer.echo(f"specadia {__version__}")
    return
  report = run_checks(model, output_dir, rag=rag, check_network=not no_network)
  if json_output:
    typer.echo(json.dumps(report.to_dict(), indent=2))
  else:
    table = Table(title="Specadia Doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Details")
    for check in report.checks:
      table.add_row(check.name, "PASS" if check.ok else "FAIL", check.message)
    Console().print(table)
  if not report.ok:
    raise typer.Exit(1)


if __name__ == "__main__":
  app()
