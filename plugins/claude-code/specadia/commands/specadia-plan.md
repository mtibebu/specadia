---
description: Convert approved requirements and design artifacts into a Claude implementation contract
argument-hint: <path-to-requirements> [path-to-design]
allowed-tools: Bash
---

Create a Claude implementation contract from these approved artifacts:

$ARGUMENTS

1. Verify `specadia` is available.
2. Treat the first path as requirements and the optional second path as design. If paths were not
   provided, request the READ-MAS outputs; Specadia does not generate designs.
3. Run `specadia contract` with `--harness claude` and add `--design` only when supplied.
4. Do not add `--force` without explicit authorization.
5. Report generated contract and manifest paths. Do not begin implementation unless separately asked.
