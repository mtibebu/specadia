import pytest

from contracts.validation import validate_documents


def test_valid_documents_pass():
  report = validate_documents(
      "# Product SRS\n\n## Functional Requirements\n\n- FR-1: Create records safely.",
      "# Product Design\n\n## Architecture\n\nThe FR-1 service owns record creation.",
  )
  assert report.ok


def test_placeholders_and_missing_ids_fail():
  report = validate_documents(
      "# SRS\n\n## Requirements\n\n[TBD]",
      "# Design\n\n## Architecture\n\nTODO",
  )
  assert not report.ok
  assert {issue.code for issue in report.issues} >= {
      "missing-requirement-ids",
      "unresolved-placeholders",
  }


@pytest.mark.parametrize(
    "definition",
    [
        "- **FR-1**: Create records safely.",
        "- __FR-1__: Create records safely.",
        "- *FR-1*: Create records safely.",
        "- `FR-1`: Create records safely.",
    ],
)
def test_markdown_emphasized_requirement_definitions_pass(definition):
  report = validate_documents(
      f"# Product SRS\n\n## Functional Requirements\n\n{definition}",
      "# Product Design\n\n## Architecture\n\nThe FR-1 service owns record creation.",
  )

  assert report.ok


def test_markdown_references_are_not_counted_as_duplicate_definitions():
  report = validate_documents(
      """# Product SRS

## Functional Requirements

- **FR-1**: Create records safely.

The workflow implements **FR-1**.

| Requirement | Component |
| --- | --- |
| `FR-1` | Records service |
""",
      "# Product Design\n\n## Architecture\n\nThe FR-1 service owns record creation.",
  )

  assert report.ok


def test_bold_requirement_heading_without_delimiter_is_a_definition():
  report = validate_documents(
      "# Product SRS\n\n"
      "## Functional Requirements\n\n"
      "**FR-1**  \n"
      "- ID: FR-1\n"
      "- Description: Create records safely.\n",
      "# Product Design\n\n## Architecture\n\nThe FR-1 service owns record creation.",
  )

  assert report.ok


def test_design_must_preserve_all_srs_ids_without_replacements():
  report = validate_documents(
      "# SRS\n\n## Requirements\n\nFR-1: Create records.\nNFR-1: Respond quickly.",
      "# Design\n\n## Architecture\n\nREQ-1 uses a records service.",
  )

  codes = {issue.code for issue in report.issues}
  assert "missing-design-requirement-ids" in codes
  assert "unexpected-design-requirement-ids" in codes


def test_design_rejects_named_technology_absent_from_srs():
  report = validate_documents(
      "# SRS\n\n## Requirements\n\nFR-1: Process events.",
      "# Design\n\n## Architecture\n\nFR-1 uses Kafka and Kubernetes.",
  )

  assert "unsupported-named-technology" in {issue.code for issue in report.issues}


def test_compact_and_hyphenated_requirement_ids_are_equivalent():
  report = validate_documents(
      "# SRS\n\n## Requirements\n\nFR1: Process events.\nNFR1: Respond quickly.",
      "# Design\n\n## Architecture\n\nFR-1 processes events and NFR-1 bounds latency.",
  )

  assert report.ok


def test_labeled_requirement_fields_are_definitions():
  report = validate_documents(
      """# Product SRS

## Functional Requirements

**ID:** FR-01
**Description:** Process events.

## Non-Functional Requirements

ID: **NFR-01**
Description: Respond quickly.
""",
      """# Product Design

## Architecture

FR-1 processes events while NFR-1 bounds latency.
""",
  )

  assert report.ok


def test_zero_padded_srs_references_do_not_create_phantom_missing_ids():
  report = validate_documents(
      """# Product SRS

## Requirements

**ID:** FR-01
**Description:** Process events.
**Dependencies:** NFR-1.

**ID:** NFR-01
**Description:** Respond quickly.
""",
      """# Product Design

## Architecture

FR-01 processes events while NFR-01 bounds latency.
""",
  )

  assert report.ok
