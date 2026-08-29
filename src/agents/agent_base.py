"""Base interface for agent classes."""

from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path

from google.adk.agents import Agent

from specadia._utils.constants import AgentRunMode
from .agent_util import format_rag_few_shot


class AgentBase(ABC):
  """All agents use this base class."""

  @abstractmethod
  def __init__(
      self,
      llm_model_name: str,
      system_prompt: Optional[str] = None,
      run_mode: Optional[AgentRunMode] = AgentRunMode.MAIN,
      rag: Optional[bool] = False,
      rag_source: str = "default",
      rag_index_dir: Path = Path(".specadia/rag"),
  ):
    """
    The agent initialization.

    Args:
      llm_model_name: The LLM model
      system_prompt: The system prompt for the agent
      run_mode: The agent run mode, e.g. main, eval, or benchmark
      rag: Whether to use the RAG tool
      rag_source: Named collection created with ``specadia rag build``
    """
    self._llm_model_name = llm_model_name
    self._system_prompt = system_prompt or ""
    self._run_mode = run_mode
    self._rag = rag
    self._rag_source = rag_source
    self._rag_index_dir = rag_index_dir

  @abstractmethod
  def get_agent() -> Agent:
    pass

  def get_instruction(self, context) -> str:
    rag_examples = context.state.get("rag_examples")
    if rag_examples:
      return self._system_prompt + "\n" + format_rag_few_shot(rag_examples)
    if self._rag:
      return (
          self._system_prompt
          + "\n\nBefore generating the design, you MUST first call the"
          " `get_requirement_examples` tool with the user's query to retrieve example"
          " requirements. Use the returned examples to inform your requirements analysis."
      )
    return self._system_prompt
