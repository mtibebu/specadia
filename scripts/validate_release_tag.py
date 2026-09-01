"""Validate a release tag before the PyPI publish workflow checks it out.

Called by ``.github/workflows/publish.yml`` with exactly one argument: the tag
to publish (``github.event.release.tag_name`` for a release event, or the
``workflow_dispatch`` ``tag`` input for a recovery).

Safety contract
---------------
The sole job of this script is to refuse anything that is not an existing,
annotated or lightweight ``vMAJOR.MINOR.PATCH`` tag whose commit's
``pyproject.toml`` version
matches the tag. It is run under ``persist-credentials: false`` and receives the
candidate tag as a positional argument (never shell-interpolated). It performs
no network access and only runs ``git`` subcommands with the tag passed as a
separate, already-syntax-checked argv element.

Exit status is 0 when the tag is valid and has been checked out, and non-zero
on any rejection.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

# Strict `vMAJOR.MINOR.PATCH`: rejects branches, SHAs, `refs/...`, prerelease
# (`-rc1`, `a1`, `+build`) and anything with shell metacharacters.
TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")


def is_valid_tag_syntax(tag: str) -> bool:
    """Return True when ``tag`` is a strictly formed ``vMAJOR.MINOR.PATCH``."""
    return bool(TAG_PATTERN.match(tag))


def run_git(*args: str) -> str:
    """Run a git subcommand and return stripped stdout; raise on failure."""
    proc = subprocess.run(
        ["git", *args], check=False, capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {args[0]} failed")
    return proc.stdout.strip()


def reject(message: str) -> int:
    print(f"::error::{message}", file=sys.stderr)
    return 1


def validate(tag: str) -> int:
    if not is_valid_tag_syntax(tag):
        return reject(
            f"tag {tag!r} must match vMAJOR.MINOR.PATCH "
            "(no branch/SHA/refs prefix, no prerelease or build suffix)"
        )

    ref = f"refs/tags/{tag}"

    probe = subprocess.run(
        ["git", "show-ref", "--verify", "--tags", ref],
        capture_output=True, text=True,
    )
    if probe.returncode != 0:
        return reject(f"tag {tag!r} does not exist under refs/tags")

    obj_type = run_git("cat-file", "-t", ref)
    if obj_type not in ("tag", "commit"):
        return reject(
            f"{ref!r} is a {obj_type!r}, not an annotated or lightweight tag"
        )

    # Check out the exact tag (detached). The value already matched the strict
    # pattern above, so it cannot act as a flag or shell metacharacter.
    subprocess.run(["git", "checkout", "--detach", ref], check=True)

    # Dereference the tag to its target commit: peels an annotated tag and
    # returns the commit directly for a lightweight tag.
    tag_commit = run_git("rev-parse", f"{ref}^{{commit}}")
    head = run_git("rev-parse", "HEAD")
    if tag_commit != head:
        return reject(
            f"tag {tag!r} dereferences to {tag_commit}, "
            f"not checked-out HEAD {head}"
        )

    pyproject = Path("pyproject.toml")
    project_version = tomllib.loads(pyproject.read_text(encoding="utf-8"))[
        "project"
    ]["version"]
    expected = f"v{project_version}"
    if tag != expected:
        return reject(
            f"tag {tag!r} does not match project version {expected!r}"
        )

    print(f"::notice::publishing annotated or lightweight tag {tag!r} -> {tag_commit}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <TAG>", file=sys.stderr)
        return 2
    try:
        return validate(argv[1])
    except Exception as exc:  # noqa: BLE001 - surface any git/toml failure
        return reject(f"validation failed: {exc}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
