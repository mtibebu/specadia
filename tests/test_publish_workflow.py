"""Guard the PyPI trusted-publishing workflow against security regressions.

Reads ``.github/workflows/publish.yml`` and ``scripts/validate_release_tag.py``
as plain text (no PyYAML, no network) and asserts the contract invariants that
keep publishing safe:

  * the workflow runs for a published GitHub Release (never on push/PR) and, for
    recovery of a missed release event, on a guarded ``workflow_dispatch`` that
    requires a single ``tag`` input with no stale default;
  * the whole workflow holds least privilege (``contents: read``), and OIDC
    ``id-token: write`` appears only in the ``publish`` job;
  * every action is pinned to an immutable 40-char commit SHA;
  * the release tag is checked out only after being validated as an existing
    annotated ``vMAJOR.MINOR.PATCH`` tag that equals ``v`` + the
    ``pyproject.toml`` project version;
  * the tag is passed through env and quoted, never shell-interpolated;
  * publishing relies on OIDC trusted publishing, so no token is referenced.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
VALIDATOR = (ROOT / "scripts" / "validate_release_tag.py").read_text(encoding="utf-8")

REQUIRED_SHAS = [
    "11d5960a326750d5838078e36cf38b85af677262",  # actions/checkout v4.4.0
    "a26af69be951a213d495a4c3e4e4022e16d87065",  # actions/setup-python v5.6.0
    "ea165f8d65b6e75b540449e92b4886f43607fa02",  # actions/upload-artifact v4.6.2
    "d3f86a106a0bac45b974a628896c90dbdf5c8093",  # actions/download-artifact v4.3.0
    "dc37677b2e1c63e2034f94d8a5b11f265b73ba33",  # pypa/gh-action-pypi-publish v1.14.2
]


def _on_block() -> str:
    jobs_idx = WORKFLOW.index("jobs:")
    return WORKFLOW[:jobs_idx]


def test_trigger_is_release_published_and_guarded_dispatch():
    on_block = _on_block()
    assert "release" in on_block
    assert "published" in on_block
    assert "workflow_dispatch" in on_block
    for forbidden in ("pull_request_target", "push:", "pull_request",
                      "schedule"):
        assert forbidden not in on_block, f"forbidden trigger key present: {forbidden}"


def test_dispatch_requires_tag_input_no_default():
    on_block = _on_block()
    assert "tag:" in on_block
    assert "type: string" in on_block
    assert "required: true" in on_block
    assert "default:" not in on_block, "manual tag input must not carry a stale default"


def test_global_permissions_are_contents_read():
    on_block = _on_block()
    assert "permissions:" in on_block
    assert "contents: read" in on_block


def test_normalized_release_tag_for_concurrency():
    assert "github.event.release.tag_name || inputs.tag" in WORKFLOW
    assert "group: pypi-publish-" in WORKFLOW
    assert "cancel-in-progress: false" in WORKFLOW


def test_two_jobs_with_build_before_publish():
    assert "build:" in WORKFLOW
    assert "publish:" in WORKFLOW
    assert "needs: build" in WORKFLOW


def test_checkout_is_unauthenticated_and_fetches_tags():
    assert "persist-credentials: false" in WORKFLOW
    assert "fetch-depth: 0" in WORKFLOW
    assert "fetch-tags: true" in WORKFLOW


def test_tag_is_validated_before_build():
    assert "scripts/validate_release_tag.py" in WORKFLOW
    assert "RELEASE_TAG" in WORKFLOW
    assert '"$RELEASE_TAG"' in WORKFLOW


def test_validator_enforces_annotated_strict_tag():
    assert r"^v\d+\.\d+\.\d+$" in VALIDATOR
    assert "refs/tags" in VALIDATOR
    assert "cat-file" in VALIDATOR
    assert '"tag"' in VALIDATOR
    assert "rev-parse" in VALIDATOR
    assert "pyproject.toml" in VALIDATOR
    assert "^{{}}" in VALIDATOR


def test_all_actions_pinned_to_immutable_sha():
    for sha in REQUIRED_SHAS:
        assert sha in WORKFLOW, f"missing pinned SHA: {sha}"
    assert "@main" not in WORKFLOW
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
