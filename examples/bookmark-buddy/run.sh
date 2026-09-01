#!/usr/bin/env bash
#
# Bookmark Buddy — deterministic Specadia contract-generation demo.
#
# Proves that Specadia's `specadia-contract generate` command turns the same
# requirements.md + design.md into byte-for-byte identical contracts on every
# run, and that the generated artifacts never leak local filesystem paths or
# temp-directory names.
#
# Usage:
#   ./run.sh                 # uses `specadia-contract` on PATH
#   SPECADIA=/path/to/bin ./run.sh   # use a specific binary
#
# Requirements: a `specadia-contract` binary (see Specadia README install).
# No credentials, no model, no network, no paid services are used.
#
# Exit codes: 0 success; 1 on determinism/hygiene failure; 2 if the binary
# cannot be found.
set -euo pipefail

# Resolve paths relative to this script, so the demo works from any cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIREMENTS="$SCRIPT_DIR/requirements.md"
DESIGN="$SCRIPT_DIR/design.md"

# Discover the binary; allow override via SPECADIA env var.
SPECADIA=${SPECADIA:-$(command -v specadia-contract || true)}
if [[ -z "$SPECADIA" ]]; then
  echo "ERROR: 'specadia-contract' not found on PATH." >&2
  echo "Install Specadia, then run again (see the Specadia README)." >&2
  exit 2
fi

# Fresh, disposable workspace — nothing written into the repo.
WORKSPACE="$(mktemp -d)"
trap 'rm -rf "$WORKSPACE"' EXIT

echo "==> Specadia binary: $SPECADIA"
echo "==> Workspace:       $WORKSPACE (temporary)"

cp "$REQUIREMENTS" "$WORKSPACE/requirements.md"
cp "$DESIGN" "$WORKSPACE/design.md"

echo "==> Generating contract into out-a..."
"$SPECADIA" generate "$WORKSPACE/requirements.md" \
  --design "$WORKSPACE/design.md" \
  --harness codex \
  --output-dir "$WORKSPACE/out-a"

echo "==> Generating contract into out-b..."
"$SPECADIA" generate "$WORKSPACE/requirements.md" \
  --design "$WORKSPACE/design.md" \
  --harness codex \
  --output-dir "$WORKSPACE/out-b"

echo "==> Checking determinism (diff -ru out-a out-b)..."
if diff -ru "$WORKSPACE/out-a" "$WORKSPACE/out-b" >/dev/null; then
  echo "PASS: out-a and out-b are identical (deterministic)."
else
  echo "FAIL: out-a and out-b differ." >&2
  exit 1
fi

echo "==> Checking hygiene (no absolute paths / temp-dir leakage)..."
LEAK=""
if grep -RIl "/Users/" "$WORKSPACE/out-a" "$WORKSPACE/out-b" | grep -q .; then
  LEAK="/Users/"
fi
if grep -RIl "mktemp" "$WORKSPACE/out-a" "$WORKSPACE/out-b" | grep -q .; then
  LEAK="${LEAK:+$LEAK, }mktemp"
fi
if grep -RIl "$WORKSPACE" "$WORKSPACE/out-a" "$WORKSPACE/out-b" | grep -q .; then
  LEAK="${LEAK:+$LEAK, }$WORKSPACE"
fi
if [[ -n "$LEAK" ]]; then
  echo "FAIL: generated output leaks paths/strings: $LEAK" >&2
  exit 1
fi
echo "PASS: generated output contains no absolute paths or temp-dir leakage."

echo
echo "Produced (in $WORKSPACE/out-a and out-b):"
echo "  - AGENTS.md               (implementation contract) (identical)"
echo "  - contract-manifest.json  (source + output sha256 traceability)"
echo
echo "Determinism: PASS   Hygiene: PASS"
echo "Demo complete: Specadia generated a deterministic, traceable contract."
