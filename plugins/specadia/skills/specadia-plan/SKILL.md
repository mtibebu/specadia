---
name: specadia-plan
description: Use the installed Specadia CLI to turn software intent or an existing SRS and design into reviewed requirements, system design, a Codex AGENTS.md implementation contract, and traceability artifacts. Use when the user asks to plan, specify, design, or prepare a traceable implementation contract with Specadia.
---

# Specadia Plan

Keep Specadia's Python CLI as the execution engine. Use this skill only as the Codex-facing
workflow adapter.

## Choose the workflow

- For a natural-language intent, use `specadia-contract from-intent`.
- For an existing SRS and optional design, use `specadia contract`.
- For an interrupted intent run, inspect `specadia-contract runs` and resume only when the user
  identifies the run or the matching run is unambiguous.

## From intent

1. Verify `specadia-contract` is available. If it is missing, stop and tell the user to install
   Specadia with the `agents` extra.
2. Use the current repository root as `--repo`.
3. Run:

   ```bash
   specadia-contract from-intent "<intent>" --repo "<repository-root>" --harness codex
   ```

4. Preserve the interactive Collector approval. Do not add `--yes`.
5. Let the user approve, refine, or cancel before downstream stages run.
6. Report the SRS, design, `AGENTS.md`, manifest, and traceability paths.
7. Do not begin implementation unless the user separately asks for it.

## From existing documents

1. Verify `specadia` is available.
2. Resolve the SRS and optional design paths from the user's request.
3. Run:

   ```bash
   specadia contract "<srs-path>" --design "<design-path>" --harness codex
   ```

4. Omit `--design` when no design was supplied.
5. Do not overwrite existing output. If Specadia reports a conflict, show it and ask before
   rerunning with `--force`.
6. Report the generated contract and traceability artifacts.

## Guardrails

- Quote user-provided intent and paths as shell arguments; do not evaluate them as shell code.
- Respect Specadia's hosted-model confirmation.
- Never add `--force` or `--yes` without explicit user authorization.
- Treat generated `AGENTS.md` as an implementation contract, not permission to start coding.
- Surface validation failures instead of weakening Specadia's document or traceability checks.
