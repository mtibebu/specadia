"""Assert version surfaces and console entrypoints stay consistent."""

import tomllib
from pathlib import Path

from typer.testing import CliRunner

import specadia
from specadia.contracts.cli import app as contract_app


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_VERSION = "0.2.2"


def test_package_version_is_expected():
  assert specadia.__version__ == EXPECTED_VERSION


def test_pyproject_version_matches():
  with (ROOT / "pyproject.toml").open("rb") as fh:
    project = tomllib.load(fh)["project"]
  assert project["version"] == EXPECTED_VERSION


def test_uv_lock_version_matches():
  with (ROOT / "uv.lock").open("rb") as fh:
    lock = tomllib.load(fh)
  entry = next(pkg for pkg in lock["package"] if pkg["name"] == "specadia")
  assert entry["version"] == EXPECTED_VERSION


def test_console_entrypoints_declared():
  with (ROOT / "pyproject.toml").open("rb") as fh:
    scripts = tomllib.load(fh)["project"]["scripts"]
  assert scripts == {
      "specadia": "specadia.cli:app",
      "specadia-contract": "specadia.contracts.cli:app",
      "specadia-doctor": "specadia.diagnostics.doctor:app",
  }


def test_canonical_generate_and_retained_contract_surfaces_resolve():
  runner = CliRunner()
  result = runner.invoke(contract_app, ["--help"])
  assert result.exit_code == 0, result.output
  assert "generate" in result.output
  assert "from-intent" in result.output
  assert "runs" in result.output
