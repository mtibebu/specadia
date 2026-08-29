from pathlib import Path

from specadia._contracts.session_store import RunCheckpoint
from specadia._contracts.session_store import SessionStore


def test_atomic_round_trip(tmp_path: Path):
  store = SessionStore(tmp_path)
  checkpoint = RunCheckpoint(
      run_id="run-1",
      intent="Build it",
      harnesses=["codex"],
      output_dir="out",
      collector_drafts=[{"FRs": ["FR-1: Build"]}],
  )

  path = store.save(checkpoint)
  loaded = store.load("run-1")

  assert path.is_file()
  assert loaded.collector_drafts == checkpoint.collector_drafts
  assert list(tmp_path.glob(".run-1-*")) == []


def test_lists_valid_runs_and_skips_corrupt(tmp_path: Path):
  store = SessionStore(tmp_path)
  store.save(RunCheckpoint("good", "Intent", ["codex"], "out"))
  (tmp_path / "broken.json").write_text("{", encoding="utf-8")

  assert [run.run_id for run in store.list_runs()] == ["good"]
