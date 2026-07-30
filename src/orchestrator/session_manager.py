"""Manages the session for the orchestrator agent."""

import uuid
from typing import Optional

from google.adk.apps import App
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.runners import Runner


class SessionManager:
  """Manages the session for the orchestrator agent."""

  def __init__(self):
    self._session_service = InMemorySessionService()
    self._user_id = str(uuid.uuid4())

  def get_session(self) -> BaseSessionService:
    return self._session_service

  def get_user_id(self) -> str:
    return self._user_id

  def get_session_id(self) -> str:
    return str(uuid.uuid4())

  def get_runner(self, app: App) -> Runner:
    return Runner(app=app, session_service=self._session_service)

  async def create_new_session(self, app_name: str) -> tuple[str, str]:
    """Create a new session on the existing service without recreating the Runner.

    Args:
        app_name: The app name to create the session for

    Returns:
        A tuple of (session_id, user_id)
    """
    session_id = self.get_session_id()
    await self._session_service.create_session(
        app_name=app_name, user_id=self._user_id, session_id=session_id
    )
    return session_id, self._user_id

  async def initialize_session(self, app: App = None, state: Optional[dict] = None) -> tuple:
    if app is None:
      raise ValueError("App is required")
    session_id = self.get_session_id()
    await self._session_service.create_session(
        app_name=app.name,
        user_id=self._user_id,
        session_id=session_id,
        state=state,
    )
    runner = self.get_runner(app)
    return session_id, runner, self._user_id
