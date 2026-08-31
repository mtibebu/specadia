"""Verify `.python-version` pins a portable minor, not an exact patch.

The `.python-version` file must select a supported minor (3.12 or 3.13) so
pyenv/asdf/uv resolve any installed patch of that minor. Pinning an exact patch
(e.g. a full ``major.minor.micro`` string) causes launchers to hard-fail on
machines with a different patch of the same supported minor.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A full ``<major>.<minor>.<micro>`` version, e.g. ``3.13.x``.
_FULL_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Forward-looking specifiers that leave room for any patch within a minor.
_OPEN_ENDED = (">=", "<=", ">", "<")


def _parse_specifiers(requires_python: str) -> list[tuple[str, tuple[int, ...]]]:
    """Parse a ``requires-python`` specifier list into (op, version) pairs.

    Dependency-free; handles ``>=``, ``<=``, ``>``, ``<``, ``==``, and ``~=``
    operators separated by commas (including optional whitespace).
    """
    parsed: list[tuple[str, tuple[int, ...]]] = []
    for chunk in requires_python.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        match = re.match(r"^(>=|<=|==|~=|>|<)\s*(\d+(?:\.\d+)*)$", chunk)
        if not match:
            raise ValueError(f"Unsupported requires-python specifier: {chunk!r}")
        op = match.group(1)
        version = tuple(int(part) for part in match.group(2).split("."))
        parsed.append((op, version))
    return parsed


def _load_requires_python() -> str:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)["project"]["requires-python"]


def _satisfies_specifier(value: tuple[int, ...], op: str, bound: tuple[int, ...]) -> bool:
    if op == ">=":
        return value >= bound
    if op == "<=":
        return value <= bound
    if op == ">":
        return value > bound
    if op == "<":
        return value < bound
    if op == "==":
        return value == bound
    if op == "~=":
        # PEP 440 compatible release: `~=3.12` means `>=3.12, ==3.*`.
        release_len = len(bound) - 1
        return value >= bound and value[:release_len] == bound[:release_len]
    return False


def _python_version_content() -> str:
    path = ROOT / ".python-version"
    assert path.is_file(), ".python-version is missing"
    content = path.read_text(encoding="utf-8").strip()
    assert content, ".python-version is empty"
    return content


def test_python_version_exists_and_is_non_empty():
    assert _python_version_content()


def test_python_version_is_a_supported_minor():
    value = _python_version_content()
    assert value in {"3.12", "3.13"}, (
        f".python-version must be a supported minor (3.12 or 3.13), got {value!r}"
    )


def test_python_version_is_not_an_exact_patch():
    value = _python_version_content()
    assert not _FULL_VERSION_RE.match(value), (
        f".python-version must not pin an exact patch, got {value!r}"
    )


def test_python_version_minor_satisfies_requires_python():
    value = _python_version_content()
    parts = tuple(int(part) for part in value.split("."))
    specifiers = _parse_specifiers(_load_requires_python())
    assert specifiers, "requires-python produced no specifiers"
    for op, bound in specifiers:
        assert _satisfies_specifier(parts, op, bound), (
            f".python-version {value!r} does not satisfy {op}{'.'.join(map(str, bound))}"
        )


def test_requires_python_lower_bound_allows_minor_collapse():
    # The chosen minor must not need a micro part to satisfy the range, i.e. the
    # range is minor-granular and any patch of the chosen minor is acceptable.
    specifiers = _parse_specifiers(_load_requires_python())
    assert all(op in _OPEN_ENDED for op, _ in specifiers), (
        "requires-python must be minor-granular (no == or ~= pinning)"
    )
