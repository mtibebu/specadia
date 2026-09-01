# Contributing

Contributions are welcome through GitHub issues and pull requests.

## Development setup

Use Python 3.12 or 3.13 and work in a virtual environment:

```bash
uv python install 3.13
uv sync --all-extras
source .venv/bin/activate
uv run python -m pytest -q
```

A conventional venv fallback is also supported:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[full,test,dev]"
```

Install the `full`, `test`, and `dev` extras (or `--all-extras`) so that `pytest`,
`build`, and `twine` are all present before running tests or release checks.

`.python-version` selects a supported minor (3.12 or 3.13), not an exact patch, so pyenv/asdf/uv
resolve any installed patch of that minor.

Keep the public Python distribution dependency-light and under the `specadia` namespace. Harness
adapters should remain thin: shared contract behavior belongs in the Python engine.

Before opening a pull request, run the relevant tests and describe the input-to-output behavior
that changed. Do not include credentials, generated run logs, local indexes, or environment files.

## Release checks

Maintainers should build from a clean checkout and inspect the artifacts before publishing:

The `test`/`dev`/`full` extras (or `--all-extras`) must be installed first so that
`build` and `twine` exist. With those extras present, run from the managed
interpreter:

```bash
uv run python -m build
uv run python -m twine check dist/*
uv run python scripts/audit_distribution.py dist/*.whl
uv lock --check
npm pack --dry-run
```

As part of the clean-core-wheel release checks, also verify the missing-extra hint path for
`from-intent`: in a venv with only the core wheel installed (no `google-adk`), run
`specadia-contract from-intent "Build a todo app"` and confirm it exits non-zero with a single
clear `specadia[full]` install message and no traceback.

Publishing, tagging, and creating a GitHub release are separate maintainer actions and are not
performed by CI.

### Publishing to PyPI

Publishing is performed by the `.github/workflows/publish.yml` trusted-publishing workflow. It runs
automatically when a GitHub Release is published for an existing tag, and can be run manually to
recover a missed release event. It checks out the exact release tag and verifies it equals `v` plus
the `pyproject.toml` project version before building. Publishing uses PyPI OIDC
trusted publishing, so no PyPI token or secret is stored or needed.

Normal path: publish a GitHub Release for an existing `vMAJOR.MINOR.PATCH` tag (for example
`v0.2.7`); the workflow runs automatically and publishes to https://pypi.org/p/specadia. Tags may be
annotated or lightweight; GitHub UI-created release tags are typically lightweight, and both are
supported. Do not move or recreate the tag after the release is created.

Recovering a missed release event (for example if the Release was created before `publish.yml`
reached `main`, so no workflow run fired):

1. On GitHub, open **Actions → Publish to PyPI → Run workflow**.
2. Leave the **Branch** as `main`.
3. Enter the exact existing release tag (for example `v0.2.7`) in the **tag** field.
4. If a `pypi` environment approval is configured, approve it when prompted.
5. Click **Run workflow** and watch the run until it completes.

The manual dispatch builds only from the existing release tag you specify (annotated or
lightweight). It does not move or recreate the tag or the GitHub Release, does not bump the package
version, and does not run for arbitrary branches or commits (the input must be an existing
`vMAJOR.MINOR.PATCH` tag whose commit's `pyproject.toml` version matches). After the run, verify the
distribution on
https://pypi.org/p/specadia.
