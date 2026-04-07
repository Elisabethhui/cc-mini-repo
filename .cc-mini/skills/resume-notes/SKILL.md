---
name: resume-notes
description: 32K-safe progress and recovery skill for continuing after interruption or token overflow
context: fork
allowed-tools: Bash, Read, Glob, Grep, Write
arguments:
---

# Resume Notes (32K Safe)

You are reporting reading progress and recommending the next step.

## Goal
Help the user continue the workflow after interruption, token overflow, or partial completion.

## Context safety rules
- Do not perform any new code reading.
- Only inspect progress artifacts and generated notes.
- Prefer reporting and next-step recommendation over any new synthesis.

## Required tasks
1. Read:
   - `./code-reading-notes/manifest.json`
   - `./code-reading-notes/TODO.md`
   - `./code-reading-notes/progress.md`
2. Report:
   - what has been completed
   - what remains
   - what the next best skill is
   - what the next 3 target files/modules should be
   - whether the previous skill appears partially completed and can be resumed from disk
3. Optionally update:
   - `progress.md`

## Stop condition
Stop after reporting progress and next actions.
