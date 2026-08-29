"""A wrapper agent for the RE and design agents in Specadia."""

from typing import Optional
from pathlib import Path
from specadia._agents import (
    AgentBase,
)
from dotenv import load_dotenv
import os
import time

import warnings

warnings.filterwarnings("ignore", category=UserWarning)

from google.adk.agents import Agent, SequentialAgent
from specadia._utils.logger import (get_run_id, setup_logging)
from specadia._design import DesignWrapperAgent
from specadia._requirement import RequirementsWrapperAgent
from specadia._utils.constants import (
    AgentRunMode,
    DEFAULT_MODEL_NAME,
)

# Load configs from .env file, if available.
load_dotenv()


def _agent_env_config() -> tuple[str, AgentRunMode, bool]:
  """Read agent config from environment variables."""
  model = os.getenv("SPECADIA_MODEL", DEFAULT_MODEL_NAME)
  run_mode = AgentRunMode[os.getenv("SPECADIA_RUN_MODE", "MAIN")]
  rag = os.getenv("SPECADIA_RAG", "false").lower() == "true"
  return model, run_mode, rag


# Lazy load root_agent (for testing with ADK Web) to avoid its creation during the import of ReadWrapperAgent.
_agent_cache: dict = {}


def __getattr__(name: str):
  if name == "root_agent":
    if name not in _agent_cache:
      setup_logging(get_run_id(), "adk")
      _agent_cache[name] = ReadWrapperAgent(DEFAULT_MODEL_NAME).get_agent()
    return _agent_cache[name]
  raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class ReadWrapperAgent(AgentBase):
  """This class defines the wrapper agent for the RE and design phases of the SDLC."""

  def __init__(
      self,
      llm_model_name: str,
      system_prompt: Optional[str] = None,
      run_mode: Optional[AgentRunMode] = AgentRunMode.MAIN,
      rag: Optional[bool] = False,
      rag_source: str = "default",
      rag_index_dir: Path = Path(".specadia/rag"),
  ):
    super().__init__(
        llm_model_name,
        system_prompt=system_prompt,
        run_mode=run_mode,
        rag=rag,
        rag_source=rag_source,
        rag_index_dir=rag_index_dir,
    )

  def get_agent(self) -> Agent:
    re_sub = RequirementsWrapperAgent(
        self._llm_model_name,
        run_mode=self._run_mode,
        rag=self._rag,
        rag_source=self._rag_source,
        rag_index_dir=self._rag_index_dir,
    ).get_agent()
    design_sub = DesignWrapperAgent(
        self._llm_model_name,
        run_mode=self._run_mode,
        rag=self._rag,
    ).get_agent()

    return SequentialAgent(
        name="read_agent",
        sub_agents=[re_sub, design_sub],
    )
