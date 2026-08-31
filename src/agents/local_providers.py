"""Local model provider routing shared by agents, diagnostics, and CLI safety checks.

The core provider definitions live in :mod:`specadia.providers`, which remains
dependency-free. This module re-exports them and adds only the agents-specific
``local_openai_model_kwargs`` helper.
"""

from specadia.providers import LOCAL_PROVIDERS
from specadia.providers import LocalProvider
from specadia.providers import is_local_model
from specadia.providers import local_provider_for
from specadia.providers import provider_host_port

__all__ = [
    "LocalProvider",
    "LOCAL_PROVIDERS",
    "local_provider_for",
    "provider_host_port",
    "is_local_model",
    "local_openai_model_kwargs",
]


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
