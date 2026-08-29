---
name: specadia-plan
description: Convert approved requirements and design artifacts into a traceable Codex AGENTS.md contract with the installed Specadia CLI.
---

# Specadia Contract Handoff

1. Verify `specadia` is available.
2. Resolve the approved requirements path and optional design path. If the user supplied only an
   intent, request the READ-MAS outputs; Specadia does not generate designs.
3. Run `specadia contract "<requirements-path>" --harness codex`, adding
   `--design "<design-path>"` when supplied.
4. Preserve existing outputs. Add `--force` only with explicit authorization.
5. Report the generated `AGENTS.md` and manifest paths and surface validation failures unchanged.
6. Treat the output as a reviewed handoff artifact, not permission to start implementation.
7. Quote user-provided paths as shell arguments and never evaluate them as shell code.
