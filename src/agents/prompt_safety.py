"""Compatibility re-export of the contract pipeline's trust-boundary helpers."""

from specadia._contracts.prompt_safety import (  # noqa: F401
    require_bounded_strings,
    untrusted_json,
    untrusted_text,
)

__all__ = ["require_bounded_strings", "untrusted_json", "untrusted_text"]
