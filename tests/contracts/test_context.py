import json
from pathlib import Path

from contracts.context import inspect_repository


def test_context_is_bounded_and_excludes_secrets(tmp_path: Path):
  (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
  (tmp_path / "AGENTS.md").write_text("Use pytest.", encoding="utf-8")
  (tmp_path / ".env").write_text("SECRET=value", encoding="utf-8")
  (tmp_path / "src").mkdir()
  (tmp_path / "src" / "app.py").write_text("print('hello')", encoding="utf-8")

  context = inspect_repository(tmp_path)
  payload = json.loads(context.to_prompt().split("\n", 1)[1])

  assert context.languages == ["Python"]
  assert ".env" not in context.structure
  assert "SECRET=value" not in context.to_prompt()
  assert payload["conventions"]["AGENTS.md"] == "Use pytest."
