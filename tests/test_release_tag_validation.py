"""Unit + git-backed tests for scripts/validate_release_tag.py.

The publish workflow must only ever check out an existing annotated release
tag whose commit's pyproject.toml version matches. These tests exercise the
pure syntax gate directly and the full validation path against a throwaway
local git repository (no network).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate_release_tag.py"

sys.path.insert(0, str(ROOT / "scripts"))

import validate_release_tag as vrt  # noqa: E402


@pytest.mark.parametrize(
    ("tag", "ok"),
    [
        ("v0.2.7", True),
        ("v1.0.0", True),
        ("v12.34.56", True),
        ("v0.2", False),
        ("0.2.7", False),
        ("v0.2.7.1", False),
        ("v0.2.7-rc1", False),
        ("v0.2.7rc1", False),
        ("v0.2.7+build", False),
        ("main", False),
        ("refs/tags/v0.2.7", False),
        ("abc123def", False),
        ("v0.2.7 ", False),
        ("v0.2.7;rm", False),
        ("", False),
    ],
)
def test_tag_syntax_gate(tag, ok):
    assert vrt.is_valid_tag_syntax(tag) is ok


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _make_repo(tmp_path: Path, version: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "specadia"\nversion = "%s"\n' % version,
        encoding="utf-8",
    )
    _git(repo, "add", "pyproject.toml")
    _git(repo, "commit", "-qm", "init")
    return repo


def _annotated_tag(repo: Path, tag: str) -> None:
    _git(repo, "tag", "-a", tag, "-m", tag)


def _lightweight_tag(repo: Path, tag: str) -> None:
    _git(repo, "tag", tag)


def _run_script(repo: Path, tag: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), tag],
        cwd=repo, capture_output=True, text=True,
    )


def test_valid_annotated_tag_passes(tmp_path):
    repo = _make_repo(tmp_path, "0.2.7")
    _annotated_tag(repo, "v0.2.7")
    result = _run_script(repo, "v0.2.7")
    assert result.returncode == 0, result.stderr


def test_lightweight_tag_rejected(tmp_path):
    repo = _make_repo(tmp_path, "0.2.7")
    _lightweight_tag(repo, "v0.2.7")
    result = _run_script(repo, "v0.2.7")
    assert result.returncode != 0
    assert "annotated tag" in result.stderr


def test_missing_tag_rejected(tmp_path):
    repo = _make_repo(tmp_path, "0.2.7")
    result = _run_script(repo, "v9.9.9")
    assert result.returncode != 0
    assert "does not exist" in result.stderr


def test_version_mismatch_rejected(tmp_path):
    repo = _make_repo(tmp_path, "0.2.8")
    _annotated_tag(repo, "v0.2.7")
    result = _run_script(repo, "v0.2.7")
    assert result.returncode != 0
    assert "does not match project version" in result.stderr


def test_malformed_tag_rejected_without_git(tmp_path):
    repo = _make_repo(tmp_path, "0.2.7")
    result = _run_script(repo, "v0.2.7;touch pwned")
    assert result.returncode != 0
    assert "must match" in result.stderr
    assert not (repo / "pwned").exists()
