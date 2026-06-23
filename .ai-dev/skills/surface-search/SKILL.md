---
name: surface-search
description: Use when a coding task does not yet have a clear file, symbol, route, command, error string, or module anchor.
---

# Surface Search

## Purpose

Find initial code anchors before precise CodeGraph exploration.

## Search Order

1. Extract keywords from user goal.
2. Search exact error strings or command names with `rg`.
3. Search likely filenames or directories.
4. Use `codegraph query <keyword>` for symbol candidates.
5. Use `codegraph files` for project surface.
6. Identify 1-3 likely anchors.
7. Hand off to code-intel.

## Stop Rules

Stop if no anchor can be found, more than 3 unrelated anchors are equally likely, the task is too broad, or finding the anchor requires reading many large files.
