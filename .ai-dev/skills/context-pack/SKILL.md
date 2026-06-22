---
name: context-pack
description: Use when preparing a minimal task-specific context package for a small-context coding model after code intelligence queries.
---

# Context Pack

## Purpose

Create a compact, task-specific context package that lets a small-context model implement one task without reading the whole codebase.

A context pack is not a wiki. It is a temporary working packet for one task.

## File Boundary

Committed files:

- `.ai-dev/skills/context-pack/SKILL.md`
- `.ai-dev/templates/CONTEXT_PACK.md`

Local task outputs:

- `.ai-dev/context-packs/task-xxx.md`

Do not commit generated context packs unless explicitly requested.

Never include secrets, API keys, raw environment values, or long logs.

## Inputs

Use these inputs when available:

- current task file
- CodeGraph query results
- relevant `rg` results
- selected small source snippets
- test discovery results
- known constraints from `AGENTS.md`

## Budget Defaults

For 32k context:

- max relevant files: 5
- max editable files: 3
- max source snippets: 5
- max snippet size: 80 lines each
- max total context pack length: about 300-600 lines
- prefer summaries over full file content

If the task needs more than this, return to task slicing.

## Build Process

1. Read the current task.
2. Summarize the exact goal.
3. Run or collect code intelligence queries.
4. Identify relevant files and symbols.
5. Include only the minimum source snippets needed.
6. List tests or verification commands.
7. List exclusions: what the model should not inspect or change.
8. List open questions or blockers.
9. Stop before implementation.

## Compression Rules

Keep:

- file paths
- symbol names
- function/class responsibilities
- call relationships
- constraints
- test commands
- exact snippets only when needed

Remove:

- duplicate explanations
- long historical notes
- full command logs
- unrelated architecture commentary
- raw grep dumps
- secrets
- generated cache content

## Code Intelligence Section

Prefer small CodeGraph queries before broad exploration:

```bash
codegraph status
codegraph query "<keyword>"
codegraph callers "<symbol>"
codegraph callees "<symbol>"
codegraph impact "<symbol>"
git diff --name-only | codegraph affected --stdin --quiet
```

Use `codegraph explore "<question>"` only if smaller queries fail to locate the target.

## Output Format

Write the context pack with these sections:

- `# Context Pack: task-xxx`
- `## Goal`
- `## Current Constraints`
- `## Code Intelligence Summary`
- `### Queries Run`
- `### Relevant Files`
- `### Relevant Symbols`
- `### Callers / Callees`
- `### Impact Radius`
- `### Affected Tests`
- `## Required Source Snippets`
- `## Allowed Edits`
- `## Do Not Touch`
- `## Verification Plan`
- `## Rollback Plan`
- `## Open Questions`

For source snippets, include only short snippets that are necessary for implementation.

## Quality Check

Before finishing, verify:

- The pack is tied to one task.
- It does not include unrelated files.
- It can fit a 32k model.
- It includes a test or verification path.
- It avoids local secrets and generated files.
- It clearly says what not to change.

## Stop Rules

Stop and ask for a smaller task if:

- more than 5 files are needed
- no target symbol can be identified
- the impact radius is broad
- the verification path is unclear
- the context pack would become a long wiki