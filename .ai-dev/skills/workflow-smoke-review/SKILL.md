---
name: workflow-smoke-review
description: Use before product development to audit the context-bounded workflow scaffold for file boundary problems, malformed markdown, missing templates, ignored-path mistakes, and workflow inconsistency.
---

# Workflow Smoke Review

## Purpose

Review the context-bounded development scaffold before using it for real coding tasks.

This skill checks whether the workflow files are clean, consistent, correctly ignored, and safe to use.

It does not implement product code.

## Scope

Review only workflow-related files:

- `AGENTS.md`
- `.gitignore`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/skills/*/SKILL.md`
- `.ai-dev/templates/*.md`

Do not review or edit product source code during this skill.

## File Boundary

Committed workflow files may include:

- `AGENTS.md`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/skills/`
- `.ai-dev/templates/`

Ignored local task artifacts must include:

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`
- `.codegraph/`
- `.codebase-memory/`

Generated/cache files must not be staged:

- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- build outputs
- raw query dumps
- local logs

## Inputs

Use these inputs when available:

- current git status
- file list under `.ai-dev`
- `.gitignore`
- workflow skill files
- templates
- recent commits
- user concerns about file clutter or workflow confusion

## Review Checklist

Check these areas:

### 1. File Boundary

Verify that committed files and ignored files are clearly separated.

Confirm that local task state is ignored and not staged.

### 2. Markdown Structure

Check that each `SKILL.md` has:

- valid YAML frontmatter
- one clear top-level title
- closed code fences
- readable headings
- no accidental pasted output inside code blocks

### 3. Workflow Consistency

Confirm that the workflow order is consistent:

1. task-slicer
2. surface-search
3. code-intel
4. context-pack
5. implementation
6. map-sync
7. test-gate
8. fresh review / review-rollback
9. work-log

### 4. Template Coverage

Confirm that every committed workflow skill that needs a reusable artifact has a matching template when appropriate.

### 5. Safety

Check for:

- secrets
- API keys
- raw environment values
- local absolute paths that should not be committed
- generated logs
- tool caches
- accidental `.codegraph/` or `.codebase-memory/` files

### 6. Simplicity

Check that the workflow is not becoming a large wiki.

Keep workflow files short, operational, and reusable.

## Suggested Commands

Use these commands when available:

```bash
git status --short
find .ai-dev -maxdepth 3 -type f | sort
git diff --stat
git diff --check
git check-ignore .ai-dev/tasks/example.md
git check-ignore .ai-dev/context-packs/example.md
git check-ignore .ai-dev/worklogs/example.md
git check-ignore .codegraph/example.db
git check-ignore .codebase-memory/example.db
```

For markdown fence sanity, inspect skill files directly if needed.

## Output Format

Write the smoke review with these sections:

- `# Workflow Smoke Review`
- `## Files Reviewed`
- `## Boundary Check`
- `## Markdown Check`
- `## Workflow Consistency`
- `## Template Coverage`
- `## Safety Findings`
- `## Required Fixes`
- `## Recommended Fixes`
- `## Decision`

Decision must be one of:

- `pass`
- `pass-with-minor-fixes`
- `fix-before-use`
- `blocked`

## Fix Rules

Only suggest or make fixes inside workflow files.

Allowed fix paths:

- `AGENTS.md`
- `.gitignore`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/skills/`
- `.ai-dev/templates/`

Do not modify:

- `src/`
- `tests/`
- product docs unrelated to workflow
- package configuration
- generated files

## Stop Rules

Stop and ask the user before continuing if:

- product source files are dirty
- staged files include ignored local artifacts
- a secret or API key appears in committed files
- workflow files conflict with each other
- the review would require changing product code