---
name: batch-file-notes
description: 32K-safe batched file-note workflow with a smaller default batch size and strict stopping rules
context: fork
allowed-tools: Bash, Read, Glob, Grep, Write
arguments: [optional batch size, default 2, max 3]
---

# Batch File Notes (32K Safe)

You are generating a small batch of file notes.

## Goal
Pick the next unfinished important files and create notes for them with minimal context growth.

## Context safety rules
- Default batch size is 2.
- Never process more than 3 files in one run.
- If two files are both large, stop after one file.
- Prefer finished notes over broader coverage.
- Use the same strict limits as `/file-note` for each file.
- Prefer scripts to select targets and refresh TODO/progress.

## Required tasks
1. Read `./code-reading-notes/manifest.json`.
2. Determine batch size from `$ARGUMENTS`, default 2, max 3.
3. Use helper scripts to pick next files.
4. Produce one markdown note per selected file under `./code-reading-notes/10_file_notes/`.
5. Update manifest/TODO/progress through scripts or minimal edits.

## Selection policy
Prefer in this order:
1. README and entry files
2. config files
3. runtime / executor / engine / service files
4. state / memory / compact files
5. agents / planners
6. tools / helpers

## Stop condition
Stop after the selected batch is completed.
Do not begin module-level summarization.
