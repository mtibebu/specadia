"""Public API for deterministic implementation-contract generation."""

from importlib import import_module
import sys

from specadia._contracts.generator import ContractGenerator
from specadia._contracts.models import ContractBundle, Harness

for _module in (
    "context",
    "generator",
    "models",
    "requirement_ids",
    "session_store",
    "traceability",
    "validation",
    "workflow",
    "writer",
):
  sys.modules[f"{__name__}.{_module}"] = import_module(f"specadia._contracts.{_module}")

__all__ = ["ContractBundle", "ContractGenerator", "Harness"]
