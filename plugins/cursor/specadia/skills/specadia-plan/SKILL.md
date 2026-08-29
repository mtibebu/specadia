---
name: specadia-plan
description: Convert approved requirements and design artifacts into a traceable Cursor contract with the installed Specadia CLI.
---

# Specadia Contract Handoff

1. Verify `specadia` is available.
2. Resolve the approved requirements path and optional design path. If only intent is available,
   request the READ-MAS outputs; Specadia does not generate designs.
3. Run `specadia contract "<requirements-path>" --harness generic`, adding
   `--design "<design-path>"` when supplied.
4. Add `--force` only with explicit authorization.
5. Report the generated contract and manifest paths. Do not start implementation unless asked.
