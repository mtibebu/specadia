"""Assert version surfaces and console entrypoints stay consistent."""

import json
import tomllib
from pathlib import Path

from typer.testing import CliRunner

import specadia
from specadia.contracts.cli import app as contract_app


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_VERSION = "0.2.4"


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


# JSON manifests/packages that carry an explicit top-level ``version`` field.
_VERSION_JSON_FILES = [
    "package.json",
    "plugin.json",
    ".devin-plugin/plugin.json",
    ".grok-plugin/plugin.json",
    ".kimi-plugin/plugin.json",
    "plugins/claude-code/specadia/.claude-plugin/plugin.json",
    "plugins/cursor/specadia/.cursor-plugin/plugin.json",
    "plugins/specadia/.codex-plugin/plugin.json",
]


def test_all_package_and_plugin_manifests_are_0_2_4():
  for rel in _VERSION_JSON_FILES:
    path = ROOT / rel
    assert path.exists(), f"missing manifest: {rel}"
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == EXPECTED_VERSION, rel

  marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
  for plugin in marketplace["plugins"]:
    assert plugin["version"] == EXPECTED_VERSION


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
