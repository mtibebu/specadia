---
name: specadia-plan
description: Convert approved requirements and design artifacts into a traceable Grok contract with the installed Specadia CLI.
---

# Specadia Contract Handoff

1. Verify `specadia` is available and resolve approved input artifact paths.
2. If only intent is available, request the READ-MAS outputs; Specadia does not generate designs.
3. Run `specadia contract "<requirements-path>" --harness generic`, adding
   `--design "<design-path>"` when supplied.
4. Add `--force` only with explicit authorization. Report outputs without starting implementation.
