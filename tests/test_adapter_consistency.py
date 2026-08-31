"""Assert shipped adapter instructions use one consistent decision flow and no stale phrasings."""

from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parent.parent
README_MAS_URL = "https://github.com/NU-Academics/read-mas"

ADAPTER_FILES = [
    "skills/specadia-plan/SKILL.md",
    "plugins/specadia/skills/specadia-plan/SKILL.md",
    "plugins/cline/specadia/skills/specadia-plan/SKILL.md",
    "plugins/cursor/specadia/skills/specadia-plan/SKILL.md",
    "plugins/grok/specadia/skills/specadia-plan/SKILL.md",
    "plugins/kimi/specadia/skills/specadia-plan/SKILL.md",
    "plugins/claude-code/specadia/commands/specadia-plan.md",
    "plugins/claude-code/specadia/commands/specadia-contract.md",
]

STALE_PHRASES = [
    "does not generate designs",
    "does not generate requirements",
    "does not generate a design",
    "cannot generate designs",
    "cannot generate requirements",
    "sent back to read-mas",
    "send back to read-mas",
    "back to read-mas",
]


def _adapter_texts():
  for rel in ADAPTER_FILES:
    path = ROOT / rel
    assert path.exists(), f"missing shipped adapter: {rel}"
    yield rel, path.read_text(encoding="utf-8")


def test_no_adapter_claims_specadia_cannot_generate():
  for rel, text in _adapter_texts():
    lower = text.lower()
    for phrase in STALE_PHRASES:
      assert phrase not in lower, f"{rel} contains stale phrase: {phrase!r}"


def test_intent_only_adapters_document_from_intent_path():
  for rel, text in _adapter_texts():
    if "intent" in text.lower():
      assert "from-intent" in text, f"{rel} references intent but not `from-intent`"


def test_readme_links_readmas_and_states_relationship():
  readme = (ROOT / "README.md").read_text(encoding="utf-8")
  assert README_MAS_URL in readme
  assert "predecessor" in readme.lower()
  assert "successor" in readme.lower()


def test_pyproject_readmas_url_and_version():
  with (ROOT / "pyproject.toml").open("rb") as fh:
    project = tomllib.load(fh)["project"]
  assert project["version"] == "0.2.3"
  urls = project.get("urls", {})
  assert README_MAS_URL in urls.values(), f"pyproject URLs missing READ-MAS link: {urls}"
