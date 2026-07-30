"""Write generated contracts and their manifest."""

import json
from pathlib import Path

from .models import ContractBundle


def write_bundles(bundles: list[ContractBundle], force: bool = False) -> list[Path]:
  """Write contracts and a manifest, refusing accidental overwrites."""
  if not bundles:
    raise ValueError("At least one contract bundle is required")

  output_dir = bundles[0].output_path.parent
  paths = [bundle.output_path for bundle in bundles]
  manifest_path = output_dir / "contract-manifest.json"
  existing = [path for path in [*paths, manifest_path] if path.exists()]
  if existing and not force:
    names = ", ".join(str(path) for path in existing)
    raise FileExistsError(f"Refusing to overwrite existing contract files: {names}")

  output_dir.mkdir(parents=True, exist_ok=True)
  for bundle in bundles:
    bundle.output_path.write_text(bundle.content, encoding="utf-8")

  manifest = {
      "schema_version": "1.0",
      "project_name": bundles[0].project_name,
      "sources": [source.model_dump() for source in bundles[0].sources],
      "contracts": [
          {
              "harness": bundle.harness.value,
              "path": str(bundle.output_path),
              "sha256": _sha256(bundle.content),
          }
          for bundle in bundles
      ],
  }
  manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
  return [*paths, manifest_path]


def _sha256(content: str) -> str:
  import hashlib

  return hashlib.sha256(content.encode("utf-8")).hexdigest()
