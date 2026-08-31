---
description: Generate a Claude implementation contract from an existing SRS and optional design
argument-hint: <path-to-srs> [path-to-design]
allowed-tools: Bash
---

Generate a Claude Code implementation contract from the documents named in:

$ARGUMENTS

1. Verify that `specadia` is available.
2. Treat the first path as the SRS and the optional second path as the design document.
3. Run `specadia-contract generate` with `--harness claude`. Include `--design` only when a design
   path was supplied. (`specadia contract` is a retained alias.)
4. Do not overwrite existing output. If Specadia reports an existing file, show the conflict and
   ask before rerunning with `--force`.
5. Summarize the output contract and traceability artifacts, including their paths.
