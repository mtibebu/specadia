from types import SimpleNamespace

from specadia._agents import agent_callbacks


class _State:

  def to_dict(self):
    return {"collector_output": "TOP-SECRET-VALUE"}


def test_agent_lifecycle_logs_only_state_keys(monkeypatch):
  messages = []
  monkeypatch.setattr(agent_callbacks.logger, "debug", messages.append)
  context = SimpleNamespace(
      agent_name="collector_agent",
      invocation_id="invocation-1",
      state=_State(),
  )

  agent_callbacks.before_agent(context)
  agent_callbacks.after_agent(context)

  combined = "\n".join(messages)
  assert "collector_output" in combined
  assert "TOP-SECRET-VALUE" not in combined


def test_model_logs_only_prompt_lengths(monkeypatch):
  messages = []
  monkeypatch.setattr(agent_callbacks.logger, "debug", messages.append)
  context = SimpleNamespace(agent_name="collector_agent")
  request = SimpleNamespace(
      contents=[
          SimpleNamespace(
              role="user",
              parts=[SimpleNamespace(text="PROMPT-SECRET-VALUE")],
          )
      ],
      config=SimpleNamespace(system_instruction="SYSTEM-SECRET-VALUE"),
  )

  agent_callbacks.before_model(context, request)

  combined = "\n".join(messages)
  assert "prompt chars=" in combined
  assert "PROMPT-SECRET-VALUE" not in combined
  assert "SYSTEM-SECRET-VALUE" not in combined


def test_model_response_log_does_not_include_generated_text(monkeypatch):
  messages = []
  monkeypatch.setattr(agent_callbacks.logger, "debug", messages.append)
  context = SimpleNamespace(agent_name="collector_agent")
  response = SimpleNamespace(
      content=SimpleNamespace(
          parts=[
              SimpleNamespace(
                  text="GENERATED-SECRET-VALUE",
                  function_call=None,
              )
          ]
      ),
      error_message=None,
  )

  agent_callbacks.after_model(context, response)

  combined = "\n".join(messages)
  assert "returned text; chars=" in combined
  assert "GENERATED-SECRET-VALUE" not in combined
