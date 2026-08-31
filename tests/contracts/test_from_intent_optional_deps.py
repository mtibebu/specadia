"""Regression guards for the dependency-light from-intent path."""

import importlib.util
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from specadia.contracts.cli import app


def _google_adk_available() -> bool:
  try:
    return importlib.util.find_spec("google.adk") is not None
  except (ImportError, ModuleNotFoundError):
    return False


@pytest.mark.skipif(
    _google_adk_available(),
    reason="missing-extra hint is only observable when google-adk is absent",
)
def test_from_intent_missing_extras_exits_cleanly_with_hint():
  result = CliRunner().invoke(app, ["from-intent", "Build a todo app"])
  assert result.exit_code != 0
  assert "specadia[full]" in result.output
  assert "Traceback" not in result.output


def test_runs_is_dependency_free(tmp_path):
  result = CliRunner().invoke(
      app,
      ["runs", "--sessions-dir", str(tmp_path)],
  )
  assert result.exit_code == 0, result.output
  assert "No saved runs." in result.output


def test_is_local_model_and_no_google_adk():
  from specadia.providers import is_local_model

  assert is_local_model("ollama/qwen3")
  assert is_local_model("lm_studio/model")
  assert not is_local_model("openai/gpt-4")

  probe = subprocess.run(
      [
          sys.executable,
          "-c",
          "import sys; import specadia.providers; assert 'google.adk' not in sys.modules",
      ],
      check=False,
      capture_output=True,
      text=True,
  )
  assert probe.returncode == 0, probe.stderr


def test_providers_imports_without_google():
  probe = subprocess.run(
      [
          sys.executable,
          "-c",
          (
              "import sys; import specadia.providers; "
              "assert 'google.adk' not in sys.modules; "
              "assert 'google' not in sys.modules; "
              "assert 'litellm' not in sys.modules"
          ),
      ],
      check=False,
      capture_output=True,
      text=True,
  )
  assert probe.returncode == 0, probe.stderr
