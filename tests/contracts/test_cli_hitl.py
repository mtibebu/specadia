from pathlib import Path

from typer.testing import CliRunner

from specadia._contracts.cli import app
from specadia._contracts.specadia_pipeline import SpecadiaPipeline
from specadia._contracts.workflow import GeneratedDocuments

runner = CliRunner()


async def _collect(self, intent, previous=None, feedback=None):
  version = "FR-2" if feedback else "FR-1"
  return {"FRs": [f"{version}: Approved behavior"], "NFRs": []}


async def _documents(self, intent, approved):
  requirement = approved["FRs"][0].split(":", 1)[0]
  return GeneratedDocuments(
      srs=f"# Product SRS\n\n## Functional Requirements\n\n- {requirement}: Approved behavior.",
      design=(
          f"# Product Design\n\n## Architecture\n\nThe service component implements {requirement}."
      ),
  )


def _patch_pipeline(monkeypatch):
  monkeypatch.setattr(SpecadiaPipeline, "collect", _collect)
  monkeypatch.setattr(SpecadiaPipeline, "generate_documents", _documents)


def test_cli_approve(monkeypatch, tmp_path: Path):
  _patch_pipeline(monkeypatch)
  result = runner.invoke(
      app,
      [
          "from-intent",
          "Build it",
          "-o",
          str(tmp_path / "out"),
          "--run-id",
          "approve",
          "--sessions-dir",
          str(tmp_path / "sessions"),
      ],
      input="approve\n",
  )
  assert result.exit_code == 0, result.output
  assert (tmp_path / "out" / "AGENTS.md").is_file()


def test_cli_refine_then_approve(monkeypatch, tmp_path: Path):
  _patch_pipeline(monkeypatch)
  result = runner.invoke(
      app,
      [
          "from-intent",
          "Build it",
          "-o",
          str(tmp_path / "out"),
          "--run-id",
          "refine",
          "--sessions-dir",
          str(tmp_path / "sessions"),
      ],
      input="refine\nAdd auditing\napprove\n",
  )
  assert result.exit_code == 0, result.output
  assert "1 refinement(s)" in result.output


def test_cli_cancel(monkeypatch, tmp_path: Path):
  _patch_pipeline(monkeypatch)
  result = runner.invoke(
      app,
      [
          "from-intent",
          "Build it",
          "-o",
          str(tmp_path / "out"),
          "--run-id",
          "cancel",
          "--sessions-dir",
          str(tmp_path / "sessions"),
      ],
      input="cancel\n",
  )
  assert result.exit_code == 2
  assert not (tmp_path / "out").exists()
