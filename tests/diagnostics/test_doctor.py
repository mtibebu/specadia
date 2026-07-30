import sys
from pathlib import Path

from diagnostics.doctor import run_checks


def test_openai_requires_key(tmp_path: Path):
  report = run_checks(
      "openai/gpt-5",
      tmp_path,
      check_network=False,
      environ={},
  )

  assert report.ok is False
  assert any("OPENAI_API_KEY" in check.message for check in report.checks)


def test_openai_passes_with_key(tmp_path: Path):
  report = run_checks(
      "openai/gpt-5",
      tmp_path,
      check_network=False,
      environ={"OPENAI_API_KEY": "test"},
  )

  expected = sys.version_info >= (3, 12)
  assert report.ok is expected


def test_ollama_network_can_be_skipped(tmp_path: Path):
  report = run_checks(
      "ollama/qwen",
      tmp_path,
      check_network=False,
      environ={},
  )

  assert any(check.name == "ollama" and check.ok for check in report.checks)


def test_lm_studio_network_can_be_skipped(tmp_path: Path):
  report = run_checks(
      "lm_studio/qwen",
      tmp_path,
      check_network=False,
      environ={},
  )

  assert report.ok is (sys.version_info >= (3, 12))
  assert any(check.name == "lm-studio" and check.ok for check in report.checks)
  assert any(
      check.name == "provider-credentials" and check.ok for check in report.checks
  )


def test_generic_openai_compatible_provider_requires_endpoint(tmp_path: Path):
  report = run_checks(
      "openai_compatible/custom",
      tmp_path,
      check_network=False,
      environ={},
  )

  assert report.ok is False
  assert any(
      "OPENAI_COMPATIBLE_API_BASE is required" in check.message
      for check in report.checks
  )


def test_generic_openai_compatible_provider_accepts_endpoint(tmp_path: Path):
  report = run_checks(
      "openai_compatible/custom",
      tmp_path,
      check_network=False,
      environ={"OPENAI_COMPATIBLE_API_BASE": "http://localhost:9000/v1"},
  )

  assert report.ok is (sys.version_info >= (3, 12))
  assert any(
      check.name == "openai-compatible" and check.ok for check in report.checks
  )
