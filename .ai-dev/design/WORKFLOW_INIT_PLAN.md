# Workflow Init Command Plan

## Purpose

Plan the second product command in the context-bounded workflow feature:

`/workflow-init`

This document is design-only. Do not implement from this file without creating a current task card first.

## Goal

Add a safe initializer that creates missing workflow scaffold files for a repository.

The command should help users adopt the context-bounded workflow without manually copying many files.

## Why After Status

`workflow status` is read-only and tells users what is missing.

`workflow init` is the next logical command because it can fill those missing workflow pieces.

## Non-Goals

Do not implement yet:

- task generation
- context pack generation
- CodeGraph queries
- test execution
- review automation
- commit automation
- state router
- full skill installation marketplace

## Safety Rules

`workflow init` must be conservative.

It should:

- create missing files only
- never overwrite existing files without confirmation
- print a clear summary
- update `.gitignore` only with explicit user approval
- not run model calls
- not initialize CodeGraph automatically unless user asks
- not commit changes

## Proposed User Experience

```bash
/workflow-init
```

Expected behavior:

1. Detect repository root.
2. Check existing workflow files.
3. Show missing files.
4. Ask before writing.
5. Create missing scaffold files.
6. Print next step.

Possible output:

```text
Context-Bounded Workflow Init

Missing:
  .ai-dev/WORKFLOW.md
  .ai-dev/templates/CURRENT_TASK.md
  .ai-dev/skills/task-slicer/SKILL.md

Will create missing files only.
No product code will be changed.

Next:
  Run `/workflow-status`
```

## Required Files

Initializer may create:

- `AGENTS.md`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/PROJECT_MAP.md`
- `.ai-dev/CODEGRAPH.md`
- `.ai-dev/TESTING.md`
- `.ai-dev/templates/`
- `.ai-dev/skills/`

But first version should be smaller.

Recommended v1 creates only:

- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/templates/CURRENT_TASK.md`
- `.ai-dev/templates/CONTEXT_PACK.md`
- `.ai-dev/templates/TEST_GATE.md`
- `.ai-dev/templates/REVIEW_ROLLBACK.md`
- `.ai-dev/templates/WORK_LOG.md`

Keep skill generation for later unless already bundled cleanly.

## Implementation Areas

Likely files:

- `src/core/workflow_status.py` or new `src/core/workflow_init.py`
- `src/core/commands.py`
- `tests/test_workflow_init.py`
- `tests/test_commands.py`

## Acceptance Criteria

- creates missing workflow files
- does not overwrite existing files by default
- works outside git but warns
- updates no product code
- prints created/skipped files
- has tests using temporary directories
- does not require CodeGraph

## Test Plan

Targeted tests:

```bash
pytest tests/test_workflow_init.py -v
pytest tests/test_commands.py -v
```

Test cases:

- empty temp repo creates expected files
- existing files are not overwritten
- partial scaffold creates only missing files
- missing git repo does not crash
- command output is stable enough

## Risks

- init becomes too broad
- overwrites user files
- creates too many files
- duplicates repository-specific workflow files
- conflicts with manually maintained AGENTS.md

## First Executable Task

Create a task card:

`Task 031 - workflow init core`

Keep it limited to file creation helpers and tests first.
