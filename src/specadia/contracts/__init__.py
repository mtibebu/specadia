"""Specadia implementation-contract generation."""

from importlib import import_module
import sys

_SUBMODULES = (
    "context",
    "generator",
    "models",
    "specadia_pipeline",
    "session_store",
    "traceability",
    "validation",
    "workflow",
    "writer",
)

for _name in _SUBMODULES:
  sys.modules[f"{__name__}.{_name}"] = import_module(f"contracts.{_name}")
