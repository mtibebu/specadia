from typer.testing import CliRunner

import specadia
from specadia.cli import app as main_app
from specadia.contracts.cli import app as contract_app
from specadia.contracts.models import Harness
from specadia.diagnostics.doctor import app as doctor_app


def test_specadia_namespace_is_available():
  assert Harness.CODEX.value == "codex"


def test_primary_clis_report_package_version():
  for cli in (main_app, contract_app, doctor_app):
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == f"specadia {specadia.__version__}"


def test_primary_cli_positions_contract_handoff():
  result = CliRunner().invoke(main_app, ["--help"])

  assert result.exit_code == 0, result.output
  assert "READ-MAS" in result.output
  assert "contract" in result.output
  assert "run" not in result.output
