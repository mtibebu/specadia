"""Fail when a wheel exposes packages outside Specadia's public allowlist."""

from __future__ import annotations

import ast
import sys
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


FORBIDDEN_TOP_LEVEL_IMPORTS = {
    "agents",
    "contracts",
    "design",
    "diagnostics",
    "main",
    "orchestrator",
    "prompt_templates",
    "rag",
    "requirement",
    "single",
    "tools",
    "utils",
}


def _top_level_imports(source: str, filename: str) -> set[str]:
  tree = ast.parse(source, filename=filename)
  imported: set[str] = set()
  for node in ast.walk(tree):
    if isinstance(node, ast.Import):
      imported.update(alias.name.partition(".")[0] for alias in node.names)
    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
      imported.add(node.module.partition(".")[0])
  return imported


def audit(wheel: Path) -> list[str]:
  errors: list[str] = []
  with ZipFile(wheel) as archive:
    names = archive.namelist()
    metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
    metadata = archive.read(metadata_name).decode("utf-8")
    for name in names:
      if not name.startswith("specadia/") or not name.endswith(".py"):
        continue
      imported = _top_level_imports(archive.read(name).decode("utf-8"), name)
      forbidden = sorted(imported & FORBIDDEN_TOP_LEVEL_IMPORTS)
      if forbidden:
        errors.append(f"{name} imports forbidden top-level package(s): {', '.join(forbidden)}")
  for name in names:
    path = PurePosixPath(name)
    top = path.parts[0]
    if top == "specadia" or top.endswith(".dist-info"):
      continue
    errors.append(f"unexpected wheel entry: {name}")
  if not any(name == "specadia/cli.py" for name in names):
    errors.append("missing specadia/cli.py")
  if any("google" in name.lower() for name in names):
    errors.append("wheel unexpectedly contains Google-specific code")
  unconditional = [
      line
      for line in metadata.splitlines()
      if line.lower().startswith("requires-dist:")
      and ("google-adk" in line.lower() or "google-genai" in line.lower())
      and "extra ==" not in line.lower()
  ]
  if unconditional:
    errors.append("core metadata unconditionally requires Google agent dependencies")
  normalized_metadata = metadata.lower()
  required_extra_dependencies = {
      "aiohttp": ('extra == "agents"', 'extra == "full"'),
      "numpy": ('extra == "rag"', 'extra == "full"'),
  }
  for dependency, markers in required_extra_dependencies.items():
    matching = [
        line.lower()
        for line in metadata.splitlines()
        if line.lower().startswith(f"requires-dist: {dependency}")
    ]
    for marker in markers:
      if not any(marker in line for line in matching):
        errors.append(f"metadata is missing {dependency} for {marker}")
  if "license-expression: apache-2.0" not in normalized_metadata:
    errors.append("metadata is missing the Apache-2.0 license expression")
  return errors


def main(argv: list[str]) -> int:
  if len(argv) != 2:
    print("usage: audit_distribution.py WHEEL", file=sys.stderr)
    return 2
  wheel = Path(argv[1])
  errors = audit(wheel)
  if errors:
    print("\n".join(errors), file=sys.stderr)
    return 1
  print(f"audited {wheel}: specadia namespace only")
  return 0


if __name__ == "__main__":
  raise SystemExit(main(sys.argv))
