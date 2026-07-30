import pytest

from agents.local_providers import is_local_model, local_openai_model_kwargs


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
