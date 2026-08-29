"""This is the first agent in the Design agent pipeline and generates the system and component design for the given requirements."""

from typing import Optional
from specadia._agents import (AgentBase, get_model_from, get_agent_config)
from specadia._utils.constants import (
    AgentRunMode,

    DEFAULT_MODEL_NAME,
    CONTENT_LENGTH_MAX,
    THINKING_BUDGET_STRUCTURED,
)
import time

from google.adk.agents import Agent
from specadia._utils.logger import (get_run_id, setup_logging)
from specadia._prompt_templates import DESIGNER_AGENT_SYSTEM_PROMPT
from .designer_models import DesignerOutputModel
from specadia._agents import (before_agent, after_agent, before_model, after_model)


class DesignerAgent(AgentBase):
  """This class defines the designer agent in the Design phase of the SDLC."""

  def __init__(
      self,
      llm_model_name: str,
      system_prompt: Optional[str] = DESIGNER_AGENT_SYSTEM_PROMPT,
      run_mode: Optional[AgentRunMode] = AgentRunMode.MAIN,
      rag: Optional[bool] = True,
  ):
    super().__init__(llm_model_name, system_prompt, run_mode, rag)

  def get_agent(self) -> Agent:
    return Agent(
        name="designer_agent",
        model=get_model_from(self._llm_model_name),
        description=(
            "A designer agent that generates the system and component design for the given"
            " requirements."
        ),
        instruction=self._system_prompt,
        generate_content_config=get_agent_config(
            CONTENT_LENGTH_MAX,
            thinking_budget=THINKING_BUDGET_STRUCTURED,
            llm_model_name=self._llm_model_name,
        ),
        output_schema=DesignerOutputModel,
        output_key="designer_output",
        before_agent_callback=before_agent,
        after_agent_callback=after_agent,
        before_model_callback=before_model,
        after_model_callback=after_model,
    )


# For testing in adk web ui
def __getattr__(name: str):
  if name == "root_agent":
    setup_logging(get_run_id(), "adk")
    return DesignerAgent(DEFAULT_MODEL_NAME).get_agent()
  raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
