# Bookmark Buddy Design

## Architecture

A single-command CLI backed by a small local store. Commands parse arguments, delegate to storage functions, and print results to standard output. Storage reads and writes one newline-delimited file, with each line holding one bookmark's URL, title, and tags so the file stays human-readable.

## File Structure

- `cli.py` — argument parsing and command dispatch.
- `store.py` — load, save, filter, and search operations against the bookmark file.
- `bookmarks.txt` — the local data file created on first save.
