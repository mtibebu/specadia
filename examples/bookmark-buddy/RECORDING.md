# Bookmark Buddy — Demo Recording Script

Timestamp: 2026-09-01T21:05:00Z
Target: ~2:00 (1:50–2:00)

No secrets, no live LLM calls. `requirements.md` and `design.md` are
hand-authored, deterministic inputs; `specadia-contract generate` is the only
command that runs. The optional `from-intent` step is shown via `--help` only.

| # | Time | Command you type | Narration (spoken) | What appears on screen |
|---|------|------------------|---------------------|------------------------|
| 1 | 0:00 | `cd examples/bookmark-buddy` | "This is Bookmark Buddy, a tiny local-first CLI for saving and searching bookmarks. It starts from a single plain-English intent." | Terminal at the demo directory. |
| 2 | 0:10 | `cat intent.md` | "One short paragraph: save, organize, and search bookmarks — all on your own machine." | The intent paragraph renders. |
| 3 | 0:22 | `cat requirements.md` | "A human turns that intent into this SRS, the source of truth: FR-1 through NFR-2 and AC-1. Specadia doesn't derive it — it's a hand-authored input." | Purpose, FR-1..FR-3, NFR-1..NFR-2, AC-1 headings. |
| 4 | 0:44 | `cat design.md` | "A short hand-authored design adds the architecture and file structure — a second deterministic input." | Architecture and File Structure sections. |
| 5 | 0:58 | `./run.sh` | "Now the Specadia part: `generate` runs twice — no credentials, no live model — then diffs the two outputs." | Two `Generating contract into out-a/out-b` lines. |
| 6 | 1:22 | — (script continues) | "The two runs are byte-for-byte identical, and no local paths leak into the output." | `PASS: identical (deterministic)` and `PASS: no absolute paths`. |
| 7 | 1:32 | `cat contracts/AGENTS.md` | "That output is the coding-agent contract for Codex — every FR, NFR, and AC mapped to its source document." | The generated AGENTS.md with "Bookmark Buddy Agent Contract" header. |
| 8 | 1:44 | `cat contracts/contract-manifest.json` | "The manifest records the SHA-256 of every input and output, so each requirement traces to its source." | JSON manifest with project_name and sources/contracts hashes. |
| 9 | 1:54 | `specadia-contract from-intent --help` | "Finally, an optional live path needs a model and the full extras, so we only inspect its help." | from-intent usage/options list; cut to close around the two-minute mark. |

## Notes

- Ensure `specadia-contract` is on PATH before recording (or set `SPECADIA`).
- Keep step 9 clearly framed as optional/live; do not run it.
- To land at 1:50–2:00, keep each `cat` brief and do not reread whole files aloud.
