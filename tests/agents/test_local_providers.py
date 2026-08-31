import pytest

import specadia.providers as providers
from specadia._agents.local_providers import LOCAL_PROVIDERS
from specadia._agents.local_providers import LocalProvider
from specadia._agents.local_providers import is_local_model
from specadia._agents.local_providers import local_openai_model_kwargs
from specadia._agents.local_providers import local_provider_for
from specadia._agents.local_providers import provider_host_port


@pytest.mark.parametrize(
    ("model", "api_base"),
    [
        ("lm_studio/model", "http://localhost:1234/v1"),
        ("localai/model", "http://localhost:8080/v1"),
        ("vllm/model", "http://localhost:8000/v1"),
        ("llama_cpp/model", "http://localhost:8080/v1"),
    ],
)
def test_named_local_provider_defaults(model: str, api_base: str):
  assert local_openai_model_kwargs(model)["api_base"] == api_base
  assert is_local_model(model)


def test_generic_provider_uses_configured_endpoint_and_key():
  kwargs = local_openai_model_kwargs(
      "openai_compatible/private-model",
      environ={
          "OPENAI_COMPATIBLE_API_BASE": "http://localhost:9000/v1/",
          "OPENAI_COMPATIBLE_API_KEY": "secret",
      },
  )

  assert kwargs == {
      "model": "openai/private-model",
      "api_base": "http://localhost:9000/v1",
      "api_key": "secret",
  }


def test_hosted_openai_model_is_not_local():
  assert is_local_model("openai/gpt-5") is False


def test_agent_localprovider_is_core_localprovider():
  assert LocalProvider is providers.LocalProvider


def test_agent_local_providers_is_core_local_providers():
  assert LOCAL_PROVIDERS is providers.LOCAL_PROVIDERS


def test_re_exports_are_same_objects():
  assert local_provider_for is providers.local_provider_for
  assert provider_host_port is providers.provider_host_port
  assert is_local_model is providers.is_local_model


@pytest.mark.parametrize(
    ("model", "api_key_env", "default_key"),
    [
        ("vllm/model", "VLLM_API_KEY", "vllm"),
        ("localai/model", "LOCALAI_API_KEY", "localai"),
        ("openai_compatible/model", "OPENAI_COMPATIBLE_API_KEY", "openai-compatible"),
    ],
)
def test_api_key_env_available_via_providers_and_agents(
    model: str, api_key_env: str, default_key: str
):
  provider = providers.local_provider_for(model)
  assert provider is not None
  assert provider.api_key_env == api_key_env
  # Default (unset) falls back to the provider name.
  assert provider.api_key({}) == default_key
  # Set value is honored through both the core and agent re-export.
  assert provider.api_key({api_key_env: "sekrit"}) == "sekrit"
  agent_provider = local_provider_for(model)
  assert agent_provider is provider
  assert agent_provider.api_key({api_key_env: "sekrit"}) == "sekrit"


def test_lm_studio_and_llama_cpp_have_no_api_key_env():
  for model in ("lm_studio/model", "llama_cpp/model"):
    provider = providers.local_provider_for(model)
    assert provider is not None
    assert provider.api_key_env is None
    # api_key falls back to the provider name when no key env is configured.
    assert provider.api_key({}) == provider.name


def test_local_openai_model_kwargs_unsupported_prefix_raises():
  with pytest.raises(ValueError):
    local_openai_model_kwargs("unknown/model")


def test_local_openai_model_kwargs_missing_name_raises():
  with pytest.raises(ValueError):
    local_openai_model_kwargs("vllm/")


def test_local_openai_model_kwargs_missing_base_url_raises():
  with pytest.raises(ValueError):
    local_openai_model_kwargs("openai_compatible/model", environ={})
