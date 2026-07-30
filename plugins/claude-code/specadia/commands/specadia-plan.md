---
description: Turn an intent into a reviewed Specadia requirements, design, and Claude implementation contract
argument-hint: <software intent>
allowed-tools: Bash
---

Create a Specadia implementation plan for this intent:

$ARGUMENTS

Use the repository containing the current Claude Code session as project context.

1. Verify that `specadia-contract` is available. If it is missing, stop and tell the user to
   install Specadia with its `agents` extra.
2. Run `specadia-contract from-intent` with the intent above, `--repo "$CLAUDE_PROJECT_DIR"`,
   and `--harness claude`.
3. Keep Specadia's interactive Collector approval enabled. Do not add `--yes`.
4. After the run, summarize the generated SRS, design, Claude contract, and traceability
   artifacts. Report their paths and any validation failures.
5. Do not begin implementation unless the user separately asks Claude Code to implement the
   approved contract.
