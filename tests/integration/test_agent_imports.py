def test_agents_import_without_rag_dependencies():
  from requirement.collector.collector_agent import CollectorAgent

  assert CollectorAgent.__name__ == "CollectorAgent"


def test_ollama_chat_uses_local_openai_compatibility_route(monkeypatch):
  from agents import agent_util

  captured = {}

  def fake_lite_llm(**kwargs):
    captured.update(kwargs)
    return kwargs

  monkeypatch.setattr(agent_util, "LiteLlm", fake_lite_llm)
  agent_util.get_model_from("ollama_chat/qwen3.6:35b")

  assert captured == {
      "model": "openai/qwen3.6:35b",
      "api_base": "http://localhost:11434/v1",
      "api_key": "ollama",
      "timeout": 400,
      "no-log": True,
  }


def test_lm_studio_uses_local_openai_compatibility_route(monkeypatch):
  from agents import agent_util

  captured = {}

  def fake_lite_llm(**kwargs):
    captured.update(kwargs)
    return kwargs

  monkeypatch.setattr(agent_util, "LiteLlm", fake_lite_llm)
  agent_util.get_model_from("lm_studio/qwen3.5-9b")

  assert captured == {
      "model": "openai/qwen3.5-9b",
      "api_base": "http://localhost:1234/v1",
      "api_key": "lm-studio",
      "timeout": 400,
      "no-log": True,
  }


def test_local_models_extend_best_effort_logging_timeout():
  from agents import agent_util
  from litellm.litellm_core_utils.logging_worker import GLOBAL_LOGGING_WORKER

  original_timeout = GLOBAL_LOGGING_WORKER.timeout
  try:
    GLOBAL_LOGGING_WORKER.timeout = 20
    agent_util.get_model_from("ollama_chat/qwen3.6:35b")
    assert GLOBAL_LOGGING_WORKER.timeout == 400
  finally:
    GLOBAL_LOGGING_WORKER.timeout = original_timeout


def test_generic_openai_compatible_provider_requires_endpoint(monkeypatch):
  from agents import agent_util

  monkeypatch.delenv("OPENAI_COMPATIBLE_API_BASE", raising=False)

  try:
    agent_util.get_model_from("openai_compatible/custom-model")
  except ValueError as error:
    assert "OPENAI_COMPATIBLE_API_BASE is required" in str(error)
  else:
    raise AssertionError("Expected missing endpoint to raise ValueError")
