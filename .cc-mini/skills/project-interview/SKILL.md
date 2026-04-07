---
name: project-interview
description: 32K-safe interview summary skill that never rereads raw source files
context: fork
allowed-tools: Bash, Read, Glob, Grep, Write
arguments: [optional focus module or topic]
---

# Project Interview (32K Safe)

You are converting project understanding into interview-ready material.

## Goal
Turn generated project summaries into concise, high-quality interview content.

## Context safety rules
- Never read raw source files in this skill.
- Use only project summaries, module notes, and interview helper files.
- Focus on concise, reusable interview output.
- Stop after the required interview files are written.

## Required tasks
1. Read:
   - `./code-reading-notes/30_project_summary/*`
   - relevant `./code-reading-notes/20_module_notes/*`
   - `./code-reading-notes/40_interview_notes/qa_bank.md` if present
   - `./code-reading-notes/manifest.json`
2. Produce:
   - `./code-reading-notes/40_interview_notes/project_interview_30s.md`
   - `./code-reading-notes/40_interview_notes/project_interview_full.md`
   - `./code-reading-notes/40_interview_notes/qa_bank.md` if missing or incomplete
3. Update manifest/progress minimally.

## Stop condition
Stop after the interview files are written.
