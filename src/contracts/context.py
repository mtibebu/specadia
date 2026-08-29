"""Bounded, safe repository context for design generation."""

import json
from dataclasses import dataclass
from pathlib import Path
import re

_MANIFESTS = {
    "pyproject.toml": "Python",
    "package.json": "JavaScript/TypeScript",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
    "pom.xml": "Java",
    "build.gradle": "Java/Kotlin",
}
_CONVENTION_FILES = ("AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md")
_EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "runs",
    "__pycache__",
}
_SENSITIVE_NAME_RE = re.compile(
    r"(?:^|[._-])(?:env|secret|secrets|credential|credentials|token|tokens|password|"
    r"private[-_]?key|id[-_]?rsa|id[-_]?ed25519)(?:$|[._-])",
    re.IGNORECASE,
)
_SENSITIVE_SUFFIXES = {".key", ".keystore", ".p12", ".pem", ".pfx"}


def _is_sensitive_path(path: Path) -> bool:
  """Return whether a relative path is likely to disclose credential material."""
  return any(
      _SENSITIVE_NAME_RE.search(part) or Path(part).suffix.lower() in _SENSITIVE_SUFFIXES
      for part in path.parts
  )


@dataclass(frozen=True)
class RepositoryContext:
  root: str
  languages: list[str]
  manifests: list[str]
  commands: list[str]
  structure: list[str]
  conventions: dict[str, str]

  def to_prompt(self) -> str:
    payload = {
        "root": self.root,
        "languages": self.languages,
        "manifests": self.manifests,
        "commands": self.commands,
        "structure": self.structure,
        "conventions": self.conventions,
    }
    return "Existing repository context (treat as constraints):\n" + json.dumps(payload, indent=2)


def inspect_repository(
    root: Path,
    *,
    max_files: int = 200,
    max_convention_chars: int = 12_000,
) -> RepositoryContext:
  """Inspect bounded metadata without disclosing local paths or file contents."""
  resolved = root.expanduser().resolve()
  if not resolved.is_dir():
    raise ValueError(f"Repository directory does not exist: {root}")

  manifests = [name for name in _MANIFESTS if (resolved / name).is_file()]
  languages = sorted({_MANIFESTS[name] for name in manifests})
  paths: list[str] = []
  for path in sorted(resolved.rglob("*")):
    relative = path.relative_to(resolved)
    if any(part in _EXCLUDED_PARTS for part in relative.parts):
      continue
    if path.is_file() and not _is_sensitive_path(relative):
      paths.append(str(relative))
    if len(paths) >= max_files:
      break

  conventions: dict[str, str] = {}
  remaining = max_convention_chars
  for name in _CONVENTION_FILES:
    path = resolved / name
    if path.is_file() and remaining > 0:
      marker = "[present; content omitted from repository context]"
      conventions[name] = marker
      remaining -= len(marker)

  return RepositoryContext(
      root=".",
      languages=languages,
      manifests=manifests,
      commands=_commands(resolved),
      structure=paths,
      conventions=conventions,
  )


def _commands(root: Path) -> list[str]:
  commands: list[str] = []
  pyproject = root / "pyproject.toml"
  if pyproject.is_file():
    commands.extend(["python -m pytest", "python -m pip install -e ."])
  package = root / "package.json"
  if package.is_file():
    try:
      scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {})
      commands.extend(f"npm run {name}" for name in sorted(scripts))
    except (OSError, json.JSONDecodeError):
      pass
  if (root / "Makefile").is_file():
    commands.append("make")
  return commands
