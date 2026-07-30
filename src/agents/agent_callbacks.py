"""Callback functions before and after LLM and agent calls for logging."""

import re
from typing import Any, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from loguru import logger

_JSON_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*\n(.*?)\n\s*```\s*$", re.DOTALL)
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")


def _strip_json_fences(text: str) -> str:
  """Remove markdown code fences wrapping a JSON response."""
  m = _JSON_FENCE_RE.match(text)
  return m.group(1).strip() if m else text


def _normalize_markdown(text: str) -> str:
  """Strip trailing whitespace, table cell padding, and file-tree comment alignment."""
  result = []
  for line in text.splitlines():
    line = line.rstrip()
    if _TABLE_ROW_RE.match(line):
      cells = line.strip().split("|")
      line = "|" + "|".join(c.strip() for c in cells[1:-1]) + "|"
    elif line.lstrip()[:1] in "├└│":
      line = re.sub(r" {2,}#", " #", line)
    result.append(line)
  return "\n".join(result)


def after_rag_tool(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext, tool_response: dict
) -> Optional[dict]:
  """Captures RAG tool output into session state for prompt injection."""
  logger.debug(
      f"after_rag_tool called for tool '{tool.name}' with response type"
      f" {type(tool_response).__name__}."
  )
  if tool.name == "get_requirement_examples":
    tool_context.state["rag_examples"] = tool_response
    logger.debug("Captured RAG tool output into session state for few-shot injection.")
  return None


def before_agent(callback_context: CallbackContext) -> Optional[types.Content]:
  """Log agent entry without persisting potentially sensitive prompt/state content."""
  agent_name = callback_context.agent_name
  invocation_id = callback_context.invocation_id
  state_keys = sorted(callback_context.state.to_dict())
  logger.debug(
      f"Entering agent {agent_name} (invocation {invocation_id}); state keys={state_keys}"
  )
  return None


def after_agent(callback_context: CallbackContext) -> Optional[types.Content]:
  """Log agent exit without persisting potentially sensitive prompt/state content."""
  agent_name = callback_context.agent_name
  invocation_id = callback_context.invocation_id
  state_keys = sorted(callback_context.state.to_dict())
  logger.debug(
      f"Exiting agent {agent_name} (invocation {invocation_id}); state keys={state_keys}"
  )
  return None


def before_model(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
  """Callback to log input before LLM invocation."""
  agent_name = callback_context.agent_name
  user_prompt_chars = 0
  for content in reversed(llm_request.contents or []):
    if content.role == "user" and content.parts:
      text = content.parts[0].text
      if text:
        user_prompt_chars = len(text)
        break

  system_prompt = llm_request.config.system_instruction or types.Content(role="system", parts=[])
  if isinstance(system_prompt, str):
    system_prompt_chars = len(system_prompt)
  else:
    system_prompt_chars = sum(len(part.text or "") for part in system_prompt.parts or [])
  logger.debug(
      f"Invoking LLM for agent {agent_name}; system prompt chars={system_prompt_chars}; "
      f"user prompt chars={user_prompt_chars}."
  )

  return None


def after_model(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
  """Normalizes text responses: strips JSON fences, trailing whitespace, and table cell padding."""
  agent_name = callback_context.agent_name
  if llm_response.content and llm_response.content.parts:
    part = llm_response.content.parts[0]
    if part.text:
      stripped = _strip_json_fences(part.text)
      is_json = stripped.lstrip()[:1] in ("{", "[")
      cleaned = stripped if is_json else _normalize_markdown(stripped)
      if cleaned != part.text:
        logger.debug(f"Agent {agent_name}: normalized response (fences/whitespace/table padding).")
        part.text = cleaned
      logger.debug(f"Agent {agent_name} returned text; chars={len(part.text)}.")
    elif part.function_call:
      logger.debug(f"Agent {agent_name} made a function call '{part.function_call.name}'.")
    else:
      logger.debug(f"No text response from agent {agent_name}.")
  elif llm_response.error_message:
    logger.debug(f"Agent {agent_name} responded with error '{llm_response.error_message}'.")
  else:
    logger.debug(f"An empty LLM response from agent {agent_name}.")

  return None
