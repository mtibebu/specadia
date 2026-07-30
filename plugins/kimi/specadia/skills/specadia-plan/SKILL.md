---
name: specadia-plan
description: Use the installed Specadia CLI to turn software intent or an existing SRS and design into reviewed requirements, system design, an implementation contract, and traceability artifacts. Use when the user asks to plan, specify, design, or prepare a traceable implementation contract with Specadia.
---

# Specadia Plan

Keep Specadia's Python CLI as the execution engine.

## Choose the workflow

- For natural-language intent, use `specadia-contract from-intent`.
- For an existing SRS and optional design, use `specadia contract`.
- For an interrupted run, inspect `specadia-contract runs` and resume only when the matching run
  is unambiguous.

## From intent

1. Verify `specadia-contract` is available. If missing, tell the user to install Specadia with
   the `agents` extra.
2. Run:

   ```bash
   specadia-contract from-intent "<intent>" --repo "<repository-root>" --harness generic
   ```

3. Preserve interactive Collector approval. Do not add `--yes`.
4. Let the user approve, refine, or cancel before downstream stages run.
5. Report the SRS, design, contract, manifest, and traceability paths.
6. Do not begin implementation unless separately requested.

## From existing documents

1. Verify `specadia` is available.
2. Run `specadia contract "<srs-path>" --harness generic`, adding
   `--design "<design-path>"` only when supplied.
3. Do not overwrite output. Ask before rerunning with `--force`.
4. Report the contract and traceability artifacts.

## Guardrails

- Quote user-provided intent and paths; do not evaluate them as shell code.
- Respect hosted-model confirmation.
- Never add `--force` or `--yes` without explicit authorization.
- Treat the generated contract as a plan, not permission to start coding.
- Surface validation failures instead of weakening Specadia's checks.
