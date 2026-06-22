---
name: code-intel
description: Use when exploring code with a strict context budget. Prefer CodeGraph and precise searches before reading source files.
---

# Code Intel

## Purpose

Reduce token usage during code exploration by querying local code intelligence before reading source files.

Use this skill before implementation, debugging, impact analysis, or test selection.

## File Boundary

Do not write query outputs into committed files by default.

Temporary outputs belong in ignored local paths:

- `.ai-dev/context-packs/`
- `.ai-dev/tmp/`
- `.ai-dev/worklogs/`

Never commit:

- `.codegraph/`
- `.codebase-memory/`
- raw query dumps
- local task notes

## Query Order

Use the smallest useful query first:

1. `codegraph status`
2. `codegraph files`
3. `codegraph query <keyword>`
4. `codegraph callers <symbol>`
5. `codegraph callees <symbol>`
6. `codegraph impact <symbol>`
7. `codegraph affected`

Use `codegraph explore "<question>"` only when narrower queries cannot locate the relevant code.

## Before Reading Source

Before opening a large file, answer:

- What symbol, file, or behavior am I looking for?
- Which CodeGraph query can narrow it?
- What is the minimum snippet needed?

Prefer symbol-level or small snippet reads over whole-file reads.

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

When preparing code intelligence results for a task, summarize them with these sections:

- `# Code Intelligence Summary`
- `## Task`
- `## Queries Run`
- `## Relevant Files`
- `## Relevant Symbols`
- `## Callers / Callees`
- `## Impact`
- `## Affected Tests`
- `## Still Needs Source Read`

Keep the output short. Do not paste raw query dumps unless the exact lines are needed.

## Stop Rules

Stop and ask for task slicing if:

- more than 5 files seem necessary
- impact radius is broad
- no clear target symbol is found
- query results conflict with repository structure
- the next step would require reading a large file without a target symbol