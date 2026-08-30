"""Local model provider routing shared by agents, diagnostics, and CLI safety checks."""

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from specadia.providers import is_local_model


@dataclass(frozen=True)
class LocalProvider:
  name: str
  prefixes: tuple[str, ...]
  base_url_env: str
  default_base_url: str | None
  api_key_env: str | None = None

  def base_url(self, environ: dict[str, str] | None = None) -> str | None:
    env = environ if environ is not None else os.environ
    return env.get(self.base_url_env) or self.default_base_url

  def api_key(self, environ: dict[str, str] | None = None) -> str:
    env = environ if environ is not None else os.environ
    if self.api_key_env and env.get(self.api_key_env):
      return env[self.api_key_env]
    return self.name


LOCAL_PROVIDERS = (
    LocalProvider("lm-studio", ("lm_studio", "lm-studio"), "LM_STUDIO_API_BASE", "http://localhost:1234/v1"),
    LocalProvider("localai", ("localai",), "LOCALAI_API_BASE", "http://localhost:8080/v1", "LOCALAI_API_KEY"),
    LocalProvider("vllm", ("vllm",), "VLLM_API_BASE", "http://localhost:8000/v1", "VLLM_API_KEY"),
    LocalProvider(
        "llama.cpp",
        ("llama_cpp", "llama-cpp"),
        "LLAMA_CPP_API_BASE",
        "http://localhost:8080/v1",
    ),
    LocalProvider(
        "openai-compatible",
        ("openai_compatible", "openai-compatible"),
        "OPENAI_COMPATIBLE_API_BASE",
        None,
        "OPENAI_COMPATIBLE_API_KEY",
    ),
)


def local_provider_for(model: str) -> LocalProvider | None:
  prefix = model.lower().split("/", 1)[0]
  return next(
      (provider for provider in LOCAL_PROVIDERS if prefix in provider.prefixes),
      None,
  )


def local_openai_model_kwargs(
    model: str,
    *,
    environ: dict[str, str] | None = None,
) -> dict[str, str]:
  provider = local_provider_for(model)
  if provider is None:
    raise ValueError(f"Unsupported local provider prefix in model {model!r}")
  if "/" not in model or not model.split("/", 1)[1]:
    prefixes = ", ".join(provider.prefixes)
    raise ValueError(f"Model name is required after local provider prefix ({prefixes}/<model>)")
  base_url = provider.base_url(environ)
  if not base_url:
    raise ValueError(
        f"{provider.base_url_env} is required for the {provider.name} local provider"
    )
  return {
      "model": f"openai/{model.split('/', 1)[1]}",
      "api_base": base_url.rstrip("/"),
      "api_key": provider.api_key(environ),
  }


def provider_host_port(
    provider: LocalProvider,
    environ: dict[str, str] | None = None,
) -> tuple[str, int, str] | None:
  base_url = provider.base_url(environ)
  if not base_url:
    return None
  parsed = urlparse(base_url)
  host = parsed.hostname or "localhost"
  port = parsed.port or (443 if parsed.scheme == "https" else 80)
  return host, port, base_url
