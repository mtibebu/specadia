---
name: specadia-plan
description: Convert approved requirements and design artifacts into a traceable generic coding-agent contract with the installed Specadia CLI.
---

# Specadia Contract Handoff

1. Verify `specadia` is available and resolve approved input artifact paths.
2. Choose a generation path by what is available:
   - Approved SRS/design artifacts: use the canonical `specadia-contract generate`.
   - Only raw intent and a full agent-capable install: use `specadia-contract from-intent`
     (human-in-the-loop intent-to-SRS/design-to-contract; requires the optional
     `specadia[full]` dependency).
   - No full agent capability or a noninteractive session: request the approved READ-MAS
     SRS/design artifacts, or explain the `specadia[full]` install / interactive prerequisite.
   Specadia can generate SRS and design documents; it is not limited to existing READ-MAS artifacts.
3. Run `specadia-contract generate "<requirements-path>" --harness generic`, adding
   `--design "<design-path>"` when supplied. (`specadia contract` is a retained alias.)
4. Add `--force` only with explicit authorization.
5. Report outputs and validation failures. Do not start implementation unless separately asked.
