---
description: Convert approved requirements and design artifacts into a Claude implementation contract
argument-hint: <path-to-requirements> [path-to-design]
allowed-tools: Bash
---

Create a Claude implementation contract from these approved artifacts:

$ARGUMENTS

1. Verify `specadia` is available.
2. Treat the first path as requirements and the optional second path as design. If no paths were
   provided, choose a generation path:
   - Approved SRS/design artifacts: use the canonical `specadia-contract generate`.
   - Only raw intent and a full agent-capable install: use `specadia-contract from-intent`
     (human-in-the-loop intent-to-SRS/design-to-contract; requires `specadia[full]`).
   - No full agent capability or a noninteractive session: request the approved READ-MAS
     SRS/design artifacts, or explain the `specadia[full]` install / interactive prerequisite.
   Specadia can generate SRS and design documents; it is not limited to existing READ-MAS artifacts.
3. Run `specadia-contract generate` with `--harness claude` and add `--design` only when supplied.
   (`specadia contract` is a retained alias.)
4. Do not add `--force` without explicit authorization.
5. Report generated contract and manifest paths. Do not begin implementation unless separately asked.
