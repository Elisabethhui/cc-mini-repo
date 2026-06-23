---
name: context-pack
description: Use when preparing a minimal task-specific context package for a small-context coding model after code intelligence queries.
---

# Context Pack

## Purpose

Create a compact, task-specific packet that lets a small-context model implement one task without reading the whole codebase.

## File Boundary

Committed files are this skill and `.ai-dev/templates/CONTEXT_PACK.md`. Local outputs belong in `.ai-dev/context-packs/` and are not committed by default.

Never include secrets, API keys, raw environment values, or long logs.

## Budget Defaults

For 32k: max 5 relevant files, max 3 editable files, max 5 source snippets, max 80 lines each, and about 300-600 lines total.

## Build Process

Read the current task, summarize goal, collect code-intel results, identify relevant files/symbols, include minimum snippets, list tests, list exclusions, list blockers, then stop before implementation.

## Compression Rules

Keep paths, symbols, responsibilities, call relationships, constraints, test commands, and exact snippets only when needed.

Remove duplicate explanation, long history, raw logs, unrelated architecture commentary, raw grep dumps, secrets, and generated cache content.

## Output Format

Sections: goal, current constraints, code intelligence summary, required source snippets, allowed edits, do not touch, verification plan, rollback plan, open questions.
