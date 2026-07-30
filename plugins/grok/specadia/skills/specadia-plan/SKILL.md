---
name: specadia-plan
description: Use the installed Specadia CLI to turn software intent or existing requirements into a reviewed system design, implementation contract, and traceability artifacts. Use when the user asks Grok Build to plan, specify, or design software with Specadia.
---

# Specadia Plan

Use Specadia as the planning engine.

1. Verify `specadia-contract` is available.
2. For intent, run `specadia-contract from-intent "<intent>" --repo "<repository-root>"
   --harness generic`.
3. For an existing SRS, run `specadia contract "<srs-path>" --harness generic`, adding
   `--design "<design-path>"` when supplied.
4. Preserve interactive approval. Never add `--yes` or `--force` without explicit authorization.
5. Report generated source, contract, manifest, and traceability paths.
6. Do not start implementation unless separately requested.
7. Quote user-provided shell arguments and surface validation failures unchanged.
