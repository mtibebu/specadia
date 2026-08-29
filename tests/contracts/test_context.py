import json
from pathlib import Path

from specadia.contracts.context import inspect_repository


def test_context_is_bounded_and_excludes_secrets(tmp_path: Path):
  (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
  (tmp_path / "AGENTS.md").write_text("Use pytest.", encoding="utf-8")
  (tmp_path / ".env").write_text("SECRET=value", encoding="utf-8")
  (tmp_path / ".env.production").write_text("TOKEN=value", encoding="utf-8")
  (tmp_path / "credentials.json").write_text('{"password": "value"}', encoding="utf-8")
  (tmp_path / "src").mkdir()
  (tmp_path / "src" / "app.py").write_text("print('hello')", encoding="utf-8")

  context = inspect_repository(tmp_path)
  payload = json.loads(context.to_prompt().split("\n", 1)[1])

  assert context.languages == ["Python"]
  assert ".env" not in context.structure
  assert "SECRET=value" not in context.to_prompt()
  assert payload["root"] == "."
  assert payload["conventions"]["AGENTS.md"] == "[present; content omitted from repository context]"
  assert ".env.production" not in context.structure
  assert "credentials.json" not in context.structure
  assert str(tmp_path) not in context.to_prompt()
