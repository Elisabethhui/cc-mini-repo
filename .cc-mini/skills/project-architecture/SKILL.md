---
name: project-architecture
description: 32K-safe project summary that consumes generated notes and avoids source rereads
context: fork
allowed-tools: Bash, Read, Glob, Grep, Write
arguments: [optional topic or subsystem]
---

# Project Architecture (32K Safe)

You are generating a project-level architecture summary.

## Goal
Explain the whole project using generated scan outputs, file notes, and module notes.

## Context safety rules
- Prefer generated notes over raw source files.
- Do not reread the whole codebase.
- Read at most 1 raw source file only if there is a critical gap.
- If module notes are insufficient, stop and recommend `/module-note` instead of continuing.
- Focus on mainline architecture and technical highlights.

## Required tasks
1. Read:
   - `./code-reading-notes/00_repo_scan/*`
   - `./code-reading-notes/10_file_notes/*`
   - `./code-reading-notes/20_module_notes/*`
   - `./code-reading-notes/manifest.json`
   - optionally `./code-reading-notes/30_project_summary/summary_inputs.json` if present
2. Produce:
   - `./code-reading-notes/30_project_summary/project_architecture.md`
   - `./code-reading-notes/30_project_summary/project_technical_highlights.md`
3. Update manifest/progress minimally.

## Stop condition
Stop after the project summary files are written.
