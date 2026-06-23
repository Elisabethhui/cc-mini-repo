---
name: workflow-smoke-review
description: Use before product development to audit the context-bounded workflow scaffold for file boundary problems, malformed markdown, missing templates, ignored-path mistakes, and workflow inconsistency.
---

# Workflow Smoke Review

## Purpose

Review the context-bounded scaffold before using it for real coding tasks.

## Scope

Review only `AGENTS.md`, `.gitignore`, `.ai-dev/README.md`, `.ai-dev/WORKFLOW.md`, `.ai-dev/skills/*/SKILL.md`, `.ai-dev/templates/*.md`, and `.ai-dev/design/*.md`.

## Checks

Check file boundaries, markdown structure, workflow consistency, template coverage, secrets, generated files, and excessive wiki-like bloat.

## Decision

Return pass, pass-with-minor-fixes, fix-before-use, or blocked.
