import subprocess
import sys

from typer.testing import CliRunner

from specadia.cli import app
from specadia.contracts.cli import app as contract_app


def test_core_cli_imports_without_google_adk():
  probe = subprocess.run(
      [
          sys.executable,
          "-c",
          "import sys; import specadia.cli; assert 'google.adk' not in sys.modules",
      ],
      check=False,
      capture_output=True,
      text=True,
  )
  assert probe.returncode == 0, probe.stderr
  result = CliRunner().invoke(app, ["--help"])
  assert result.exit_code == 0, result.output
  assert "contract" in result.output
  assert "doctor" in result.output


def test_contract_cli_exposes_only_deterministic_generation():
  result = CliRunner().invoke(contract_app, ["--help"])
  assert result.exit_code == 0, result.output
  assert "generate" in result.output
  assert "from-intent" not in result.output
