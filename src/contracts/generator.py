"""Deterministic spec-to-agent contract generation."""

import hashlib
import re
from pathlib import Path

from .models import ContractBundle
from .models import ContractSection
from .models import Harness
from .models import SourceDocument

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_REQUIREMENT = re.compile(
    r"^\s*(?:[-*]\s*)?(?P<id>(?:FR|NFR|REQ|AC)[-_ ]?\d+)\s*[:.)-]\s*(?P<body>.+)$",
    re.IGNORECASE,
)
_SECTION_ALIASES = {
    "objective": ("overview", "purpose", "introduction", "scope"),
    "requirements": ("functional requirement", "use case", "feature"),
    "quality": ("non-functional", "quality attribute", "constraint", "security"),
    "architecture": ("architecture", "system design", "component design", "file structure"),
    "acceptance": ("acceptance", "validation", "verification", "test"),
}


class ContractGenerator:
  """Convert an SRS and optional design document into a coding contract."""

  def generate(
      self,
      spec_path: Path,
      harness: Harness,
      output_dir: Path,
      design_path: Path | None = None,
      project_name: str | None = None,
  ) -> ContractBundle:
    spec_path = self._validate_source(spec_path, "spec")
    design_path = self._validate_source(design_path, "design") if design_path else None
    project_name = project_name or self._project_name(spec_path)

    sources = [self._source("spec", spec_path)]
    documents = [spec_path.read_text(encoding="utf-8")]
    if design_path:
      sources.append(self._source("design", design_path))
      documents.append(design_path.read_text(encoding="utf-8"))

    sections = self._normalize_sections(documents)
    content = self._render(project_name, harness, sources, sections)
    return ContractBundle(
        project_name=project_name,
        harness=harness,
        output_path=output_dir / harness.filename,
        sources=sources,
        sections=sections,
        content=content,
    )

  @staticmethod
  def _validate_source(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
      raise ValueError(f"{label.capitalize()} file does not exist: {path}")
    if resolved.stat().st_size == 0:
      raise ValueError(f"{label.capitalize()} file is empty: {path}")
    return resolved

  @staticmethod
  def _source(kind: str, path: Path) -> SourceDocument:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return SourceDocument(kind=kind, path=str(path), sha256=digest)

  @staticmethod
  def _project_name(spec_path: Path) -> str:
    for line in spec_path.read_text(encoding="utf-8").splitlines():
      match = _HEADING.match(line)
      if match and len(match.group(1)) == 1:
        return match.group(2).strip()
    return spec_path.stem.replace("_", " ").replace("-", " ").title()

  def _normalize_sections(self, documents: list[str]) -> list[ContractSection]:
    parsed = [self._parse_markdown(document) for document in documents]
    normalized: list[ContractSection] = []
    for target, aliases in _SECTION_ALIASES.items():
      content = self._matching_content(parsed, aliases)
      if content:
        normalized.append(ContractSection(title=target, content=content))

    requirements = self._extract_requirements(documents)
    if requirements:
      replacement = "\n".join(f"- `{req_id}`: {body}" for req_id, body in requirements)
      normalized = [section for section in normalized if section.title != "requirements"]
      normalized.insert(1 if normalized else 0, ContractSection(title="requirements", content=replacement))

    if not normalized:
      normalized.append(
          ContractSection(title="requirements", content=self._trim("\n\n".join(documents)))
      )
    return normalized

  @staticmethod
  def _parse_markdown(document: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"document": []}
    current = "document"
    for line in document.splitlines():
      heading = _HEADING.match(line)
      if heading:
        current = heading.group(2).strip().lower()
        sections.setdefault(current, [])
      else:
        sections[current].append(line)
    return sections

  @staticmethod
  def _matching_content(
      documents: list[dict[str, list[str]]], aliases: tuple[str, ...]
  ) -> str:
    chunks: list[str] = []
    for document in documents:
      for heading, lines in document.items():
        if any(alias in heading for alias in aliases):
          content = ContractGenerator._trim("\n".join(lines))
          if content and content not in chunks:
            chunks.append(content)
    return "\n\n".join(chunks)

  @staticmethod
  def _extract_requirements(documents: list[str]) -> list[tuple[str, str]]:
    requirements: list[tuple[str, str]] = []
    seen: set[str] = set()
    for document in documents:
      for line in document.splitlines():
        match = _REQUIREMENT.match(line)
        if not match:
          continue
        req_id = re.sub(r"[-_ ]", "-", match.group("id").upper())
        if req_id not in seen:
          requirements.append((req_id, match.group("body").strip()))
          seen.add(req_id)
    return requirements

  @staticmethod
  def _trim(content: str, limit: int = 12_000) -> str:
    content = content.strip()
    if len(content) <= limit:
      return content
    return f"{content[:limit].rstrip()}\n\n[Source section truncated by generator]"

  def _render(
      self,
      project_name: str,
      harness: Harness,
      sources: list[SourceDocument],
      sections: list[ContractSection],
  ) -> str:
    preamble = {
        Harness.CODEX: (
            "These instructions define the implementation contract for Codex and its subagents."
        ),
        Harness.CLAUDE: (
            "These instructions define the implementation contract for Claude Code and its agents."
        ),
        Harness.GENERIC: "This document is the implementation contract for a coding agent.",
    }[harness]
    rendered_sections = "\n\n".join(
        f"## {section.title.replace('_', ' ').title()}\n\n{section.content}"
        for section in sections
    )
    source_lines = "\n".join(
        f"- `{source.kind}`: `{source.path}` (SHA-256 `{source.sha256}`)"
        for source in sources
    )
    return (
        f"# {project_name} Agent Contract\n\n"
        f"{preamble}\n\n"
        "## Authority\n\n"
        "The source documents listed below are the product source of truth. Preserve explicit "
        "requirement identifiers in code, tests, and review notes. When sources conflict, stop "
        "and report the conflict instead of silently choosing an interpretation.\n\n"
        f"{source_lines}\n\n"
        f"{rendered_sections}\n\n"
        "## Delivery Rules\n\n"
        "- Keep changes within the scope above and preserve unrelated user changes.\n"
        "- Prefer existing project patterns and dependencies before adding abstractions.\n"
        "- Add tests for changed behavior and run the narrowest relevant verification suite.\n"
        "- Map every implemented requirement ID to verification evidence in the final report.\n"
        "- Report assumptions, unresolved ambiguities, skipped tests, and residual risks.\n"
        "- Do not claim completion while required acceptance criteria are unverified.\n"
    )
