---
name: surface-search
description: Use when a coding task does not yet have a clear file, symbol, route, command, error string, or module anchor. Finds initial anchors before precise CodeGraph exploration.
---

# Surface Search

## Purpose

Find the first useful code anchors for a task before running precise code intelligence queries.

Use this skill when the user request is phrased in product language, bug language, UI language, or error language rather than concrete file or symbol names.

Examples:

- "fix login 500"
- "add a workflow status command"
- "the config page crashes"
- "support CodeGraph sync"
- "make plan mode safer"

Surface search prevents the model from guessing which symbol to query.

## Relationship To Code Intel

Surface search comes before `code-intel`.

Use surface search to discover candidate anchors.

Then use `code-intel` to expand those anchors with callers, callees, impact, affected tests, and snippets.

## File Boundary

Committed files:

- `.ai-dev/skills/surface-search/SKILL.md`
- `.ai-dev/templates/SURFACE_SEARCH.md`

Local search notes belong in ignored paths:

- `.ai-dev/tmp/`
- `.ai-dev/context-packs/`

Do not commit raw search dumps unless explicitly requested.

Never include secrets, API keys, raw environment values, or huge terminal output.

## Inputs

Use these inputs when available:

- user goal
- current task file
- error message
- stack trace
- command name
- route or endpoint
- UI label
- config key
- test failure name
- project map
- CodeGraph file list
- `rg` results

## Anchor Types

Look for these anchors:

- file path
- function or method name
- class name
- CLI command name
- route or endpoint
- config key
- error message
- test name
- module or package name
- documentation section

A good anchor should lead to a small set of files or symbols.

## Search Order

Use the lowest-cost search that can produce an anchor:

1. Extract keywords from the user goal.
2. Search exact error strings or command names with `rg`.
3. Search likely filenames or directories.
4. Use `codegraph query <keyword>` for symbol candidates.
5. Use `codegraph files` to inspect project surface area.
6. Identify 1-3 likely anchors.
7. Hand off anchors to `code-intel`.

## Suggested Commands

Use these commands when appropriate:

```bash
rg -n "<exact error or keyword>"
rg -n "<command name>|<route>|<config key>"
find . -maxdepth 3 -type f | sort
codegraph status
codegraph files
codegraph query "<keyword>"
```

Prefer exact searches before fuzzy exploration.

## Keyword Extraction Rules

From the user goal, extract:

- nouns
- error strings
- command names
- API paths
- config keys
- filenames
- UI labels
- test names
- domain words

Drop generic words like:

- fix
- add
- update
- improve
- make
- support
- refactor
- issue
- bug

## Output Format

Write the surface search result with these sections:

- `# Surface Search: task-xxx`
- `## User Goal`
- `## Extracted Keywords`
- `## Searches Run`
- `## Candidate Anchors`
- `## Best Anchor`
- `## Why This Anchor`
- `## Next Code Intel Queries`
- `## Open Questions`

## Candidate Anchor Format

For each candidate anchor, record:

- path or symbol
- evidence
- confidence: high / medium / low
- next query

Example:

- Anchor: `src/core/main.py`
- Evidence: contains CLI command dispatch
- Confidence: medium
- Next query: `codegraph query "workflow"`

## Stop Rules

Stop and ask the user or return to task slicing if:

- no anchor can be found
- more than 3 unrelated anchors look equally likely
- the search points to broad architecture rather than a specific task
- the task is actually a product/design question, not an implementation task
- finding the anchor requires reading many large files