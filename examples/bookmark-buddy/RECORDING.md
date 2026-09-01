# Bookmark Buddy — Demo Recording Script

Timestamp: 2026-09-01T08:04:00Z
Target: ~75s

No secrets, no live LLM calls. The optional `from-intent` step is shown via
`--help` only.

| # | Time | Command you type | Narration (spoken) | What appears on screen |
|---|------|------------------|---------------------|------------------------|
| 1 | 0:00 | `cd examples/bookmark-buddy` | "Let's look at a small local-first CLI product called Bookmark Buddy. It starts as a plain intent." | Terminal at the demo directory. |
| 2 | 0:08 | `cat intent.md` | "A single short paragraph describes saving, organizing, and searching bookmarks locally." | The intent paragraph renders. |
| 3 | 0:18 | `cat requirements.md` | "That intent becomes an SRS — the source of truth — with FR-1 through AC-1." | Purpose, FR-1..FR-3, NFR-1..NFR-2, AC-1 headings. |
| 4 | 0:30 | `cat design.md` | "A short design adds architecture and a file structure." | Architecture and File Structure sections. |
| 5 | 0:38 | `./run.sh` | "Now the deterministic part: Specadia generates a contract twice and diffs the two outputs." | Binary/workspace lines, then two `Generating contract into out-a/out-b` lines. |
| 6 | 0:50 | — (script continues) | "The two outputs are byte-for-byte identical, and no local paths leak into them." | `PASS: identical (deterministic)` and `PASS: no absolute paths` lines. |
| 7 | 0:58 | `cat contracts/AGENTS.md` | "This is the implementation contract for Codex — FR, NFR, and AC identifiers mapped with source hashes." | The generated AGENTS.md with "Bookmark Buddy Agent Contract" header. |
| 8 | 1:08 | `cat contracts/contract-manifest.json` | "The manifest records the SHA-256 of every input and output for traceability." | JSON manifest with project_name and sources/contracts hashes. |
| 9 | 1:15 | `specadia-contract from-intent --help` | "Finally, an optional live path turns intent into the same contract interactively — it needs `specadia[full]` and a model, so we only inspect its help." | from-intent usage/options list. |

## Notes

- Ensure `specadia-contract` is on PATH before recording (or set `SPECADIA`).
- Keep step 9 clearly framed as optional/live; do not run it.
