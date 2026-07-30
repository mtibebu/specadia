"""Module for the requirements Collector agent."""

from .collector_agent import CollectorAgent
from .collector_models import CollectorOutputModel

__all__ = ["CollectorAgent", "root_agent", "CollectorOutputModel"]


def __getattr__(name: str):
  if name == "root_agent":
    from .collector_agent import root_agent

    return root_agent
  raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
