"""Wrapper agent to create a workflow of the RE agents."""

from typing import Optional
from pathlib import Path
from agents import AgentBase
from utils.constants import AgentRunMode, DEFAULT_MODEL_NAME

from google.adk.agents import SequentialAgent
from utils.logger import (get_run_id, setup_logging)
from requirement import CollectorAgent
from requirement import AnalyzerAgent
from requirement import SpecifierAgent


class RequirementsWrapperAgent(AgentBase):
  """This class defines the wrapper agent for the RE phase of the SDLC."""

  def __init__(
      self,
      llm_model_name: str,
      system_prompt: Optional[str] = None,
      run_mode: Optional[AgentRunMode] = AgentRunMode.MAIN,
      rag: Optional[bool] = True,
      rag_source: str = "default",
      rag_index_dir: Path = Path(".specadia/rag"),
  ):
    super().__init__(
        llm_model_name, system_prompt, run_mode, rag,
        rag_source=rag_source, rag_index_dir=rag_index_dir
    )
    self._collector_agent = CollectorAgent(
        llm_model_name,
        run_mode=run_mode,
        rag=rag,
        rag_source=rag_source,
        rag_index_dir=rag_index_dir,
    ).get_agent()
    self._analyzer_agent = AnalyzerAgent(
        llm_model_name, run_mode=run_mode, rag=rag
    ).get_agent()
    self._specifier_agent = SpecifierAgent(
        llm_model_name, run_mode=run_mode, rag=rag
    ).get_agent()

  def get_agent(self) -> SequentialAgent:
    return SequentialAgent(
        name="re_agent",
        sub_agents=[self._collector_agent, self._analyzer_agent, self._specifier_agent],
    )


# For testing in adk web ui
def __getattr__(name: str):
  if name == "root_agent":
    setup_logging(get_run_id(), "adk")
    return RequirementsWrapperAgent(DEFAULT_MODEL_NAME).get_agent()
  raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
