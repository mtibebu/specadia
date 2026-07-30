"""Canonical handling of stable requirement identifiers."""

import re


def normalize_requirement_id(value: str) -> str:
  """Normalize equivalent spellings such as ``FR-01`` and ``FR1``."""
  match = re.fullmatch(
      r"\s*(FR|NFR|REQ|AC)[-_ ]?(\d+)\s*",
      value,
      re.IGNORECASE,
  )
  if not match:
    return value.upper()
  number = match.group(2).lstrip("0") or "0"
  return f"{match.group(1).upper()}-{number}"
