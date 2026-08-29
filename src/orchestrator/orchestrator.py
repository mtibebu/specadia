"""A routing agent that orchestrates the multiple RE and design agents and outputs the design."""

import asyncio
from pathlib import Path
from typing import Optional

import litellm
import json
from aiohttp import (
    ClientPayloadError,
    ServerConnectionError,
    ServerDisconnectedError,
    ServerTimeoutError,
)
from pydantic import ValidationError
from google.adk.agents import BaseAgent
from google.adk.runners import Runner
from google.adk.apps import App
from google.adk.plugins import DebugLoggingPlugin
from google.genai import types
from loguru import logger

from .read_wrapper import ReadWrapperAgent
from specadia._orchestrator.constants import APP_NAME, MAX_RETRIES, RETRY_DELAY_BASE
from specadia._orchestrator.session_manager import SessionManager
from specadia._orchestrator.plugins import ConnectionRetryPlugin, SpecadiaRetryPlugin
from specadia._single import SingleAgent
from specadia._utils.constants import AgentRunMode
from specadia._utils.logger import get_log_path

# Enable this to debug litellm
# litellm._turn_on_debug()

_NO_RESPONSE = json.dumps({"error": "agent_no_response", "message": "Agent returned no response."})


def get_agent(
    llm_model_name: str,
    agent_type: str,
    run_mode: AgentRunMode,
    rag: bool,
    rag_source: str = "default",
    rag_index_dir: Path = Path(".specadia/rag"),
) -> BaseAgent:
  """Returns the agent based on the specified parameters.

  Args:
      llm_model_name: The LLM model
      agent_type: The agent type - single or multi-agent
      run_mode: The agent run mode
      rag: Whether the entry agent should use RAG

  Returns:
      The entry agent
  """
  if agent_type == "single_agent":
    agent = SingleAgent(
        llm_model_name,
        run_mode=run_mode,
        rag=rag,
        rag_source=rag_source,
        rag_index_dir=rag_index_dir,
    ).get_agent()
  elif agent_type == "read_agent":
    agent = ReadWrapperAgent(
        llm_model_name,
        run_mode=run_mode,
        rag=rag,
        rag_source=rag_source,
        rag_index_dir=rag_index_dir,
    ).get_agent()
  else:
    raise ValueError(f"Invalid agent type: {agent_type}")

  return agent


async def get_agent_response(
    query: str,
    llm_model_name: str,
    agent_type: str,
    run_mode: AgentRunMode,
    rag: bool,
    rag_source: str = "default",
    rag_index_dir: Path = Path(".specadia/rag"),
) -> str:
  """Gets the response from the agent.

  Args:
      query: The prompt from the user requesting for a system design
      llm_model_name: The LLM model
      agent_type: The agent type - single or multi-agent
      run_mode: The agent run mode
      rag: Shows whether the agents should use RAG
  """
  entry_agent = get_agent(
      llm_model_name, agent_type, run_mode, rag, rag_source, rag_index_dir
  )

  return await run_agent(query, entry_agent)


async def create_app_context(
    entry_agent: BaseAgent,
    app_name: str = APP_NAME,
    run_mode: Optional[AgentRunMode] = None,
) -> tuple[App, Runner, SessionManager]:
  """Create a reusable App/Runner/SessionManager context for repeated agent calls.

  Args:
      entry_agent: The root agent for the app
      app_name: The app name
      run_mode: The agent run mode (controls debug logging)

  Returns:
      A tuple of (app, runner, session_manager)
  """
  plugins = [
      ConnectionRetryPlugin(name="connection_retry"),
      SpecadiaRetryPlugin(max_retries=MAX_RETRIES),
  ]
  if run_mode not in (AgentRunMode.EVAL, AgentRunMode.BENCHMARK, AgentRunMode.CODE_BENCHMARK):
    log_path = get_log_path()
    debug_output = str(log_path / "adk_events.yaml") if log_path else "adk_events.yaml"
    plugins.append(DebugLoggingPlugin(output_path=debug_output))

  app = App(name=app_name, root_agent=entry_agent, plugins=plugins)
  session_manager = SessionManager()
  runner = session_manager.get_runner(app)
  return app, runner, session_manager


async def run_agent_with_context(
    query: str,
    runner: Runner,
    session_manager: SessionManager,
    app_name: str = APP_NAME,
) -> str:
  """Execute a query on a pre-built Runner, creating only a new session per call.

  Args:
      query: The user query
      runner: A pre-built Runner instance
      session_manager: The session manager that owns the runner's session service
      app_name: The app name for session creation

  Returns:
      The agent response string
  """
  session_id, user_id = await session_manager.create_new_session(app_name)

  content = types.Content(role="user", parts=[types.Part(text=query)])
  response = _NO_RESPONSE
  escalated_response: Optional[str] = None
  retryable_errors = (
      ClientPayloadError,
      ConnectionResetError,
      ServerConnectionError,
      ServerDisconnectedError,
      ServerTimeoutError,
      ValidationError,
      json.JSONDecodeError,
  )

  for attempt in range(1, MAX_RETRIES + 1):
    try:
      running = runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
      try:
        async for event in running:
          if event.actions and event.actions.escalate:
            escalated_response = f"Agent escalated: {event.error_message or 'No specific message.'}"
          if event.is_final_response():
            if event.content and event.content.parts:
              response = "".join(
                  part.text for part in event.content.parts if hasattr(part, "text") and part.text
              )
            else:
              continue
      finally:
        await running.aclose()
      if response != _NO_RESPONSE:
        break
      if attempt < MAX_RETRIES:
        delay = RETRY_DELAY_BASE**attempt
        logger.warning(
            f"Agent returned no response (attempt {attempt}/{MAX_RETRIES}). Retrying in {delay}s..."
        )
        await asyncio.sleep(delay)
    except retryable_errors as e:
      if attempt == MAX_RETRIES:
        raise
      delay = RETRY_DELAY_BASE**attempt
      logger.warning(
          f"Retryable error (attempt {attempt}/{MAX_RETRIES}): {type(e).__name__}: {e}. "
          f"Retrying in {delay}s..."
      )
      await asyncio.sleep(delay)

  return response or escalated_response


async def run_agent(
    query: str,
    entry_agent: Optional[BaseAgent] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    runner: Optional[Runner] = None,
    *,
    app_name: Optional[str] = APP_NAME,
    run_mode: Optional[AgentRunMode] = None,
    state_collector: Optional[dict] = None,
    initial_state: Optional[dict] = None,
) -> str:
  """
  Execute a single query against the supplied entry agent **inside an already‑created
  session**.  The caller is responsible for creating the session and passing the
  runner that will be reused across calls.

  Retries up to 3 times with exponential backoff if LLM model errors occur.

  Args:
    query: The user query
    entry_agent: The entry agent to use
    session_id: The session ID to use
    user_id: The user ID to use
    runner: The runner to use
    app_name: The app name to use
    run_mode: The run mode to use
    state_collector: The state collector to use
    initial_state: Initial ADK session state, used for approved pipeline handoffs

  Returns:
    The agent response string
  """
  current_session_id = session_id
  current_user_id = user_id
  current_runner = runner
  _session_manager: Optional[SessionManager] = None

  if (
      current_session_id is None or current_user_id is None or current_runner is None
  ) and entry_agent is not None:
    plugins = [
        ConnectionRetryPlugin(name="connection_retry"),
        SpecadiaRetryPlugin(max_retries=MAX_RETRIES),
    ]
    if run_mode not in (AgentRunMode.EVAL, AgentRunMode.BENCHMARK):
      log_path = get_log_path()
      debug_output = str(log_path / "adk_events.yaml") if log_path else "adk_events.yaml"
      plugins.append(DebugLoggingPlugin(output_path=debug_output))
    app = App(
        name=app_name,
        root_agent=entry_agent,
        plugins=plugins,
    )

    _session_manager = SessionManager()
    current_session_id, current_runner, current_user_id = await _session_manager.initialize_session(
        app=app, state=initial_state
    )
  elif entry_agent is None:
    raise ValueError("Entry agent is required")
  elif current_session_id is None or current_user_id is None or current_runner is None:
    raise ValueError("Session ID, user ID, and runner are required")

  content = types.Content(role="user", parts=[types.Part(text=query)])
  response = _NO_RESPONSE
  escalated_response: Optional[str] = None

  retryable_errors = (
      ClientPayloadError,
      ConnectionResetError,
      ServerConnectionError,
      ServerDisconnectedError,
      ServerTimeoutError,
      ValidationError,
      json.JSONDecodeError,
  )

  for attempt in range(1, MAX_RETRIES + 1):
    try:
      running = current_runner.run_async(
          user_id=current_user_id, session_id=current_session_id, new_message=content
      )
      try:
        async for event in running:
          if event.actions and event.actions.escalate:
            escalated_response = f"Agent escalated: {event.error_message or 'No specific message.'}"
          if event.is_final_response():
            if event.content and event.content.parts:
              response = "".join(
                  part.text for part in event.content.parts if hasattr(part, "text") and part.text
              )
            else:
              continue
      finally:
        await running.aclose()
      if response != _NO_RESPONSE:
        break  # Success — exit retry loop.
      if attempt < MAX_RETRIES:
        delay = RETRY_DELAY_BASE**attempt
        logger.warning(
            f"Agent returned no response (attempt {attempt}/{MAX_RETRIES}). Retrying in {delay}s..."
        )
        await asyncio.sleep(delay)
    except retryable_errors as e:
      if attempt == MAX_RETRIES:
        raise
      delay = RETRY_DELAY_BASE**attempt  # Exponential backoff: 2s, 4s, 8s
      logger.warning(
          f"Retryable error (attempt {attempt}/{MAX_RETRIES}): {type(e).__name__}: {e}. "
          f"Retrying in {delay}s..."
      )
      await asyncio.sleep(delay)

  if state_collector is not None and _session_manager is not None:
    try:
      session = await _session_manager.get_session().get_session(
          app_name=app_name, user_id=current_user_id, session_id=current_session_id
      )
      if session and session.state:
        state_collector.update(session.state)
    except Exception as e:
      logger.warning(f"Could not retrieve session state for state_collector: {e}")

  return response or escalated_response
