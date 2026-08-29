"""Wrapper agent to create a workflow of the Design agents."""

from typing import Optional
from specadia._agents import AgentBase
from specadia._utils.constants import AgentRunMode, DEFAULT_MODEL_NAME

from google.adk.agents import SequentialAgent
from specadia._utils.logger import (get_run_id, setup_logging)
from specadia._design import DesignerAgent
from specadia._design import DocumenterAgent


class DesignWrapperAgent(AgentBase):
  """This class defines the wrapper agent for the Design phase of the SDLC."""

  def __init__(
      self,
      llm_model_name: str,
      system_prompt: Optional[str] = None,
      run_mode: Optional[AgentRunMode] = AgentRunMode.MAIN,
      rag: Optional[bool] = True,
  ):
    super().__init__(llm_model_name, system_prompt, run_mode, rag)
    self._designer_agent = DesignerAgent(
        llm_model_name, run_mode=run_mode, rag=rag
    ).get_agent()
    self._documenter_agent = DocumenterAgent(
        llm_model_name, run_mode=run_mode, rag=rag
    ).get_agent()

  def get_agent(self) -> SequentialAgent:
    return SequentialAgent(
        name="design_agent",
        sub_agents=[self._designer_agent, self._documenter_agent],
    )


# For testing in adk web ui
def __getattr__(name: str):
  if name == "root_agent":
    setup_logging(get_run_id(), "adk")
    return DesignWrapperAgent(DEFAULT_MODEL_NAME).get_agent()
  raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
