import os
import threading
from pathlib import Path
from typing import Optional
import time

from loguru import logger


# Thread-local storage for logging state
_logging_state = threading.local()


def setup_logging(run_id: str, logger_path: str):
  """Configure logging for the application."""

  log_path = (
      Path("runs") / run_id / "logs"
      if logger_path is None
      else Path("runs") / logger_path / run_id / "logs"
  )
  log_path.mkdir(parents=True, exist_ok=True)
  logger.add(log_path / "app.log", rotation="100 MB")

  # Set the log path in thread-local storage
  _logging_state.log_path = log_path

  # Also persist the log path in the process environment so tools running in a different
  # thread (e.g., inside ADK tool execution) can still resolve the correct output dir.
  os.environ["SPECADIA_LOG_PATH"] = str(log_path)

  return log_path


def get_run_id():
  return str(int(time.time() * 1000))


def get_log_path() -> Optional[Path]:
  """Get the current log path from thread-local storage."""
  path = getattr(_logging_state, "log_path", None)
  if path is not None:
    return path

  # Fallback for tool execution contexts that do not share the caller's thread-local state.
  env_path = os.environ.get("SPECADIA_LOG_PATH")
  return Path(env_path) if env_path else None
