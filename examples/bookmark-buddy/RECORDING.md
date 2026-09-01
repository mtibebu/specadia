# Bookmark Buddy — Demo Recording Script

Timestamp: 2026-09-01T08:10:00Z
Target: 1:50–2:00

No secrets, no live LLM calls. The optional `from-intent` step is shown via
`--help` only and is documented in the Notes below, not a live visual beat.

| # | Time | Command you type | Narration (spoken) | What appears on screen |
|---|------|------------------|---------------------|------------------------|
| 1 | 0:00 | `cd examples/bookmark-buddy` | "We ship too many apps with a hand-wavy handoff from idea to code. Let me show you a small local-first CLI called Bookmark Buddy, and how Specadia turns a written contract into a reproducible, traceable handoff for a coding agent." | Terminal at the demo directory. |
| 2 | 0:12 | `cat intent.md` | "It starts as a plain intent — save, organize, and search bookmarks, entirely on your machine." | The intent paragraph renders. |
| 3 | 0:25 | `cat requirements.md` && `cat design.md` | "Important and worth being honest about: these two files are hand-authored. `requirements.md` is the source of truth (FR-1 through AC-1), and `design.md` adds the architecture and file layout. They are deterministic inputs I wrote — Specadia does not invent them here; it turns them into an implementation contract the same way every time." | requirements.md purpose/FR/NFR/AC headings, then design.md Architecture and File Structure sections. |
| 4 | 0:45 | `./run.sh` | "Now the deterministic part: the script generates the contract twice and diff-checks the two outputs." | Binary/workspace lines, then two `Generating contract into out-a/out-b` lines. |
| 5 | 1:05 | — (script continues) | "The two outputs are byte-for-byte identical, and no local paths or temp-directory names leak into them." | `PASS: identical (deterministic)` and `PASS: no absolute paths` lines. |
| 6 | 1:18 | `cat contracts/AGENTS.md` | "This is the implementation contract for Codex — the FR, NFR, and AC identifiers mapped to source hashes." | The generated AGENTS.md with "Bookmark Buddy Agent Contract" header. |
| 7 | 1:35 | `cat contracts/contract-manifest.json` | "The manifest records the SHA-256 of every input and output, so you can verify what a coding agent actually built against." | JSON manifest with project_name and sources/contracts hashes. |
| 8 | 1:50 | — (close) | "That's the whole loop: hand-authored requirements and design, a deterministic generator, and a traceable contract. Install it with `pip install specadia` and check the README for the quick start. Try it on your own next feature." | Terminal returns to prompt; overlay or outro card with `pip install specadia` and the README link. |

## Notes

- Ensure `specadia-contract` is on PATH before recording (or set `SPECADIA`).
- The optional `from-intent` path is **not** a live visual beat. If asked, it is
  documented in the demo README and needs `specadia[full]` plus a model; inspect
  it only via `specadia-contract from-intent --help`.
- Beat 3 must make the hand-authored, deterministic-input framing explicit so the
  viewer never mistakes `requirements.md`/`design.md` for auto-generated output.
