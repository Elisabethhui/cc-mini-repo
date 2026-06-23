---
name: code-intel
description: Use when exploring code with a strict context budget. Prefer CodeGraph and precise searches before reading source files.
---

# Code Intel

## Purpose

Reduce token usage during code exploration by querying local code intelligence before reading source files.

## File Boundary

Do not write query outputs into committed files by default. Temporary outputs belong in `.ai-dev/context-packs/`, `.ai-dev/tmp/`, or `.ai-dev/worklogs/`.

Never commit `.codegraph/`, `.codebase-memory/`, raw query dumps, or local task notes.

## Query Order

1. `codegraph status`
2. `codegraph files`
3. `codegraph query <keyword>`
4. `codegraph callers <symbol>`
5. `codegraph callees <symbol>`
6. `codegraph impact <symbol>`
7. `codegraph affected`

Use `codegraph explore "<question>"` only when narrower queries cannot locate the relevant code.

## Common Commands

```bash
codegraph status
codegraph files
codegraph query "<keyword>"
codegraph callers "<symbol>"
codegraph callees "<symbol>"
codegraph impact "<symbol>"
git diff --name-only | codegraph affected --stdin --quiet
```

## Output

Summarize results with task, queries run, relevant files, relevant symbols, callers/callees, impact, affected tests, and what still needs source read.

## Stop Rules

Stop and ask for task slicing if more than 5 files seem necessary, impact radius is broad, no clear target symbol is found, or query results conflict with repository structure.
