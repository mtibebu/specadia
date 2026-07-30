"""Data models for generated coding-agent contracts."""

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field


class Harness(StrEnum):
  """Supported coding harnesses."""

  CODEX = "codex"
  CLAUDE = "claude"
  GENERIC = "generic"

  @property
  def filename(self) -> str:
    return {
        Harness.CODEX: "AGENTS.md",
        Harness.CLAUDE: "CLAUDE.md",
        Harness.GENERIC: "AGENT_CONTRACT.md",
    }[self]


class SourceDocument(BaseModel):
  """A source document used to build a contract."""

  kind: str
  path: str
  sha256: str


class ContractSection(BaseModel):
  """Normalized content extracted from a source specification."""

  title: str
  content: str


class ContractBundle(BaseModel):
  """Generated contract content and its traceability metadata."""

  schema_version: str = "1.0"
  project_name: str
  harness: Harness
  output_path: Path
  sources: list[SourceDocument] = Field(default_factory=list)
  sections: list[ContractSection] = Field(default_factory=list)
  content: str
