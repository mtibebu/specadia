---
name: specadia-plan
description: Convert approved requirements and design artifacts into a traceable Codex AGENTS.md contract with the installed Specadia CLI.
---

# Specadia Contract Handoff

1. Verify `specadia` is available.
2. Resolve the approved requirements path and optional design path, then choose a generation path:
   - Approved SRS/design artifacts: use the canonical `specadia-contract generate`.
   - Only raw intent and a full agent-capable install: use `specadia-contract from-intent`
     (human-in-the-loop intent-to-SRS/design-to-contract; requires the optional
     `specadia[full]` dependency).
   - No full agent capability or a noninteractive session: request the approved READ-MAS
     SRS/design artifacts, or explain the `specadia[full]` install / interactive prerequisite.
   Specadia can generate SRS and design documents; it is not limited to existing READ-MAS artifacts.
3. Run `specadia-contract generate "<requirements-path>" --harness codex`, adding
   `--design "<design-path>"` when supplied. (`specadia contract` is a retained alias.)
4. Preserve existing outputs. Add `--force` only with explicit authorization.
5. Report the generated `AGENTS.md` and manifest paths and surface validation failures unchanged.
6. Treat the output as a reviewed handoff artifact, not permission to start implementation.
7. Quote user-provided paths as shell arguments and never evaluate them as shell code.
