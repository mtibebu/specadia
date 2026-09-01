# Bookmark Buddy

## Purpose

Bookmark Buddy is a local-first command-line application that lets a user save, organize, and search web bookmarks. Bookmarks are stored in a single plain-text file on the user's machine; the app has no server, no account, and no network dependency.

## Functional Requirements

- FR-1: Users can save a bookmark by providing a URL and an optional title and one or more tags.
- FR-2: Users can list saved bookmarks and filter them by tag.
- FR-3: Users can search saved bookmarks by matching text in the title or URL.

## Non-Functional Requirements

- NFR-1: All bookmark data is stored locally in a single human-readable file and never sent over the network.
- NFR-2: Commands complete interactively for a personal-scale bookmark collection.

## Acceptance Criteria

- AC-1: A bookmark can be saved, then listed, filtered, and searched with the same required tags and URL.
