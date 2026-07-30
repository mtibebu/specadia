import builtins

from typer.testing import CliRunner

import specadia
from utils import DEFAULT_MODEL_NAME
from diagnostics.doctor import app as doctor_app
from main import app as main_app
from contracts.cli import DEFAULT_SESSIONS_DIR
from specadia.contracts.cli import app as specadia_contract_app
from specadia.contracts.models import Harness


def test_specadia_namespace_is_available():
  assert Harness.CODEX.value == "codex"


def test_contract_cli_uses_specadia_defaults():
  result = CliRunner().invoke(specadia_contract_app, ["from-intent", "--help"])

  assert result.exit_code == 0
  assert str(DEFAULT_SESSIONS_DIR) == ".specadia/sessions"
  assert ".specadia/contracts" in result.stdout
  assert ".specadia/sessions" in result.stdout


def test_primary_clis_report_package_version():
  for cli in (main_app, specadia_contract_app, doctor_app):
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == f"specadia {specadia.__version__}"


def test_default_model_is_qwen_across_primary_clis():
  assert DEFAULT_MODEL_NAME == "ollama_chat/qwen3.6:35b"
  for cli, command in (
      (main_app, ["run", "--help"]),
      (specadia_contract_app, ["from-intent", "--help"]),
      (doctor_app, ["--help"]),
  ):
    result = CliRunner().invoke(cli, command)
    assert result.exit_code == 0, result.output
    assert DEFAULT_MODEL_NAME in result.stdout


def test_missing_agent_dependency_message_keeps_extra_name(monkeypatch):
  original_import = builtins.__import__

  def block_orchestrator(name, *args, **kwargs):
    if name == "orchestrator.orchestrator":
      raise ImportError("simulated core-only install")
    return original_import(name, *args, **kwargs)

  monkeypatch.setattr(builtins, "__import__", block_orchestrator)
  result = CliRunner().invoke(main_app, ["run", "--query", "Build it"])

  assert result.exit_code == 1
  assert "specadia[agents]" in result.stdout
