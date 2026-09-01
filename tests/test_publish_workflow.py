"""Guard the PyPI trusted-publishing workflow against security regressions.

Reads ``.github/workflows/publish.yml`` as plain text (no PyYAML, no network)
and asserts the contract invariants that keep publishing safe:

  * the workflow only runs for a published GitHub Release (never on push/PR);
  * the whole workflow holds least privilege (``contents: read``), and OIDC
    ``id-token: write`` appears only in the ``publish`` job -- the ``build``
    job never receives identity-token permission;
  * every action is pinned to an immutable 40-char commit SHA (no floating
    ``@vX`` tags or ``@main``);
  * the release tag is checked out and verified against ``v`` + the
    ``pyproject.toml`` project version before any artifact is built;
  * publishing relies on OIDC trusted publishing, so no ``secrets.`` token is
    ever referenced;
  * the ``build`` job hands a ``pypi-dist`` artifact to the ``publish`` job.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = (ROOT / ".github" / "workflows" / "publish.yml").read_text(
    encoding="utf-8"
)

REQUIRED_SHAS = [
    "11d5960a326750d5838078e36cf38b85af677262",  # actions/checkout v4.4.0
    "a26af69be951a213d495a4c3e4e4022e16d87065",  # actions/setup-python v5.6.0
    "ea165f8d65b6e75b540449e92b4886f43607fa02",  # actions/upload-artifact v4.6.2
    "d3f86a106a0bac45b974a628896c90dbdf5c8093",  # actions/download-artifact v4.3.0
    "dc37677b2e1c63e2034f94d8a5b11f265b73ba33",  # pypa/gh-action-pypi-publish v1.14.2
]


def _on_block() -> str:
    """Return the ``on:`` trigger block, up to the first ``jobs:`` heading."""
    jobs_idx = WORKFLOW.index("jobs:")
    return WORKFLOW[:jobs_idx]


def test_trigger_is_release_published_only():
    on_block = _on_block()
    assert "release" in on_block
    assert "published" in on_block
    for forbidden in ("pull_request_target", "push:", "workflow_dispatch",
                      "pull_request", "schedule"):
        assert forbidden not in on_block, f"forbidden trigger key present: {forbidden}"


def test_global_permissions_are_contents_read():
    on_block = _on_block()
    assert "permissions:" in on_block
    assert "contents: read" in on_block


def test_two_jobs_with_build_before_publish():
    assert "build:" in WORKFLOW
    assert "publish:" in WORKFLOW
    assert "needs: build" in WORKFLOW


def test_checkout_uses_release_tag_and_no_persistent_credentials():
    assert "github.event.release.tag_name" in WORKFLOW
    assert "persist-credentials: false" in WORKFLOW


def test_release_tag_version_gate_is_present():
    assert "tomllib" in WORKFLOW
    assert "::error::" in WORKFLOW


def test_all_actions_pinned_to_immutable_sha():
    for sha in REQUIRED_SHAS:
        assert sha in WORKFLOW, f"missing pinned SHA: {sha}"
    # No floating major/minor tags like @v4 or @main.
    assert "@main" not in WORKFLOW
    import re
    assert not re.search(r"@v\d", WORKFLOW), "floating version tag found"


def test_oidc_permission_only_in_publish_job():
    assert "id-token: write" in WORKFLOW
    publish_idx = WORKFLOW.index("publish:")
    id_token_idx = WORKFLOW.index("id-token")
    assert id_token_idx > publish_idx, "id-token appears before the publish job"


def test_no_secret_token_references():
    assert "${{ secrets." not in WORKFLOW
    assert "secrets." not in WORKFLOW


def test_artifact_handoff_and_policies():
    assert "name: pypi-dist" in WORKFLOW
    assert "if-no-files-found: error" in WORKFLOW


def test_attestations_enabled():
    assert "attestations: true" in WORKFLOW


def test_environment_points_at_pypi_project():
    assert "name: pypi" in WORKFLOW
    assert "https://pypi.org/p/specadia" in WORKFLOW
