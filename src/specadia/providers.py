"""Dependency-free local provider endpoint parsing for diagnostics."""

import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class LocalProvider:
  name: str
  prefixes: tuple[str, ...]
  base_url_env: str
  default_base_url: str | None

  def base_url(self, environ: dict[str, str] | None = None) -> str | None:
    env = environ if environ is not None else os.environ
    return env.get(self.base_url_env) or self.default_base_url


LOCAL_PROVIDERS = (
    LocalProvider("lm-studio", ("lm_studio", "lm-studio"), "LM_STUDIO_API_BASE", "http://localhost:1234/v1"),
    LocalProvider("localai", ("localai",), "LOCALAI_API_BASE", "http://localhost:8080/v1"),
    LocalProvider("vllm", ("vllm",), "VLLM_API_BASE", "http://localhost:8000/v1"),
    LocalProvider("llama.cpp", ("llama_cpp", "llama-cpp"), "LLAMA_CPP_API_BASE", "http://localhost:8080/v1"),
    LocalProvider(
        "openai-compatible",
        ("openai_compatible", "openai-compatible"),
        "OPENAI_COMPATIBLE_API_BASE",
        None,
    ),
)


def local_provider_for(model: str) -> LocalProvider | None:
  prefix = model.lower().split("/", 1)[0]
  return next((provider for provider in LOCAL_PROVIDERS if prefix in provider.prefixes), None)


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
