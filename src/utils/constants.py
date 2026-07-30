"""Constants common across modules are defined here."""

import os
from enum import StrEnum

DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL_NAME = f"{DEFAULT_PROVIDER}_chat/qwen3.6:35b"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_BASE = f"{OLLAMA_BASE_URL}/v1"


class AgentRunMode(StrEnum):
  """Run modes for the Specadia agents: eval, benchmark, or main"""

  TRAIN = "train"
  EVAL = "eval"
  BENCHMARK = "benchmark"
  CODE_BENCHMARK = "code_benchmark"
  LLM_BENCHMARK = "llm_benchmark"
  MAIN = "main"





NUMBER_OF_TRIES = 1

THINKING_BUDGET = 8192
THINKING_BUDGET_STRUCTURED = 2048



CONTENT_LENGTH_MAX = 64000
CONTENT_LENGTH_LARGE = 16384
CONTENT_LENGTH_MEDIUM = 8192
CONTENT_LENGTH_SMALL = 4096

LITE_LLM_TIMEOUT = 400

LOCAL_LLM_TASK_TIMEOUT = 1200
