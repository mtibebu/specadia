"""Requirement traceability across generated artifacts."""

import json
import re
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

from contracts.requirement_ids import normalize_requirement_id

_REQ = re.compile(
    r"(?<![A-Za-z0-9])((?:FR|NFR|REQ|AC)[-_ ]?\d+)(?![A-Za-z0-9])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TraceRecord:
  requirement_id: str
  collector: bool
  srs: bool
  design: bool
  contract: bool

  @property
  def complete(self) -> bool:
    return self.collector and self.srs and self.design and self.contract


@dataclass(frozen=True)
class TraceabilityReport:
  records: list[TraceRecord]

  @property
  def ok(self) -> bool:
    return bool(self.records) and all(record.complete for record in self.records)

  def to_dict(self) -> dict[str, object]:
    return {"ok": self.ok, "records": [asdict(record) for record in self.records]}

  def require_valid(self) -> None:
    if not self.ok:
      missing = [f"{record.requirement_id} ({', '.join(
              name
              for name in ('collector', 'srs', 'design', 'contract')
              if not getattr(record, name)
          )})" for record in self.records if not record.complete]
      detail = "; ".join(missing) if missing else "no stable requirement IDs found"
      raise ValueError(f"Generated artifact traceability gate failed: {detail}")

  def to_markdown(self) -> str:
    lines = [
        "# Traceability Report",
        "",
        "| Requirement | Collector | SRS | Design | Contract | Complete |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for record in self.records:
      values = [
          "yes" if value else "no"
          for value in (
              record.collector,
              record.srs,
              record.design,
              record.contract,
              record.complete,
          )
      ]
      lines.append(f"| {record.requirement_id} | {' | '.join(values)} |")
    return "\n".join(lines) + "\n"


def build_traceability(
    collector: dict[str, object],
    srs: str,
    design: str,
    contracts: list[str],
) -> TraceabilityReport:
  """Map stable IDs across Collector, SRS, design, and contracts."""
  collector_ids = _collector_ids(collector)
  ids = sorted(collector_ids | _ids(srs))
  contract_text = "\n".join(contracts)
  return TraceabilityReport([
      TraceRecord(
          requirement_id=requirement_id,
          collector=requirement_id in collector_ids,
          srs=requirement_id in _ids(srs),
          design=requirement_id in _ids(design),
          contract=requirement_id in _ids(contract_text),
      )
      for requirement_id in ids
  ])


def write_traceability(report: TraceabilityReport, output_dir: Path) -> list[Path]:
  json_path = output_dir / "traceability.json"
  markdown_path = output_dir / "traceability.md"
  json_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
  markdown_path.write_text(report.to_markdown(), encoding="utf-8")
  return [json_path, markdown_path]


def _ids(content: str) -> set[str]:
  return {normalize_requirement_id(value) for value in _REQ.findall(content)}


def _collector_ids(collector: dict[str, object]) -> set[str]:
  """Derive stable positional IDs when Collector values are still plain strings."""
  explicit = _ids(json.dumps(collector, default=str))
  derived: set[str] = set()
  for key, prefix in (("FRs", "FR"), ("NFRs", "NFR")):
    values = collector.get(key)
    if not isinstance(values, list):
      continue
    for index, value in enumerate(values, 1):
      value_ids = _ids(str(value))
      derived.update(value_ids or {f"{prefix}-{index}"})
  return explicit | derived
