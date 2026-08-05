# Specadia

**From intent to implementation.**

Specadia generates software requirements specifications (SRS) and system designs from
natural-language queries using multi-agent AI orchestration built on Google ADK. It supports
single-agent and multi-agent pipelines, user-managed RAG knowledge bases, and structured output
via Pydantic.

It can also turn an existing SRS and optional design document into a deterministic
implementation contract for Codex, Claude Code, or a generic coding harness.

## Plugin verification status

The thin coding-agent adapters have different verification levels:

- **Host installation verified:** Claude Code and Codex are installed, enabled, and expose
  Specadia's commands or skill.
- **Adapter execution verified:** OpenCode and Pi load their native adapters and register the
  Specadia skill.
- **Local installation verified, host not exercised:** the Cline skill installer and Cursor
  local-plugin link were tested, but the Cline and Cursor applications were not available for
  an in-host workflow test.
- **Static validation only:** Kimi Code CLI, Grok Build CLI, Devin CLI, GitHub Copilot, Factory
  Droid, Qwen Code, and Antigravity CLI. Their manifests or skills validate, but their host CLIs
  were not installed for end-to-end testing.

All repository plugin manifests parse and all bundled Agent Skills pass structural validation.
These checks do not constitute an end-to-end model-backed Specadia run in every host.

## Claude Code plugin

Specadia includes a thin Claude Code plugin. The plugin keeps the Python CLI as the
canonical engine and adds native `/specadia:specadia-plan` and
`/specadia:specadia-contract` commands.

Add this repository as a local marketplace, then install the plugin:

```bash
claude plugin marketplace add /path/to/specadia
claude plugin install specadia@specadia --scope user
```

The plan command preserves Specadia's interactive Collector approval and generates
a Claude-specific implementation contract without automatically starting implementation.

## Codex plugin

The thin Codex plugin exposes the `$specadia-plan` skill while keeping the Python CLI
as the canonical engine. Install it from the repository marketplace:

```bash
codex plugin marketplace add /path/to/specadia
codex plugin add specadia@personal
```

Start a new Codex thread, then ask:

```text
Use $specadia-plan to turn this software intent into an approved implementation contract.
```

## Cursor plugin

The Cursor plugin exposes `/specadia-plan` from Cursor's skill picker and uses Specadia's
generic harness contract until a dedicated Cursor contract format is added.

For local development, link the thin adapter into Cursor's local plugin directory:

```bash
mkdir -p ~/.cursor/plugins/local
ln -s /path/to/specadia/plugins/cursor/specadia ~/.cursor/plugins/local/specadia
```

Restart Cursor or run **Developer: Reload Window**, then invoke `/specadia-plan`.

## Kimi Code CLI plugin

The repository includes a native Kimi plugin manifest and `/specadia-plan` skill. Install the
local checkout from Kimi:

```text
/plugins install /path/to/specadia
```

Run `/reload` or start a new Kimi session after installing or updating.

## Cline skill adapter

Cline uses Agent Skills rather than its tools-and-hooks plugin API for this workflow. Enable
**Settings -> Features -> Enable Skills**, then link Specadia globally or per project:

```bash
./.cline/scripts/install-skills.sh --global
./.cline/scripts/install-skills.sh --project
```

Start a new Cline task after installing.

## Grok Build CLI plugin

The repository root is a native Grok plugin with a `/specadia-plan` skill. Install the local
checkout, then start a new Grok session:

```bash
grok plugin install /path/to/specadia
```

## Devin CLI plugin

Devin loads the root `skills/` directory by convention. Install the local checkout and start a
new session:

```bash
devin plugins install /path/to/specadia
devin plugins info specadia
```

The skill appears as `/specadia:specadia-plan`.

## GitHub Copilot plugin

Copilot CLI and VS Code Copilot Agent Plugins consume the repository's existing
Claude-compatible marketplace and plugin manifest. No duplicate Copilot-only manifest is
required.

For a local checkout, add the repository as a marketplace and install `specadia`:

```text
/plugin marketplace add /path/to/specadia
/plugin install specadia@specadia
```

Start a new Copilot session after installing.

## Factory Droid plugin

Factory Droid translates the existing Claude-compatible Specadia plugin automatically:

```bash
droid plugin marketplace add /path/to/specadia
droid plugin install specadia@specadia
```

Start a new Droid session after installing.

## Qwen Code plugin

Qwen Code converts the existing Claude-compatible plugin during installation:

```bash
qwen extensions install <github-owner>/specadia:specadia
```

This requires the repository to be published on GitHub. Start a new Qwen Code session after
installing.

## OpenCode plugin

The native OpenCode adapter registers Specadia's root skill directory and `/specadia-plan`
command. Add the local checkout to global or project `opencode.json`:

```json
{
  "plugin": ["/path/to/specadia"]
}
```

Restart OpenCode after changing the configuration.

## Pi package

Pi discovers the root Specadia skill through its native package metadata. Test the local checkout
directly:

```bash
pi -e /path/to/specadia
```

For a published GitHub repository, install with `pi install git:github.com/<owner>/specadia`.

## Antigravity CLI plugin

The repository root is a native Antigravity plugin bundle (`plugin.json` plus `skills/`):

```bash
agy plugin validate /path/to/specadia
agy plugin install /path/to/specadia
```

Start a new Antigravity session after installing.

## Installation

```bash
git clone <repository-url>
cd specadia
pyenv install -s 3.13.14
pyenv local 3.13.14
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Python 3.13 is the supported runtime for the agent stack; the repository's
`.python-version` selects the tested patch release when pyenv is available.

The core install supports deterministic contract generation and diagnostics.
Install only the capabilities you need:

```bash
python -m pip install -e ".[agents]"          # Multi-agent SRS/design generation
python -m pip install -e ".[agents,rag]"      # Agents plus local knowledge-base retrieval
python -m pip install -e ".[agents,rag,dev,test]"  # Full development install
```

Virtual environments contain launchers with absolute interpreter paths. If the
repository or environment is moved, recreate `.venv` and reinstall instead of
using a stale `.venv/bin/pip`; invoking pip as `python -m pip` is safest.

Set environment variables for your LLM provider as needed (for example
`GOOGLE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or
one of the local endpoint variables below). Validate the setup before a run:

```bash
specadia doctor --model openai/gpt-5
specadia-doctor --model ollama/qwen3 --no-network --json
```

### Local model providers

Specadia supports Ollama plus OpenAI-compatible local servers. Use a provider-qualified model
name; Specadia routes these providers locally, does not require hosted-provider credentials, and
checks endpoint reachability with `specadia doctor`.

| Provider | Model prefix | Endpoint variable | Default |
|---|---|---|---|
| Ollama chat API | `ollama_chat/` | `OLLAMA_BASE_URL` | `http://localhost:11434` |
| LM Studio | `lm_studio/` | `LM_STUDIO_API_BASE` | `http://localhost:1234/v1` |
| LocalAI | `localai/` | `LOCALAI_API_BASE` | `http://localhost:8080/v1` |
| vLLM | `vllm/` | `VLLM_API_BASE` | `http://localhost:8000/v1` |
| llama.cpp server | `llama_cpp/` | `LLAMA_CPP_API_BASE` | `http://localhost:8080/v1` |
| Any OpenAI-compatible server | `openai_compatible/` | `OPENAI_COMPATIBLE_API_BASE` | required |

Optional API keys are read from `LOCALAI_API_KEY`, `VLLM_API_KEY`, or
`OPENAI_COMPATIBLE_API_KEY`. Local servers that do not enforce authentication need no key.

```bash
# LM Studio
specadia doctor --model lm_studio/qwen3.5-9b
specadia run --query "Design a task manager" -m lm_studio/qwen3.5-9b

# Generic OpenAI-compatible endpoint
export OPENAI_COMPATIBLE_API_BASE=http://localhost:9000/v1
specadia doctor --model openai_compatible/my-local-model
specadia run --query "Design a task manager" -m openai_compatible/my-local-model
```

When Specadia runs in Docker and the model server runs on the host, set the endpoint to
`http://host.docker.internal:<port>/v1`.

## Docker

### Build

```bash
docker compose build
```

### Main CLI

```bash
docker compose run --rm specadia run \
  --query "Design a task management app" -t single_agent -m gemini-2.5-flash
```

### Ollama (local models)

OLLAMA_BASE_URL=http://host.docker.internal:11434 is pre-configured in docker-compose.yml. Start Ollama on your host then pass the model name directly:

```bash
docker compose run --rm specadia run \
  --query "Design a chat app" -t single_agent -m ollama_chat/qwen3.6:35b
```

## Usage

### Running the CLI

```bash
# Single agent mode
specadia run --query "Design a task management app" -t single_agent -m ollama_chat/qwen3.6:35b

# Multi-agent mode
specadia run --query "Design a chat app" -t read_agent -m ollama_chat/qwen3.6:35b
```

**Flags:**

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--query` | `-q` | Natural language query describing the software | — |
| `--agent-type` | `-t` | `single_agent` or `read_agent` (multi-agent) | `single_agent` |
| `--llm-model-name` | `-m` | LLM model name | `ollama_chat/qwen3.6:35b` |
| `--rag` | `-r` | Enable RAG retrieval | `false` |
| `--run-id` | `-i` | Unique run identifier | auto-generated |

Outputs are saved to `runs/{run_id}/logs/`.

### Generate a coding-agent contract

Generate a Codex `AGENTS.md` contract from an SRS:

```bash
specadia contract runs/example/logs/srs.md \
  --design runs/example/logs/design.md \
  --harness codex
```

Generate contracts for more than one harness:

```bash
specadia contract srs.md \
  --harness codex \
  --harness claude \
  --harness generic \
  --output-dir .specadia/contracts
```

The command emits the harness-specific Markdown files and
`contract-manifest.json`, which records source and output SHA-256 hashes. Existing
files are preserved unless `--force` is supplied. In a full Specadia installation,
the same command is available as `specadia contract`.

#### Hand the contract to an implementation harness

Contract generation is the end of Specadia's planning phase; it does not start an
implementation agent. The generated filename depends on the selected harness:

| Harness | Generated contract | How implementation receives it |
|---------|--------------------|--------------------------------|
| Codex | `AGENTS.md` | Codex discovers it as repository instructions when it is at the target repository root. |
| Claude Code | `CLAUDE.md` | Claude Code discovers it as project instructions when it is at the target repository root. |
| Generic | `AGENT_CONTRACT.md` | Attach the file or explicitly reference its path in the implementation prompt. |

`--output-dir` controls where Specadia writes artifacts; it does not install the
contract into another repository or make a harness load it automatically. After
reviewing the generated files, place the appropriate contract at the target
repository root, or explicitly reference it when the harness supports that
workflow. If the repository already has an `AGENTS.md` or `CLAUDE.md`, do not
blindly overwrite it. Merge the generated contract with the existing project
instructions, or keep it at a separate path and explicitly tell the harness to
follow both, resolving any conflicts before implementation.

Start a fresh harness session from the target repository so project instructions
are loaded, then give an explicit implementation request. For example:

```text
Implement the approved Specadia contract in this repository. Follow AGENTS.md,
preserve every requirement ID in implementation and test evidence, run the
relevant tests, and report the requirement-to-evidence mapping and residual risks.
```

For a generic harness, name the artifact directly:

```text
Implement the approved requirements in .specadia/contracts/AGENT_CONTRACT.md.
Use .specadia/contracts/traceability.md to confirm source-to-contract coverage,
then report code and test evidence for every requirement ID.
```

During final review, use `traceability.md` or `traceability.json` to confirm that
each approved requirement reached the generated contract, then compare those IDs
with the coding harness's implementation and test evidence. The traceability
artifacts validate planning outputs; they do not inspect the resulting code or
prove that implementation is complete.

Start from a user intent and run the existing multi-agent pipeline:

```bash
specadia-contract from-intent "Build an auditable inventory transfer service" \
  --harness codex \
  --harness claude \
  --run-id inventory-v1
```

This mode runs Collector first and displays its structured requirements draft.
Choose `approve` to continue, `refine` to provide feedback and rerun Collector,
or `cancel` to stop. Analyzer, Specifier, Designer, and Documenter do not run
until the Collector draft is explicitly approved. The approved SRS and design
are stored under `<output-dir>/sources/` and become the traceable inputs to the
generated contracts.

Runs are checkpointed atomically under `.specadia/sessions/`. Resume an
interrupted run without rerunning approved stages:

```bash
specadia-contract from-intent "Build an auditable inventory transfer service" \
  --run-id inventory-v1 \
  --resume \
  --force

specadia-contract runs
```

Use existing project context and an ordered model fallback chain:

```bash
specadia-contract from-intent "Add auditable inventory transfers" \
  --repo /path/to/existing/project \
  --llm-model-name openai/gpt-5 \
  --fallback-model anthropic/claude-sonnet-4-5 \
  --stage-timeout 240 \
  --harness codex
```

Repository inspection is bounded to manifests, file names, commands, and
convention files such as `AGENTS.md`; secrets, dependency trees, generated data,
and source bodies are excluded. Hosted models require confirmation unless
`--yes` is supplied.

Before contracts are written, Specadia rejects empty documents, unresolved
placeholders, missing/duplicate requirement IDs, and missing requirements or
architecture sections. Interactive runs can return failed documents to
Collector for another refinement. Every successful run emits
`traceability.json` and `traceability.md`, mapping requirement IDs across the
Collector draft, SRS, design, and contract.

Stage progress is printed to the terminal. Each stage has a configurable
timeout and ordered fallback models. Checkpoints preserve approved Collector
drafts and a completed SRS when a later Design stage fails.

### Release Verification

```bash
python -m pip install -e ".[test]"
python -m pytest -q
python -m compileall -q src
```

The normal suite uses no model provider. A live Collector smoke test is opt-in:

```bash
SPECADIA_LIVE_MODEL=openai/gpt-5 python -m pytest -m live
```

### Bring Your Own Knowledge Base

Install the RAG extra, then build a named, persistent collection from individual files or
directories. Directories are scanned recursively for Markdown, text, PDF, and JSON files.

```bash
python -m pip install -e ".[agents,rag]"

specadia rag build ./product-docs ./policies.json \
  --collection payments

specadia rag status payments
specadia rag query "How are refunds approved?" --collection payments

specadia run --query "Design our refund service" --rag \
  --rag-collection payments
```

`specadia-contract from-intent` accepts the same `--rag`, `--rag-collection`, and
`--rag-index-dir` options. Collections default to `.specadia/rag`; use `--rag-index-dir`
to keep them elsewhere. Re-running `rag build` keeps unchanged sources and replaces
changed files. Use `--rebuild` to discard the existing collection first.

SQLite databases are opened in read-only mode and ingestion is bounded to 10,000 rows:

```bash
specadia rag database ./catalog.sqlite --table products --collection catalog

# A single read-only SELECT or WITH statement is also supported.
specadia rag database ./catalog.sqlite \
  --query "SELECT sku, description FROM products WHERE active = 1" \
  --collection catalog
```

Specadia stores source hashes and retrieval metadata, including source file paths, in the
local collection. Keep `.specadia/rag` private and out of version control. Database
manifests never store SQL text, credentials, or an absolute database path. Queries
containing write/DDL operations, comments, multiple statements, or SQLite pragmas are
rejected. Cells and files are size-bounded; narrow large queries or split large document
sets before ingestion. Symbolic-link sources and collection directories are rejected so
ingestion and index writes cannot escape their configured roots. Collection artifacts are
hash-checked and structurally validated before FAISS loads them; rebuild older collections
that lack integrity metadata. Scanned/image-only PDFs need OCR before ingestion.

User collections use deterministic local embeddings and FAISS, so indexing and retrieval
do not send knowledge-base content to an embedding provider. The selected agent model may
still receive retrieved passages as prompt context; consider the model provider's data
handling policy. RAG collections work in local execution mode.

## Architecture

### Single Agent (`single_agent`)

One `SingleAgent` handles both requirements and design in a single pass.

### Multi-Agent (`read_agent`)

A `SequentialAgent` pipeline with specialized agents for each phase:

```
ReadWrapperAgent
├── RequirementsWrapperAgent
│   └── CollectorAgent → AnalyzerAgent → SpecifierAgent
└── DesignWrapperAgent
    └── DesignerAgent → DocumenterAgent
```

`ReadWrapperAgent` runs both sub-pipelines locally in one process using Google ADK's
`SequentialAgent`. No separate agent servers are required.

### Key Patterns

- **AgentBase** (`src/agents/agent_base.py`): All agents extend this base class, which provides LLM model init, system prompt, run mode, and RAG config. Each subclass implements `get_agent()` returning a Google ADK `Agent`.
- **LLM routing** (`src/agents/agent_util.py`): Gemini models use native ADK support; Ollama and others are wrapped via LiteLLM.
- **RAG** (`src/rag/`): Persistent user collections use deterministic local hashing embeddings and FAISS over Markdown, text, PDF, JSON, or bounded SQLite data. The selected local collection is registered as an agent tool when `--rag` is enabled.
- **Structured output**: Collector, Analyzer, and Designer agents produce Pydantic models; downstream agents consume these.

## Project Structure

```
specadia/
├── src/
│   ├── agents/           # Base agent classes and utilities
│   ├── requirement/      # Requirements agents (Collector, Analyzer, Specifier)
│   ├── design/           # Design agents (Designer, Documenter)
│   ├── single/           # Single agent implementation
│   ├── orchestrator/     # Agent orchestration and session management
│   ├── rag/              # User-managed FAISS knowledge bases
│   ├── prompt_templates/ # System prompts for each agent
│   ├── tools/            # Agent tools (save_to_file, RAG)
│   ├── utils/            # Logging, constants, helpers
│   └── main.py           # Main CLI entry point
├── runs/                 # Execution logs and outputs
└── pyproject.toml        # Project configuration
```

## Development

```bash
# Run tests
pytest

# Format code (pyink, 2-space indent, 100 char line length)
pyink src/
```

Python >= 3.12 required.

## License

Specadia Core and its harness adapters are licensed under the
[Apache License 2.0](LICENSE).

This license applies only to this repository. Any separately distributed
hosted service, cloud control plane, or commercial add-on may use different
license terms.

## Contributing

This is a research project. For contributions or questions, please open an issue.
