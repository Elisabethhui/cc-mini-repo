---
name: context-tier-policy
description: Use when a task has more relevant code than the model context can safely hold. Classify context into core, support, and peripheral tiers instead of hard-dropping files.
---

# Context Tier Policy

## Purpose

Prevent context loss when a task touches more code than a small-context model can safely read.

This skill upgrades context packing from simple file-count limits to tiered context selection.

Do not hard-drop relevant code just because the context budget is small. Degrade the detail level instead.

## Relationship To Context Pack

Use this skill inside or before `context-pack` when CodeGraph, search, or impact analysis finds many related files.

The result should guide what `context-pack` includes as source body, signature, summary, or exclusion.

## File Boundary

Committed file:

- `.ai-dev/skills/context-tier-policy/SKILL.md`

Local tier notes belong in ignored paths:

- `.ai-dev/context-packs/`
- `.ai-dev/tmp/`

Never commit:

- raw query dumps
- generated cache content
- `.codegraph/`
- `.codebase-memory/`
- secrets
- API keys

## Inputs

Use these inputs when available:

- current task file
- surface-search anchors
- code-intel results
- CodeGraph callers/callees/impact
- changed files
- test targets
- model context size
- known risk areas

## Context Tiers

Classify context into three tiers.

### Core

Core context is code the model is likely to edit or must understand deeply.

Include:

- target functions/classes/methods
- directly edited files
- nearby tests being changed
- public interface being modified

Representation:

- short source snippets
- exact signatures
- local invariants
- focused comments only if needed

### Support

Support context is directly related code the model needs to respect but probably should not edit.

Include:

- direct callers
- direct callees
- interface definitions
- config schema
- related tests
- nearby command wiring

Representation:

- signatures
- responsibilities
- constraints
- short snippets only when necessary

### Peripheral

Peripheral context is broad impact area or architecture context that should guide caution but not consume source budget.

Include:

- indirect callers/callees
- distant impacted modules
- generated files
- broad architecture notes
- optional feature areas

Representation:

- file paths
- symbol names
- one-line responsibility
- risk note

Do not include source bodies for peripheral context.

## Tiering Rules

Use these defaults for 32k models:

- Core: up to 3 files or 5 symbols
- Support: up to 5 files or 10 symbols
- Peripheral: summary only

For 64k models:

- Core may include more snippets
- Support can include selected short snippets
- Peripheral remains summary only

For 128k+ models:

- More source can be included, but tiers still apply
- Do not turn the context pack into a wiki

## Selection Priority

Prioritize in this order:

1. Files the task is allowed to edit.
2. Symbols directly mentioned by the user or task.
3. Functions/classes found by surface-search.
4. Direct callers/callees from CodeGraph.
5. Tests likely affected by the change.
6. Public API or config boundaries.
7. Peripheral impact summary.

## Degradation Policy

When context is too large, degrade in this order:

1. Full snippet to short snippet.
2. Short snippet to signature.
3. Signature to responsibility summary.
4. Responsibility summary to path plus risk note.
5. Exclude only if irrelevant or duplicate.

Never silently drop a high-risk dependency. Mark it as peripheral with a risk note.

## Output Format

Write the tier policy result with these sections:

- `# Context Tier Policy: task-xxx`
- `## Task`
- `## Context Budget`
- `## Core Context`
- `## Support Context`
- `## Peripheral Context`
- `## Excluded Context`
- `## Degradation Decisions`
- `## Risk Notes`
- `## Recommendation For Context Pack`

## Quality Check

Before finishing, verify:

- Core contains the likely edit targets.
- Support contains direct dependencies.
- Peripheral preserves broad risk without source bloat.
- No important dependency was silently dropped.
- The result can fit the selected model context.
- The next step is clear for `context-pack`.

## Stop Rules

Stop and ask for reslicing if:

- more than 3 core files are truly needed for a 32k task
- support context is too large to summarize safely
- peripheral impact includes public API or security behavior
- the task mixes unrelated modules
- the model would need to edit files outside the allowed scope