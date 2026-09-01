# Specadia

**From approved design to implementation-ready coding-agent contracts.**

Specadia is the public successor companion to
[README-MAS](https://github.com/NU-Academics/read-mas), the predecessor (upstream)
requirements-and-design system. READ-MAS produces requirements and system-design artifacts;
Specadia converts approved artifacts into deterministic, traceable contracts for coding-agent
harnesses and supplies thin plugin or skill adapters for those harnesses.

Specadia does not start an implementation agent and does not claim that generated code satisfies
the design. It prepares the handoff: harness instructions, source hashes, and requirement-level
traceability that reviewers can inspect before implementation begins.

## What it produces

Given an SRS Markdown file and an optional design Markdown file, Specadia emits:

- `AGENTS.md` for Codex;
- `CLAUDE.md` for Claude Code;
- `AGENT_CONTRACT.md` for a generic coding harness;
- `contract-manifest.json` with source and output SHA-256 hashes.

The repository also contains adapters for Claude Code, Codex, Cursor, Cline, Kimi, Grok, Devin,
GitHub Copilot, Factory Droid, Qwen Code, OpenCode, Pi, and Antigravity. The Python CLI remains the
canonical contract engine; adapters call or instruct that engine rather than duplicating it.

## Install

Specadia supports Python 3.12 and 3.13.

```bash
python -m pip install specadia
```

For a source checkout:

```bash
git clone https://github.com/mtibebu/specadia.git
cd specadia
uv python install 3.13
uv sync --all-extras
source .venv/bin/activate
```

`--all-extras` installs the `full`, `test`, and `dev` extras together. A bare
`python3.13` / `python -m pytest` / `python -m build` does **not** include `pytest`,
`build`, or `twine`, because those live only in the `test` and `dev` extras; you
must install the extras first (or use `uv run` as shown under
[Development](#development)).

A conventional venv fallback is also supported:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[full,test,dev]"
```

Use `.venv/bin/python` (or the activated env) consistently for all subsequent
`python` commands so `pytest`, `build`, and `twine` resolve from the same
environment.

`.python-version` selects a supported minor (3.12 or 3.13), not an exact patch, so pyenv/asdf/uv
resolve any installed patch of that minor.

The core wheel intentionally has no Google ADK dependency. It installs only deterministic
contract generation and diagnostics. Produce or approve requirements and designs separately,
then pass those files to Specadia.

## Generate from natural-language intent

The `specadia-contract from-intent` command turns a natural-language product intent into an SRS
and system design through a human-in-the-loop (HITL) agent pipeline, then emits coding-agent
contracts from the approved artifacts. This path depends on the optional agent stack:

```bash
python -m pip install "specadia[full]"
specadia-contract from-intent "Build a todo app" --harness codex
```

Progress is staged through Collector, Analyzer, Specifier, Designer, and Documenter agents, with
interactive approval/refinement at each quality gate. Saved HITL runs can be listed and resumed:

```bash
specadia-contract runs --sessions-dir .specadia/sessions
specadia-contract from-intent "Build a todo app" --run-id todo --resume
```

The core wheel deliberately omits the agent stack, so `from-intent` is unavailable there. If a
core-only install (or the `.[test]` environment without `google-adk`) invokes `from-intent`, the
CLI fails cleanly with a single hint rather than a traceback:

```
Natural-language intent-to-contract requires the agent extras. Install with: pip install "specadia[full]"
```

The deterministic `generate` and `runs` commands remain dependency-free and work in the core wheel.

## Generate a contract

The canonical contract-generation command is `specadia-contract generate`:

```bash
specadia-contract generate requirements.md \
  --design design.md \
  --harness codex \
  --output-dir .specadia/contracts
```

Generate several harness formats in one run:

```bash
specadia-contract generate requirements.md \
  --design design.md \
  --harness codex \
  --harness claude \
  --harness generic
```

> Note: the primary CLI subcommand `specadia contract ...` is a retained alias that
> behaves identically to `specadia-contract generate ...`. Both resolve to the same
> `generate_contract` command and accept the same options.

Existing output files are preserved unless `--force` is supplied. Review generated instructions
before placing them at a target repository root. If a repository already has `AGENTS.md` or
`CLAUDE.md`, merge the instructions deliberately instead of overwriting project policy.

Useful checks:

```bash
specadia --version
specadia doctor --model ollama/qwen3 --no-network
specadia-contract --help
```

## Demo

See the [Bookmark Buddy demo](examples/bookmark-buddy/README.md) for a self-contained,
credential-free walkthrough of intent → contract and determinism checks.

[Watch the two-minute demo](examples/bookmark-buddy/assets/specadia-bookmark-buddy-demo.mp4).

## Harness adapters

### Claude Code

```bash
claude plugin marketplace add https://github.com/mtibebu/specadia.git
claude plugin install specadia@specadia --scope user
```

Use `/specadia:specadia-contract` with existing requirements and design artifacts.

### Codex

```bash
codex plugin marketplace add https://github.com/mtibebu/specadia.git
codex plugin add specadia@personal
```

Invoke `$specadia-plan` and provide the approved input artifact paths.

### Other adapters

Adapter manifests and skills live under [`plugins/`](plugins/) and the harness-specific hidden
directories at the repository root. Their installation formats differ, but they share the same
contract boundary: design artifacts in, reviewable harness instructions out.

Examples using repository coordinates:

```bash
qwen extensions install mtibebu/specadia:specadia
pi install git:github.com/mtibebu/specadia
```

## Development

Prefer uv so every command runs against the same managed interpreter with the
full set of extras (`full`, `test`, and `dev` — including `build` and `twine`):

```bash
uv python install 3.13
uv sync --all-extras
uv run python -m pytest -q
uv run python -m build
uv run python -m twine check dist/*
```

If your shell does not expand `dist/*` (or no artifacts exist yet), run `uv run python -m build`
first, then pass the matched files explicitly, e.g.
`uv run python -m twine check dist/*` or `uv run python -m twine check $(ls dist | sed 's#^#dist/#')`.

The conventional venv equivalent is `python -m pip install -e ".[full,test,dev]"` followed by
`python -m pytest -q`, `python -m build`, and `python -m twine check dist/*` — the uv-first path
above is preferred and must include `build`/`twine` via `--all-extras`.

CI tests Python 3.12 and 3.13, builds both distribution formats, checks wheel contents against an
allowlist, and runs the installed core CLIs in an environment without Google ADK.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution and release-check instructions,
[SECURITY.md](SECURITY.md) for private vulnerability reporting, and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community expectations.

## License

Apache License 2.0. See [LICENSE](LICENSE).
