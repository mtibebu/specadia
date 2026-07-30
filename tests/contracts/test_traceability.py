from contracts.traceability import build_traceability


def test_traceability_flags_missing_design_mapping():
  report = build_traceability(
      {"FRs": ["FR-1: Create item"]},
      "# SRS\nFR-1: Create item",
      "# Design\nNo stable identifier",
      ["# Contract\nImplement FR-1"],
  )

  assert not report.ok
  assert report.records[0].design is False


def test_traceability_derives_positional_ids_for_plain_collector_requirements():
  report = build_traceability(
      {"FRs": ["Create item"], "NFRs": ["Respond within one second"]},
      "# SRS\nFR-1: Create item\nNFR-1: Respond within one second",
      "# Design\nFR-1 component\nNFR-1 latency control",
      ["# Contract\nImplement FR-1 and NFR-1"],
  )

  assert report.ok


def test_traceability_treats_compact_and_hyphenated_ids_as_equivalent():
  report = build_traceability(
      {"FRs": ["Create item"], "NFRs": ["Respond quickly"]},
      "# SRS\nFR1: Create item\nNFR1: Respond quickly",
      "# Design\nFR-1 component\nNFR-1 latency control",
      ["# Contract\nImplement FR1 and NFR1"],
  )

  assert report.ok


def test_traceability_treats_zero_padded_ids_as_equivalent():
  report = build_traceability(
      {"FRs": ["FR-01: Create item"], "NFRs": ["NFR-001: Respond quickly"]},
      "# SRS\nFR-1: Create item\nNFR-1: Respond quickly",
      "# Design\nFR001 component\nNFR-01 latency control",
      ["# Contract\nImplement FR-0001 and NFR1"],
  )

  assert report.ok
  assert [record.requirement_id for record in report.records] == ["FR-1", "NFR-1"]


def test_traceability_still_flags_a_truly_missing_zero_padded_id():
  report = build_traceability(
      {"FRs": ["FR-01: Create item", "FR-02: Delete item"]},
      "# SRS\nFR-1: Create item\nFR-2: Delete item",
      "# Design\nFR-1 component",
      ["# Contract\nImplement FR-1 and FR-2"],
  )

  missing = {record.requirement_id: record for record in report.records}
  assert not report.ok
  assert missing["FR-2"].design is False


def test_traceability_gate_rejects_incomplete_report():
  report = build_traceability(
      {"FRs": ["Create item"]},
      "# SRS\nFR-1: Create item",
      "# Design\nNo stable identifier",
      ["# Contract\nImplement FR-1"],
  )

  import pytest

  with pytest.raises(ValueError, match="traceability gate failed"):
    report.require_valid()
