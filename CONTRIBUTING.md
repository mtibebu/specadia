# Contributing

Contributions are welcome through GitHub issues and pull requests.

## Development setup

Use Python 3.12 or 3.13 and work in a virtual environment:

```bash
uv python install 3.13
uv sync --extra test --extra dev
source .venv/bin/activate
python -m pytest -q
```

A conventional venv fallback is also supported:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
```

`.python-version` selects a supported minor (3.12 or 3.13), not an exact patch, so pyenv/asdf/uv
resolve any installed patch of that minor.

Keep the public Python distribution dependency-light and under the `specadia` namespace. Harness
adapters should remain thin: shared contract behavior belongs in the Python engine.

Before opening a pull request, run the relevant tests and describe the input-to-output behavior
that changed. Do not include credentials, generated run logs, local indexes, or environment files.

## Release checks

Maintainers should build from a clean checkout and inspect the artifacts before publishing:

```bash
python -m build
python -m twine check dist/*
python scripts/audit_distribution.py dist/*.whl
uv lock --check
npm pack --dry-run
```

As part of the clean-core-wheel release checks, also verify the missing-extra hint path for
`from-intent`: in a venv with only the core wheel installed (no `google-adk`), run
`specadia-contract from-intent "Build a todo app"` and confirm it exits non-zero with a single
clear `specadia[full]` install message and no traceback.

Publishing, tagging, and creating a GitHub release are separate maintainer actions and are not
performed by CI.
