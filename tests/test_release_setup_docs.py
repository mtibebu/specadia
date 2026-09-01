"""Guard the source-checkout/release setup docs against a test-only regression.

Ensures the documented setup installs the complete set of extras (``full``,
``test``, and ``dev``) so that ``pytest``, ``build``, and ``twine`` are all
present before any build/release command is invoked. Read-only and hermetic:
parses docs and version surfaces only, with no network or provider access.
"""

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_VERSION = "0.2.7"


def _read(*parts):
  return (ROOT / Path(*parts)).read_text(encoding="utf-8")


def test_readme_source_checkout_installs_all_extras():
  readme = _read("README.md")
  assert "uv sync --all-extras" in readme
  assert 'python -m pip install -e ".[full,test,dev]"' in readme
  # Bare python3.13 must be explained as NOT including pytest/build/twine.
  assert "does **not** include" in readme


def test_readme_development_uses_managed_interpreter_and_build_twine():
  readme = _read("README.md")
  assert "uv run python -m pytest -q" in readme
  assert "uv run python -m build" in readme
  assert "uv run python -m twine check" in readme


def test_contributing_dev_setup_installs_all_extras():
  contrib = _read("CONTRIBUTING.md")
  assert "uv sync --all-extras" in contrib
  assert 'python -m pip install -e ".[full,test,dev]"' in contrib
  assert '".[test]"' not in contrib


def test_contributing_release_checks_use_managed_interpreter():
  contrib = _read("CONTRIBUTING.md")
  assert "uv run python -m build" in contrib
  assert "uv run python -m twine check" in contrib
  # build/twine presence is stated to require the extras first.
  assert "--all-extras" in contrib


def test_no_test_only_flow_before_build_twine():
  # The release/setup docs must never present a bare test-only install as the
  # environment used before build/twine because that omits the dev extras.
  for name in ("README.md", "CONTRIBUTING.md"):
    text = _read(name)
    assert '".[test]"' not in text, f"{name} regressed to a test-only install"
    assert "uv sync --extra test" not in text, f"{name} still uses --extra test"
    assert ".[full,test,dev]" in text, f"{name} missing complete extras install"
    assert "--all-extras" in text, f"{name} missing --all-extras"

  # CLAUDE.md still documents `. [test]` as a core-only testing convenience,
  # but its environment/buid/twine flow must use the complete extras.
  claude = _read("CLAUDE.md")
  assert "uv sync --extra test" not in claude, "CLAUDE.md still uses --extra test"
  assert "uv sync --all-extras" in claude
  assert ".[full,test,dev]" in claude
  assert "uv run python -m build" in claude


def test_version_surfaces_are_0_2_7():
  with (ROOT / "pyproject.toml").open("rb") as fh:
    assert tomllib.load(fh)["project"]["version"] == EXPECTED_VERSION

  import specadia

  assert specadia.__version__ == EXPECTED_VERSION

  with (ROOT / "uv.lock").open("rb") as fh:
    lock = tomllib.load(fh)

  entry = next(pkg for pkg in lock["package"] if pkg["name"] == "specadia")
  assert entry["version"] == EXPECTED_VERSION

  for manifest in ("package.json", "plugin.json"):
    assert json.loads(_read(manifest))["version"] == EXPECTED_VERSION
