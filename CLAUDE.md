# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Specadia is the public successor companion to [README-MAS](https://github.com/NU-Academics/read-mas),
the predecessor (upstream) requirements-and-design system. Specadia converts approved SRS and
optional system designs into deterministic implementation contracts (`AGENTS.md`, `CLAUDE.md`, or
a generic harness file) for coding agents. The core wheel installs only deterministic contract
generation and diagnostics; intent-to-SRS/design generation is available on
`specadia-contract from-intent` with the optional `specadia[full]` agent dependencies.

The repository doubles as a distributable multi-harness plugin: the same root `skills/` and
manifest files let Claude Code, Codex, Cursor, Kimi, Cline, Grok, Devin, Copilot, Factory Droid,
Qwen Code, OpenCode, Pi, and Antigravity install a thin `/specadia-plan`-style adapter that shells
out to this Python CLI. See README.md for per-harness install steps — that detail is not
duplicated here.

## Commands

```bash
# Install (editable); use the full extra only when maintaining legacy internals
python -m pip install -e .                              # core: contract generation, doctor
python -m pip install -e ".[test]"                     # core development and tests
python -m pip install -e ".[full,test,dev]"            # all private/legacy implementation deps

# SRS/design -> implementation contract (existing docs)
specadia contract requirements.md --design design.md --harness codex
specadia-contract generate requirements.md --design design.md --harness claude

# Verify the local core environment
specadia doctor --no-network --json
specadia-doctor --no-network --json

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

### Three public entry points

`pyproject.toml` declares three console scripts, but they aren't independent programs:

- `specadia` → `specadia.cli:app`, with `contract` and `doctor` commands.
- `specadia-contract` → `specadia.contracts.cli:app`, with the deterministic `generate` command.
- `specadia-doctor` → `specadia.diagnostics.doctor:app`.

**Where to make changes**: `src/specadia/` defines the public package and CLI adapters. The
implementation source directories under `src/` are packaged only as private `specadia._*`
namespaces through explicit `pyproject.toml` mappings; they must never be imported as top-level
packages by shipped code. Public imports belong under `specadia`, `specadia.contracts`, or
`specadia.diagnostics`.

### Private legacy agent implementation

The optional `full` extra supports maintenance and testing of the existing agent and RAG
implementation under private `specadia._*` namespaces. It is not part of the public CLI contract.

**Single Agent**: One `SingleAgent` (`src/single/single_agent.py`) handles both requirements and
design in a single pass.

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
  private agent paths, so provider support only needs to be added in one place.
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
  tool (`get_requirement_examples`) when private RAG support is enabled. Its ingestion boundary
  rejects symlinks, oversized inputs, and non-read-only SQL statements.
- **Structured output**: Collector, Analyzer, and Designer agents produce Pydantic models
  (`*_models.py` files); downstream agents consume these.
- **Run modes** (`AgentRunMode` in `src/utils/constants.py`): `MAIN` (normal), `EVAL`
  (evaluation), `BENCHMARK` (no file output). Controls whether the `save_to_file` tool is
  attached.

### Contract generation pipeline (`src/contracts/`)

Turns an approved READ-MAS SRS/design pair into per-harness implementation contracts from existing
documents (`specadia contract` or `specadia-contract generate`). Contract generation is
deterministic and does not invoke an LLM.

- The private **`ContractWorkflow.run`** legacy adapter drives a human-in-the-loop loop: Collector draft → human
  approve/refine/cancel (`ApprovalGate`) → SRS/design generation → automated quality gate
  (`validation.py`) that can loop back into another Collector refinement → contract generation →
  traceability. Each stage accepts an ordered list of fallback callables (`--fallback-model`) and
  a per-stage timeout (`--stage-timeout`).
- **Checkpointing** (`session_store.py`, `SessionStore`/`RunCheckpoint`) belongs to that private
  legacy adapter and is not exposed by the public console scripts.
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
