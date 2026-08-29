"""This is the first agent in the RE agent pipeline and collects and self elicits requirements and generates raw requirements."""

from typing import Optional
from pathlib import Path
from specadia._agents import (AgentBase, get_model_from, get_planner_for)
from specadia._utils.constants import (AgentRunMode, DEFAULT_MODEL_NAME, CONTENT_LENGTH_SMALL)
import time

from google.adk.agents import Agent

from specadia._utils.logger import (get_run_id, setup_logging)
from specadia._prompt_templates import COLLECTOR_AGENT_SYSTEM_PROMPT
from .collector_models import CollectorOutputModel
from specadia._agents import (
    add_rag_tool,
    before_agent,
    after_agent,
    before_model,
    after_model,
    after_rag_tool,
    get_agent_config,
)


class CollectorAgent(AgentBase):
  """This class defines the collector agent in the RE phase of the SDLC."""

  def __init__(
      self,
      llm_model_name: str,
      system_prompt: Optional[str] = COLLECTOR_AGENT_SYSTEM_PROMPT,
      run_mode: Optional[AgentRunMode] = AgentRunMode.MAIN,
      rag: Optional[bool] = True,
      rag_source: str = "default",
      rag_index_dir: Path = Path(".specadia/rag"),
  ):
    super().__init__(
        llm_model_name, system_prompt, run_mode, rag, rag_source, rag_index_dir
    )

  def get_agent(self) -> Agent:
    tools = []
    add_rag_tool(tools, self._rag, self._rag_source, self._rag_index_dir)

    planner = get_planner_for(self._llm_model_name)

    return Agent(
        name="collector_agent",
        model=get_model_from(self._llm_model_name),
        description=(
            "A requirements collector agent that generates raw requirements from a user's query"
        ),
        instruction=self.get_instruction,
        planner=planner,
        tools=tools,
        generate_content_config=get_agent_config(
            CONTENT_LENGTH_SMALL, llm_model_name=self._llm_model_name
        ),
        output_schema=CollectorOutputModel,
        output_key="collector_output",
        after_tool_callback=after_rag_tool if self._rag else None,
        before_agent_callback=before_agent,
        after_agent_callback=after_agent,
        before_model_callback=before_model,
        after_model_callback=after_model,
    )


# For testing in adk web ui
def __getattr__(name: str):
  if name == "root_agent":
    setup_logging(get_run_id(), "adk")
    return CollectorAgent(DEFAULT_MODEL_NAME).get_agent()
  raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
