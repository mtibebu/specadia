"""Custom ADK plugins for Specadia."""

from typing import Any, Optional

from aiohttp import ClientPayloadError, ServerDisconnectedError
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.plugins import BasePlugin, ReflectAndRetryToolPlugin
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from loguru import logger

NO_RESPONSE_ERROR_TYPE = "agent_no_response"

# Transient connection errors that warrant a retry.
RETRYABLE_ERRORS = (ClientPayloadError, ConnectionResetError, ServerDisconnectedError)


class SpecadiaRetryPlugin(ReflectAndRetryToolPlugin):
  """ReflectAndRetryToolPlugin extended to detect empty/no-response agent tool results.

  When an agent produces no content, the agent returns ''
  (empty string). This subclass surfaces that as a retryable error so the LLM
  receives structured reflection guidance and retries the agent call.
  """

  async def extract_error_from_result(
      self,
      *,
      tool: BaseTool,
      tool_args: dict[str, Any],
      tool_context: ToolContext,
      result: Any,
  ) -> Optional[Any]:
    if isinstance(result, str) and not result.strip():
      return {"error": NO_RESPONSE_ERROR_TYPE, "message": "Agent returned no response."}
    if isinstance(result, dict) and result.get("error") == NO_RESPONSE_ERROR_TYPE:
      return result
    return None


class ConnectionRetryPlugin(BasePlugin):
  """Logs transient connection errors via on_model_error_callback.

  ADK's callback_context does not expose the LLM client, so this plugin
  cannot re-invoke the model itself. Instead it logs the error for
  observability. Actual retry logic lives in the run_agent() streaming loop.
  """

  async def on_model_error_callback(
      self,
      *,
      callback_context: CallbackContext,
      llm_request: LlmRequest,
      error: Exception,
  ) -> Optional[LlmResponse]:
    if isinstance(error, RETRYABLE_ERRORS):
      logger.warning(f"Transient connection error intercepted by plugin: {error}")
    return None  # Always propagate — retry handled at the runner level.
