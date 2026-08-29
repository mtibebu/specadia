from pathlib import Path

import pytest
from typer.testing import CliRunner

from specadia.contracts.cli import app
from specadia.contracts.generator import ContractGenerator
from specadia.contracts.models import Harness
from specadia.contracts.writer import write_bundles


SRS = """# Inventory Service

## Purpose

Track stock across warehouses.

## Functional Requirements

- FR-1: Users can receive stock.
- FR-2: Users can transfer stock between warehouses.

## Non-Functional Requirements

- NFR-1: Transfers must be auditable.

## Acceptance Criteria

- AC-1: A completed transfer updates both warehouses atomically.
"""

DESIGN = """# Inventory Service Design

## Architecture

Use a transactional service with a relational database.

## File Structure

Keep domain logic separate from transport adapters.
"""

runner = CliRunner()


def _write(path: Path, content: str) -> Path:
  path.write_text(content, encoding="utf-8")
  return path


def test_generates_traceable_codex_contract(tmp_path: Path):
  spec = _write(tmp_path / "srs.md", SRS)
  design = _write(tmp_path / "design.md", DESIGN)

  bundle = ContractGenerator().generate(
      spec_path=spec,
      design_path=design,
      harness=Harness.CODEX,
      output_dir=tmp_path / "out",
  )

  assert bundle.project_name == "Inventory Service"
  assert bundle.output_path.name == "AGENTS.md"
  assert "`FR-1`: Users can receive stock." in bundle.content
  assert "`NFR-1`: Transfers must be auditable." in bundle.content
  assert "transactional service" in bundle.content
  assert len(bundle.sources) == 2
  assert all(len(source.sha256) == 64 for source in bundle.sources)
  assert {source.path for source in bundle.sources} == {"srs.md", "design.md"}
  assert str(tmp_path) not in bundle.content


@pytest.mark.parametrize(
    ("harness", "filename"),
    [
        (Harness.CODEX, "AGENTS.md"),
        (Harness.CLAUDE, "CLAUDE.md"),
        (Harness.GENERIC, "AGENT_CONTRACT.md"),
    ],
)
def test_uses_harness_filename(tmp_path: Path, harness: Harness, filename: str):
  spec = _write(tmp_path / "srs.md", SRS)

  bundle = ContractGenerator().generate(spec, harness, tmp_path / "out")

  assert bundle.output_path.name == filename


def test_writer_refuses_overwrite_and_emits_manifest(tmp_path: Path):
  spec = _write(tmp_path / "srs.md", SRS)
  bundle = ContractGenerator().generate(spec, Harness.CODEX, tmp_path / "out")

  written = write_bundles([bundle])

  assert bundle.output_path in written
  manifest_path = tmp_path / "out" / "contract-manifest.json"
  assert manifest_path.is_file()
  manifest = manifest_path.read_text(encoding="utf-8")
  assert '"path": "AGENTS.md"' in manifest
  assert str(tmp_path) not in manifest
  with pytest.raises(FileExistsError):
    write_bundles([bundle])


def test_rejects_empty_spec(tmp_path: Path):
  spec = _write(tmp_path / "empty.md", "")

  with pytest.raises(ValueError, match="empty"):
    ContractGenerator().generate(spec, Harness.CODEX, tmp_path / "out")


def test_cli_generates_multiple_harnesses(tmp_path: Path):
  spec = _write(tmp_path / "srs.md", SRS)
  output = tmp_path / "contracts"

  result = runner.invoke(
      app,
      [
          "generate",
          str(spec),
          "--harness",
          "codex",
          "--harness",
          "generic",
          "--output-dir",
          str(output),
      ],
  )

  assert result.exit_code == 0, result.output
  assert (output / "AGENTS.md").is_file()
  assert (output / "AGENT_CONTRACT.md").is_file()
  assert (output / "contract-manifest.json").is_file()
