"""Guard the self-contained public demo under examples/bookmark-buddy/.

Verifies the demo directory ships the required input/output artifacts, that the
deterministic replay script succeeds (when the CLI is available), that contract
generation is byte-for-byte deterministic, that generated output leaks no local
paths or temp-dir names, that the demo is discoverable from the root README, and
that the committed contract preserves requirement-ID traceability. Hermetic and
credential-free; no network, no model, no `from-intent` execution.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specadia.contracts.cli import app as contract_app


ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "examples" / "bookmark-buddy"

runner = CliRunner()

REQUIRED_FILES = [
    "intent.md",
    "requirements.md",
    "design.md",
    "contracts/AGENTS.md",
    "contracts/contract-manifest.json",
    "run.sh",
    "README.md",
    "assets/specadia-bookmark-buddy-demo.mp4",
    "assets/specadia-bookmark-buddy-demo-poster.png",
    "assets/specadia-bookmark-buddy-demo.vtt",
]


def _cli_on_path() -> bool:
    return shutil.which("specadia-contract") is not None


def test_demo_directory_and_required_files_exist():
    assert DEMO.is_dir(), "demo directory missing"
    for rel in REQUIRED_FILES:
        assert (DEMO / rel).is_file(), f"missing demo file: {rel}"


def test_run_sh_is_executable():
    path = DEMO / "run.sh"
    assert os.access(path, os.X_OK), "run.sh is not executable"


@pytest.mark.skipif(not _cli_on_path(), reason="specadia-contract not on PATH")
def test_run_sh_replays_successfully():
    result = subprocess.run(
        [str(DEMO / "run.sh")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "identical" in result.stdout
    assert "PASS" in result.stdout


def test_generation_is_deterministic(tmp_path: Path):
    out_a = tmp_path / "out-a"
    out_b = tmp_path / "out-b"
    for out in (out_a, out_b):
        res = runner.invoke(
            contract_app,
            [
                "generate",
                str(DEMO / "requirements.md"),
                "--design",
                str(DEMO / "design.md"),
                "--harness",
                "codex",
                "--output-dir",
                str(out),
            ],
        )
        assert res.exit_code == 0, res.output

    assert (out_a / "AGENTS.md").read_text() == (out_b / "AGENTS.md").read_text()
    assert (out_a / "contract-manifest.json").read_text() == (
        out_b / "contract-manifest.json"
    ).read_text()


def test_generated_output_has_no_absolute_paths_or_temp_leak(tmp_path: Path):
    out = tmp_path / "out"
    res = runner.invoke(
        contract_app,
        [
            "generate",
            str(DEMO / "requirements.md"),
            "--design",
            str(DEMO / "design.md"),
            "--harness",
            "codex",
            "--output-dir",
            str(out),
        ],
    )
    assert res.exit_code == 0, res.output

    text = (out / "AGENTS.md").read_text() + (out / "contract-manifest.json").read_text()
    assert "/Users/" not in text
    assert "mktemp" not in text
    assert str(tmp_path) not in text
    # No absolute filesystem path of any kind.
    assert "://" not in text


def test_demo_is_linked_from_root_readme():
    root = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "examples/bookmark-buddy/README.md" in root


def test_demo_readme_links_to_own_inputs():
    demo_readme = (DEMO / "README.md").read_text(encoding="utf-8")
    for rel in ("intent.md", "requirements.md", "design.md"):
        assert rel in demo_readme


def test_demo_readme_links_to_video_assets():
    demo_readme = (DEMO / "README.md").read_text(encoding="utf-8")
    for rel in (
        "assets/specadia-bookmark-buddy-demo.mp4",
        "assets/specadia-bookmark-buddy-demo-poster.png",
        "assets/specadia-bookmark-buddy-demo.vtt",
    ):
        assert rel in demo_readme

    root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "examples/bookmark-buddy/assets/specadia-bookmark-buddy-demo.mp4" in root_readme


def test_demo_media_assets_are_portable_and_canonical():
    video = DEMO / "assets" / "specadia-bookmark-buddy-demo.mp4"
    poster = DEMO / "assets" / "specadia-bookmark-buddy-demo-poster.png"
    captions = DEMO / "assets" / "specadia-bookmark-buddy-demo.vtt"

    assert b"ftyp" in video.read_bytes()[:32], "video must be an MP4 container"
    assert video.stat().st_size < 10 * 1024 * 1024, "keep the README video lightweight"
    assert poster.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    caption_text = captions.read_text(encoding="utf-8")
    assert caption_text.startswith("WEBVTT\n")
    assert "01:54.000 --> 02:00.000" in caption_text
    assert "PyPI" in caption_text
    assert "Pie P I" not in caption_text


def test_read_mas_is_mentioned_lightly_and_attribution_is_accurate():
    narrative_files = (
        DEMO / "README.md",
        DEMO / "assets" / "specadia-bookmark-buddy-demo.vtt",
    )
    for path in narrative_files:
        text = path.read_text(encoding="utf-8")
        assert text.lower().count("read-mas") == 1, f"unexpected READ-MAS count in {path}"
        assert "authored by a person" in text.lower()
        assert "Specadia with agents enabled" in text

    renderer = (ROOT / "scripts" / "render_bookmark_demo.sh").read_text(
        encoding="utf-8"
    )
    assert "C L I" not in renderer
    assert "command-line app" in renderer
    assert "produced with READ-MAS" in renderer
    assert "generated by Specadia with agents enabled" in renderer


def test_committed_contract_has_project_name_and_requirement_ids():
    agents = (DEMO / "contracts" / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.startswith("# Bookmark Buddy Agent Contract")
    for req_id in ("FR-1", "FR-2", "FR-3", "NFR-1", "NFR-2", "AC-1"):
        assert f"`{req_id}`:" in agents, f"missing traceability for {req_id}"

    manifest = json.loads(
        (DEMO / "contracts" / "contract-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["project_name"] == "Bookmark Buddy"


def test_demo_targets_two_minutes_and_no_stale_timing():
    captions = (DEMO / "assets" / "specadia-bookmark-buddy-demo.vtt").read_text(
        encoding="utf-8"
    )
    assert "02:00.000" in captions
    assert "75s" not in captions.lower()

    demo_readme = (DEMO / "README.md").read_text(encoding="utf-8")
    assert "two minutes" in demo_readme


def test_committed_manifest_uses_relative_paths():
    manifest = json.loads(
        (DEMO / "contracts" / "contract-manifest.json").read_text(encoding="utf-8")
    )
    for source in manifest["sources"]:
        assert source["path"] == Path(source["path"]).name, "source path must be a basename"
    for contract in manifest["contracts"]:
        assert contract["path"] == Path(contract["path"]).name, "contract path must be a basename"
