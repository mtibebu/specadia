"""Deterministic quality checks for generated SRS and design documents."""

import re
from dataclasses import dataclass

from .requirement_ids import normalize_requirement_id

_REQ_ID = re.compile(
    r"(?<![A-Za-z0-9])(?:FR|NFR|REQ|AC)[-_ ]?\d+(?![A-Za-z0-9])",
    re.IGNORECASE,
)
_DEFINITION = re.compile(
    r"^\s*(?:[-*+]\s*)?"
    r"(?P<markup>\*\*|__|\*|_|`)?"
    r"(?P<id>(?:FR|NFR|REQ|AC)[-_ ]?\d+)"
    r"(?(markup)(?P=markup)[ \t]*(?:[:.)-]|\Z)|[ \t]*[:.)-])",
    re.IGNORECASE,
)
_LABELED_DEFINITION = re.compile(
    r"^\s*(?:[-*+]\s*)?"
    r"(?:\*\*|__|\*|_|`)?ID[ \t]*:[ \t]*(?:\*\*|__|\*|_|`)?[ \t]*"
    r"(?P<id>(?:FR|NFR|REQ|AC)[-_ ]?\d+)",
    re.IGNORECASE,
)
_PLACEHOLDER = re.compile(
    r"\[(?:todo|tbd|project name|insert|placeholder)[^\]]*\]|\b(?:TODO|TBD)\b",
    re.IGNORECASE,
)
_NAMED_TECHNOLOGY = re.compile(
    r"\b(?:"
    r"FastAPI|Kafka|RabbitMQ|Kubernetes|Terraform|Helm|Pinecone|Milvus|"
    r"PostgreSQL|Redis|GraphQL|gRPC|Avro|ITAR|IAEA|COPUOS|"
    r"Prometheus|Grafana|AES-?\d*|TLS(?:\s+\d(?:\.\d)?)?|OIDC|JWT"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class QualityIssue:
  code: str
  message: str
  document: str


@dataclass(frozen=True)
class QualityReport:
  issues: list[QualityIssue]

  @property
  def ok(self) -> bool:
    return not self.issues

  def require_valid(self) -> None:
    if self.issues:
      details = "; ".join(
          f"{issue.document}:{issue.code}: {issue.message}" for issue in self.issues
      )
      raise ValueError(f"Generated document quality gate failed: {details}")


def validate_documents(srs: str, design: str) -> QualityReport:
  """Validate release-critical document structure and requirement identity."""
  issues: list[QualityIssue] = []
  _nonempty("srs", srs, issues)
  _nonempty("design", design, issues)
  srs_ids: set[str] = set()
  if srs.strip():
    _heading("srs", srs, ("requirement", "functional"), "requirements-section", issues)
    direct_ids = [
        normalize_requirement_id(match.group("id"))
        for line in srs.splitlines()
        if (match := _DEFINITION.match(line))
    ]
    labeled_ids = [
        normalize_requirement_id(match.group("id"))
        for line in srs.splitlines()
        if (match := _LABELED_DEFINITION.match(line))
    ]
    # A field-style ``ID: FR-1`` directly beneath an ``FR-1`` heading is
    # metadata for that same definition, not a second definition.
    ids = direct_ids + [
        requirement_id for requirement_id in labeled_ids if requirement_id not in direct_ids
    ]
    if not ids:
      issues.append(
          QualityIssue("missing-requirement-ids", "No stable requirement IDs found", "srs")
      )
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
      issues.append(
          QualityIssue(
              "duplicate-requirement-ids",
              f"Requirement IDs occur more than once: {', '.join(duplicates)}",
              "srs",
          )
      )
    srs_ids = {normalize_requirement_id(value) for value in _REQ_ID.findall(srs)}
  if design.strip():
    _heading("design", design, ("architecture", "design"), "architecture-section", issues)
    design_ids = {normalize_requirement_id(value) for value in _REQ_ID.findall(design)}
    missing = sorted(srs_ids - design_ids)
    if missing:
      issues.append(
          QualityIssue(
              "missing-design-requirement-ids",
              f"Design omits stable requirement IDs: {', '.join(missing)}",
              "design",
          )
      )
    unexpected = sorted(design_ids - srs_ids)
    if unexpected:
      issues.append(
          QualityIssue(
              "unexpected-design-requirement-ids",
              f"Design introduces requirement IDs absent from the SRS: {', '.join(unexpected)}",
              "design",
          )
      )
    unsupported = sorted(
        {
            match.group(0)
            for match in _NAMED_TECHNOLOGY.finditer(design)
            if not re.search(rf"\b{re.escape(match.group(0))}\b", srs, re.IGNORECASE)
        },
        key=str.casefold,
    )
    if unsupported:
      issues.append(
          QualityIssue(
              "unsupported-named-technology",
              "Design introduces named technologies or regulations absent from the SRS: "
              + ", ".join(unsupported),
              "design",
          )
      )
  for name, content in (("srs", srs), ("design", design)):
    placeholders = sorted(set(match.group(0) for match in _PLACEHOLDER.finditer(content)))
    if placeholders:
      issues.append(
          QualityIssue(
              "unresolved-placeholders",
              f"Unresolved placeholders: {', '.join(placeholders)}",
              name,
          )
      )
  return QualityReport(issues)


def _nonempty(name: str, content: str, issues: list[QualityIssue]) -> None:
  if len(content.strip()) < 40:
    issues.append(QualityIssue("empty-or-short", "Document is empty or too short", name))


def _heading(
    name: str,
    content: str,
    terms: tuple[str, ...],
    code: str,
    issues: list[QualityIssue],
) -> None:
  headings = [
      line.lstrip("#").strip().lower() for line in content.splitlines() if line.startswith("#")
  ]
  if not any(any(term in heading for term in terms) for heading in headings):
    issues.append(QualityIssue(code, f"Missing heading containing one of: {terms}", name))
