# Bookmark Buddy — Demo Recording Script

Timestamp: 2026-09-01T21:05:00Z
Target: ~2:00 (1:50–2:00)

No secrets, no live LLM calls. `requirements.md` and `design.md` are
hand-authored, deterministic inputs; `specadia-contract generate` is the only
command that runs. The optional `from-intent` step is shown via `--help` only.

| # | Time | Command you type | Narration (spoken) | What appears on screen |
|---|------|------------------|---------------------|------------------------|
| 1 | 0:00 | `cd examples/bookmark-buddy` | "This is Bookmark Buddy, a tiny local-first CLI for saving and searching bookmarks. It starts from one plain-English intent." | Terminal at the demo directory. |
| 2 | 0:10 | `cat intent.md` | "Save, organize, and search bookmarks, all on your own machine. No accounts, cloud services, or hidden dependencies." | The intent paragraph renders. |
| 3 | 0:22 | `cat requirements.md` | "A human turns that intent into this requirements document, the source of truth. Specadia does not derive it; it is a reviewed, hand-authored input." | Purpose, FR-1..FR-3, NFR-1..NFR-2, AC-1 headings. |
| 4 | 0:44 | `cat design.md` | "A short hand-authored design adds the architecture and file structure, making implementation choices visible before coding begins." | Architecture and File Structure sections. |
| 5 | 0:58 | `./run.sh` | "Now Specadia takes over. Generate runs twice with the same inputs, without credentials or a live model, then compares both outputs." | Two `Generating contract into out-a/out-b` lines. |
| 6 | 1:22 | — (script continues) | "The runs are byte-for-byte identical, and no local absolute paths leak into the generated artifacts." | `PASS: identical (deterministic)` and `PASS: no absolute paths`. |
| 7 | 1:32 | `cat contracts/AGENTS.md` | "The coding-agent contract maps every requirement and acceptance criterion back to its reviewed source." | The generated AGENTS.md with "Bookmark Buddy Agent Contract" header. |
| 8 | 1:44 | `cat contracts/contract-manifest.json` | "The manifest hashes each input and output, creating a compact, verifiable chain from source documents to contract." | JSON manifest with project_name and sources/contracts hashes. |
| 9 | 1:54 | — (return to title frame) | "Install Specadia from PyPI, and give your coding agent a real contract." | Return to the Bookmark Buddy title frame and call to action. |

## Notes

- Ensure `specadia-contract` is on PATH before recording (or set `SPECADIA`).
- To land at 1:50–2:00, keep each `cat` brief and do not reread whole files aloud.
