"""Module for the Requirements Analyzer agent."""

from .analyzer_agent import AnalyzerAgent
from .analyzer_models import AnalyzerOutputModel

__all__ = ["AnalyzerAgent", "root_agent", "AnalyzerOutputModel"]


def __getattr__(name: str):
  if name == "root_agent":
    from .analyzer_agent import root_agent

    return root_agent
  raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
