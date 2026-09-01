# Bookmark Buddy Agent Contract

These instructions define the implementation contract for Codex and its subagents.

## Authority

The source documents listed below are the product source of truth. Preserve explicit requirement identifiers in code, tests, and review notes. When sources conflict, stop and report the conflict instead of silently choosing an interpretation.

- `spec`: `requirements.md` (SHA-256 `a0cf9df4bd30dae8d85a3efe83c1a652ffe4a61795ba4a69292195c4324acac1`)
- `design`: `design.md` (SHA-256 `7708300a918b903f74962738a1eb81b96cfd8075881232bf45ca9c59472043a1`)

## Objective

Bookmark Buddy is a local-first command-line application that lets a user save, organize, and search web bookmarks. Bookmarks are stored in a single plain-text file on the user's machine; the app has no server, no account, and no network dependency.

## Requirements

- `FR-1`: Users can save a bookmark by providing a URL and an optional title and one or more tags.
- `FR-2`: Users can list saved bookmarks and filter them by tag.
- `FR-3`: Users can search saved bookmarks by matching text in the title or URL.
- `NFR-1`: All bookmark data is stored locally in a single human-readable file and never sent over the network.
- `NFR-2`: Commands complete interactively for a personal-scale bookmark collection.
- `AC-1`: A bookmark can be saved, then listed, filtered, and searched with the same required tags and URL.

## Quality

- NFR-1: All bookmark data is stored locally in a single human-readable file and never sent over the network.
- NFR-2: Commands complete interactively for a personal-scale bookmark collection.

## Architecture

A single-command CLI backed by a small local store. Commands parse arguments, delegate to storage functions, and print results to standard output. Storage reads and writes one newline-delimited file, with each line holding one bookmark's URL, title, and tags so the file stays human-readable.

- `cli.py` — argument parsing and command dispatch.
- `store.py` — load, save, filter, and search operations against the bookmark file.
- `bookmarks.txt` — the local data file created on first save.

## Acceptance

- AC-1: A bookmark can be saved, then listed, filtered, and searched with the same required tags and URL.

## Delivery Rules

- Keep changes within the scope above and preserve unrelated user changes.
- Prefer existing project patterns and dependencies before adding abstractions.
- Add tests for changed behavior and run the narrowest relevant verification suite.
- Map every implemented requirement ID to verification evidence in the final report.
- Report assumptions, unresolved ambiguities, skipped tests, and residual risks.
- Do not claim completion while required acceptance criteria are unverified.
