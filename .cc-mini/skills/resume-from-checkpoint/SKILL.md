---
name: resume-from-checkpoint
description: Recover from interruption or token overflow by inspecting on-disk notes and recommending the next safe step
context: fork
allowed-tools: Bash, Read, Glob, Grep, Write
arguments:
---

# Resume From Checkpoint

You are a recovery skill for interrupted code-reading workflows.

## Goal
Recover from partial progress after interruption, API failure, or token overflow.

## Context safety rules
- Do not perform any broad code reading.
- Do not reread raw source files.
- Prefer reading only progress artifacts and generated note files.
- Your job is to inspect what already exists on disk, determine what is complete, detect partial outputs, and recommend the next minimal safe action.

## Required tasks
1. Ensure `./code-reading-notes/` exists. If it does not, explain that the workflow has not been initialized and recommend `/repo-bootstrap`.
2. Inspect:
   - `./code-reading-notes/manifest.json`
   - `./code-reading-notes/TODO.md`
   - `./code-reading-notes/progress.md`
   - `./code-reading-notes/00_repo_scan/`
   - `./code-reading-notes/10_file_notes/`
   - `./code-reading-notes/20_module_notes/`
   - `./code-reading-notes/30_project_summary/`
   - `./code-reading-notes/40_interview_notes/`
3. Use helper scripts to:
   - detect partial outputs
   - suggest the next safe action
4. Write:
   - `./code-reading-notes/checkpoint_report.md`
5. Optionally update:
   - `./code-reading-notes/progress.md`

## Output requirements
The checkpoint report must explain:
- what already exists
- what is missing
- what appears partially completed
- what the next best skill is
- whether the user should rerun `/repo-scan`, run `/repo-bootstrap`, continue with `/batch-file-notes 2`, `/module-note`, `/project-architecture`, or `/project-interview`

## Stop condition
Stop after the checkpoint report is written.
Do not continue into code reading.
