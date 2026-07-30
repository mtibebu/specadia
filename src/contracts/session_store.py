"""Durable, atomic checkpoints for HITL contract runs."""

import json
import os
import tempfile
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from pathlib import Path


def _now() -> str:
  return datetime.now(timezone.utc).isoformat()


@dataclass
class RunCheckpoint:
  run_id: str
  intent: str
  harnesses: list[str]
  output_dir: str
  project_name: str | None = None
  config: dict[str, object] = field(default_factory=dict)
  status: str = "created"
  stage: str = "created"
  collector_drafts: list[dict[str, object]] = field(default_factory=list)
  feedback: list[str] = field(default_factory=list)
  approved_draft: dict[str, object] | None = None
  srs: str | None = None
  design: str | None = None
  written_paths: list[str] = field(default_factory=list)
  error: str | None = None
  created_at: str = field(default_factory=_now)
  updated_at: str = field(default_factory=_now)

  def touch(self, *, stage: str | None = None, status: str | None = None) -> None:
    if stage:
      self.stage = stage
    if status:
      self.status = status
    self.updated_at = _now()


class SessionStore:
  """Store one JSON checkpoint per run."""

  def __init__(self, root: Path):
    self.root = root.expanduser()

  def path_for(self, run_id: str) -> Path:
    if not run_id or any(
        character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for character in run_id
    ):
      raise ValueError("run_id may contain only letters, numbers, '-' and '_'")
    return self.root / f"{run_id}.json"

  def save(self, checkpoint: RunCheckpoint) -> Path:
    self.root.mkdir(parents=True, exist_ok=True)
    checkpoint.updated_at = _now()
    destination = self.path_for(checkpoint.run_id)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{checkpoint.run_id}-", dir=self.root)
    try:
      with os.fdopen(handle, "w", encoding="utf-8") as stream:
        json.dump(asdict(checkpoint), stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
      os.replace(temporary_name, destination)
    except BaseException:
      try:
        os.unlink(temporary_name)
      except FileNotFoundError:
        pass
      raise
    return destination

  def load(self, run_id: str) -> RunCheckpoint:
    path = self.path_for(run_id)
    if not path.is_file():
      raise FileNotFoundError(f"No saved Specadia run: {run_id}")
    return RunCheckpoint(**json.loads(path.read_text(encoding="utf-8")))

  def list_runs(self) -> list[RunCheckpoint]:
    checkpoints: list[RunCheckpoint] = []
    seen: set[str] = set()
    paths: list[Path] = []
    if self.root.exists():
      paths.extend(sorted(self.root.glob("*.json")))
    for path in paths:
      try:
        checkpoint = RunCheckpoint(**json.loads(path.read_text(encoding="utf-8")))
        if checkpoint.run_id not in seen:
          checkpoints.append(checkpoint)
          seen.add(checkpoint.run_id)
      except (OSError, TypeError, json.JSONDecodeError):
        continue
    return checkpoints
