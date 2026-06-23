# Workflow Task Alignment

## Purpose

This document is the canonical task-route agreement for the context-bounded workflow branch.

Do not create a second task route unless this document is explicitly updated first.

## Single Source Of Truth

Use these generation scripts as the active route:

- `generate_task_000_025_files.sh`
- `generate_task_026_030_files.sh`
- `generate_task_031_035_files.sh`
- `generate_task_036_040_files.sh`
- `generate_task_041_045_files.sh`
- `generate_task_046_050_files.sh`
- `run_stable_workflow_setup.sh`
- `run_task_021_026_stable.sh`

Do not use `generate_task_027_030_files.sh`. It overlaps with `generate_task_026_030_files.sh` and is considered deprecated.

## Task Type Rules

Not every task creates the same type of artifact.

### Scaffold / Skill / Design Tasks

Committed files may be created under:

- `.ai-dev/skills/`
- `.ai-dev/templates/`
- `.ai-dev/design/`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/PROJECT_MAP.md`
- `.ai-dev/CODEGRAPH.md`
- `.ai-dev/TESTING.md`

### Runtime Execution Artifacts

These are local-only by default and should not be committed unless explicitly requested:

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`

### Product Implementation Tasks

Committed product changes belong in:

- `src/`
- `tests/`
- user-facing docs when needed

Product implementation tasks must include targeted tests.

## Command Surface Decision

Current v1 product commands are REPL slash commands, matching the existing `/workflow-status` implementation.

Use these names for current implementation tasks:

- `/workflow-status`
- `/workflow-init`
- `/workflow-doctor`
- `/codeintel-status`
- `/codeintel-query`

External commands such as `cc-mini workflow status` may be considered future aliases, but they are not the current v1 acceptance target.

## Canonical Route

Completed:

- Task 000-020: scaffold, skills, templates, initial workflow design
- Task 021-026: first real workflow closeout and `/workflow-status`

Current alignment:

- Task 026-030: design and route planning, not product implementation

Next implementation route:

- Task 031: workflow init core
- Task 032: workflow init command
- Task 033: workflow doctor core
- Task 034: workflow doctor command
- Task 035: CodeIntel provider core
- Task 036: CodeIntel commands

Then:

- Task 037: test selector core
- Task 038: workflow test command
- Task 039: review packet builder
- Task 040: worklog generator
- Task 041: rollback helper
- Task 042: workflow next state

Final convergence:

- Task 043: wiki_strict boundary review
- Task 044: prompt minimization review
- Task 045: workflow docs update
- Task 046: migration guide
- Task 047: config defaults review
- Task 048: end-to-end dry run
- Task 049: final review
- Task 050: merge plan

## Scope Locks

### Workflow Init v1

Allowed:

- create missing workflow scaffold files
- avoid overwriting existing files
- report created and skipped paths
- stay independent of CodeGraph

Not allowed:

- task generation
- context pack generation
- test execution
- CodeGraph initialization
- git commit automation

### Workflow Doctor v1

Allowed:

- read-only diagnostics
- required workflow file checks
- local artifact tracked/staged checks
- simple Markdown code fence checks
- CodeGraph availability warning

Not allowed in v1:

- automatic fixes
- automatic secret removal
- CodeGraph database inspection
- expensive scans
- file mutation

### CodeIntel Provider v1

Allowed:

- detect CodeGraph availability
- run compact status/query operations
- fall back to precise `rg`
- handle timeout and command failure

Not allowed in v1:

- full MCP client
- daemon management
- automatic context pack generation
- automatic test selection

### Context Pack Generator

Keep as design until after Task 035/036.

Do not implement context pack generation before the CodeIntel provider exists.

## Review Rule

Before starting each implementation task:

1. Read this alignment file.
2. Read the relevant design file.
3. Create or use only the current task card/template.
4. Modify only the allowed product files.
5. Run targeted tests.
6. Run closeout before commit.
