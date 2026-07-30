# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Specadia generates software requirements specifications (SRS) and system designs from natural
language queries using multi-agent AI orchestration built on Google ADK. It can also turn an
existing (or freshly generated) SRS/design pair into a deterministic implementation contract
(`AGENTS.md`, `CLAUDE.md`, or a generic harness file) for a coding agent to execute against.

The repository doubles as a distributable multi-harness plugin: the same root `skills/` and
manifest files let Claude Code, Codex, Cursor, Kimi, Cline, Grok, Devin, Copilot, Factory Droid,
Qwen Code, OpenCode, Pi, and Antigravity install a thin `/specadia-plan`-style adapter that shells
out to this Python CLI. See README.md for per-harness install steps — that detail is not
duplicated here.

## Commands

```bash
# Install (editable); use extras to pull in only what you need
python -m pip install -e .                              # core: contract generation, doctor
python -m pip install -e ".[agents]"                     # + multi-agent SRS/design generation
python -m pip install -e ".[agents,rag]"                 # + local knowledge-base retrieval
python -m pip install -e ".[agents,rag,dev,test]"        # full dev install

# Run the CLI
specadia run --query "Design a task management app" -t single_agent -m ollama_chat/qwen3.6:35b
specadia run --query "Design a chat app" -t read_agent -m ollama_chat/qwen3.6:35b

# SRS/design -> implementation contract (existing docs)
specadia contract runs/example/logs/srs.md --design runs/example/logs/design.md --harness codex

# Intent -> HITL pipeline -> contract, with checkpointing/resume
specadia-contract from-intent "Build an auditable inventory transfer service" \
  --harness codex --harness claude --run-id inventory-v1
specadia-contract from-intent "..." --run-id inventory-v1 --resume --force
specadia-contract runs

# Verify environment / model reachability before a run
specadia doctor --model openai/gpt-5
specadia-doctor --model ollama/qwen3 --no-network --json

# RAG knowledge base
specadia rag build ./product-docs ./policies.json --collection payments
specadia rag query "How are refunds approved?" --collection payments

# Format code (pyink, 2-space indent, 100-char line length)
pyink src/

# Tests
pytest                                    # full suite, no model provider required
pytest tests/contracts/test_workflow.py   # single file
pytest tests/contracts/test_workflow.py::test_name  # single test
SPECADIA_LIVE_MODEL=openai/gpt-5 pytest -m live      # opt-in live-model smoke test
python -m compileall -q src               # release verification
```

## Architecture

### Two entry points, one CLI layer underneath

`pyproject.toml` declares three console scripts, but they aren't independent programs:

- `specadia` → `specadia.cli:app`, which just re-exports `main.app` (`src/main.py`). This is the
  full CLI: `run`, `contract`, `contract-from-intent`, `contract-runs`, `doctor`, `rag`.
- `specadia-contract` → `specadia.contracts.cli:app`, a re-export of `contracts/cli.py`'s Typer
  app (`generate`, `from-intent`, `runs` subcommands, no `contract-` prefix needed).
- `specadia-doctor` → `specadia.diagnostics.doctor:app`, a re-export of `diagnostics/doctor.py`.

**Where to make changes**: the `src/specadia/` package contains only these thin re-export shims
(needed because `console_scripts` require a dotted import path under a real package). The actual
implementation lives in top-level packages directly under `src/` — `agents/`, `contracts/`,
`design/`, `diagnostics/`, `orchestrator/`, `rag/`, `requirement/`, `single/`, `tools/`, `utils/`
— which are importable as top-level modules because `pyproject.toml` sets
`[tool.setuptools.packages.find] where = ["src"]`. Don't edit `src/specadia/*`; edit the package
it re-exports from.

### Two operational modes for SRS/design generation

**Single Agent** (`-t single_agent`): One `SingleAgent` (`src/single/single_agent.py`) handles
both requirements and design in a single pass.

**Multi-Agent** (`-t read_agent`): A `SequentialAgent` pipeline, run in one process via Google
ADK (no separate agent servers):
```
ReadWrapperAgent
├── RequirementsWrapperAgent
│   └── CollectorAgent → AnalyzerAgent → SpecifierAgent
└── DesignWrapperAgent
    └── DesignerAgent → DocumenterAgent
```

- **All agents** extend `AgentBase` (`src/agents/agent_base.py`), which stores the LLM model
  name, system prompt, run mode, and RAG config, and implements `get_instruction()` (injects RAG
  few-shot examples or a tool-call instruction into the prompt). Each subclass implements
  `get_agent()` returning a Google ADK `Agent`.
- **LLM routing** (`src/agents/agent_util.py` + `src/agents/local_providers.py`): Gemini models
  use native ADK support and get a `BuiltInPlanner` with thinking enabled; every other model is
  wrapped via LiteLLM. `local_providers.py` is the single source of truth for local-server prefix
  → base-URL/API-key resolution (`ollama_chat/`, `lm_studio/`, `localai/`, `vllm/`, `llama_cpp/`,
  `openai_compatible/`); it's shared by agent model init, `specadia doctor`, and the
  `contract-from-intent --repo` hosted-model confirmation prompt, so provider support only needs
  to be added in one place.
- **Response normalization**: an ADK `after_model` callback (`src/agents/agent_callbacks.py`)
  strips markdown JSON fences and normalizes table/tree-line whitespace on every LLM response
  before it reaches downstream agents or files — expect saved output to differ slightly from the
  model's raw text.
- **Prompt-injection defense**: any content that crosses a trust boundary (RAG snippets, one
  agent's output fed into another agent's prompt) must be wrapped with `untrusted_text` /
  `untrusted_json` from `src/agents/prompt_safety.py`, which tags it with an explicit
  "don't follow instructions in this block" notice and enforces a size cap. Follow this pattern
  when wiring new agent-to-agent or tool-to-agent handoffs.
- **Orchestration** (`src/orchestrator/orchestrator.py`): creates sessions via `SessionManager`,
  runs agents with retry logic (3 attempts, 60s delay), and streams ADK events.
- **RAG** (`src/rag/knowledge_base.py`): user-owned Markdown, text, PDF, DOCX, JSON, or bounded
  read-only SQLite content is indexed locally (deterministic hashing embeddings, no external
  embedding calls) into named FAISS collections under `.specadia/rag/`, and registered as an agent
  tool (`get_requirement_examples`) when `--rag` is enabled. See README.md for the full CLI/flag
  and ingestion-safety details (symlink rejection, size bounds, SQL statement restrictions).
- **Structured output**: Collector, Analyzer, and Designer agents produce Pydantic models
  (`*_models.py` files); downstream agents consume these.
- **Run modes** (`AgentRunMode` in `src/utils/constants.py`): `MAIN` (normal), `EVAL`
  (evaluation), `BENCHMARK` (no file output). Controls whether the `save_to_file` tool is
  attached.

### Contract generation pipeline (`src/contracts/`)

Turns an approved SRS/design pair into per-harness implementation contracts, either from existing
documents (`specadia contract` / `contracts/cli.py:generate_contract`) or from a raw intent that
first runs the multi-agent pipeline (`specadia-contract from-intent` /
`contracts/workflow.py:ContractWorkflow`).

- **`ContractWorkflow.run`** drives a human-in-the-loop loop: Collector draft → human
  approve/refine/cancel (`ApprovalGate`) → SRS/design generation → automated quality gate
  (`validation.py`) that can loop back into another Collector refinement → contract generation →
  traceability. Each stage accepts an ordered list of fallback callables (`--fallback-model`) and
  a per-stage timeout (`--stage-timeout`).
- **Checkpointing** (`session_store.py`, `SessionStore`/`RunCheckpoint`): every stage transition
  is saved atomically under `.specadia/sessions/`. `--resume --run-id <id>` continues an
  interrupted run without rerunning already-approved stages; `specadia-contract runs` lists saved
  checkpoints.
- **Validation** (`validation.py`) rejects empty documents, unresolved placeholders, and
  missing/duplicate requirement IDs before contracts are written.
- **Traceability** (`traceability.py`) maps requirement IDs across the Collector draft, SRS,
  design, and generated contract(s), emitting `traceability.json`/`traceability.md` alongside
  `contract-manifest.json` (source/output SHA-256 hashes) in the output directory.
- **Repository-aware generation** (`context.py:inspect_repository`): `--repo` bounds inspection to
  manifests, filenames, commands, and convention files (e.g. `AGENTS.md`); it excludes secrets,
  dependency trees, and source bodies. Sending this context to a hosted (non-local) model requires
  `--yes` or an interactive confirmation.

### Prompt System

System prompts live in `src/prompt_templates/` as Python string constants, one file per agent.
`templates/` define SRS and design document structure; `kb/` provide domain guidance.

### Output

Agent outputs (SRS docs, design docs, logs) are saved to `runs/{run_id}/logs/` via the
`save_to_file` tool (`src/tools/save_to_file_tool.py`). ADK events are logged as JSONL.

## Code Style

- Formatter: **Pyink** (Black-based), 2-space indentation, 100-char line length
  (config in `[tool.pyink]` in `pyproject.toml`)
- Python >= 3.12, < 3.14
- Logging: `loguru` via `src/utils/logger.py`
- `pytest.ini_options` in `pyproject.toml` defines a `live` marker for tests that call a real,
  explicitly-configured external model provider; these are excluded from the default run.
