---
name: macro-planning
description: Use before implementation of a complex feature or module to turn brainstorm output or a PRD into a task DAG that can be executed by small-context coding loops.
---

# Macro Planning

## Purpose

Turn a broad feature idea, brainstorm result, or PRD into an ordered set of small implementation tasks.

Macro planning is the bridge between product thinking and context-bounded execution.

Use this skill before `task-slicer` when the goal is larger than a single task.

## Relationship To Other Skills

Macro planning creates the high-level feature plan.

Then:

1. `task-slicer` turns each milestone into small tasks.
2. `surface-search` finds anchors for each task.
3. `code-intel` explores precise code relationships.
4. `context-pack` prepares 32k-ready context.
5. implementation changes code.
6. `map-sync` refreshes code intelligence.
7. `test-gate` verifies each task.
8. `fresh-review` or `review-rollback` reviews results.
9. `work-log` records progress.

## File Boundary

Committed file:

- `.ai-dev/skills/macro-planning/SKILL.md`

Local planning outputs belong in ignored paths:

- `.ai-dev/tasks/`
- `.ai-dev/tmp/`

Only move planning content into committed docs if the user explicitly decides it is durable project documentation.

Never include:

- secrets
- API keys
- raw environment values
- full conversation transcripts
- huge pasted logs

## Inputs

Use these inputs when available:

- brainstorm notes
- PRD
- user goal
- project map
- known constraints
- architecture analysis
- current branch goal
- known risks
- model context budget
- test strategy

## Planning Outputs

Produce:

- feature goal
- non-goals
- assumptions
- acceptance criteria
- task DAG
- milestone order
- risk list
- validation strategy
- rollback strategy
- map-sync points

## Task DAG

Represent tasks as a dependency-aware list.

Each task should include:

- task id
- goal
- depends on
- expected files or areas
- expected output
- test expectation
- map-sync requirement
- estimated context size

Prefer DAG over a flat list when tasks depend on generated code from earlier tasks.

## Task Size Rules

Each executable task should fit the selected model mode.

For 32k:

- one behavior or one file-area change
- up to 5 read files
- up to 3 edit files
- clear test path
- clear rollback path

If a task needs more, split it.

## Map Sync Planning

Mark map-sync points explicitly.

Map sync is required after tasks that:

- add a new module
- add or remove functions/classes
- change imports
- change CLI commands
- change routes/endpoints
- change public interfaces
- add tests
- move or rename files

Do not let later tasks depend on code that has not been synced into the code intelligence map.

## Validation Planning

For each milestone, define:

- unit tests
- affected tests
- smoke tests
- manual verification if needed
- final fresh review scope

Do not wait until implementation is complete to think about tests.

## Output Format

Write macro planning output with these sections:

- `# Macro Plan`
- `## Feature Goal`
- `## Non-Goals`
- `## Assumptions`
- `## Acceptance Criteria`
- `## Task DAG`
- `## Map Sync Points`
- `## Validation Strategy`
- `## Rollback Strategy`
- `## Risks`
- `## First Executable Task`

## Task Format

Use this format inside the task DAG:

- Task ID:
- Goal:
- Depends On:
- Expected Areas:
- Expected Output:
- Test Expectation:
- Map Sync:
- Estimated Context:
- Notes:

## Quality Check

Before finishing, verify:

- The plan starts from a clear user goal.
- Non-goals prevent scope creep.
- Tasks are dependency-aware.
- Each task can be executed by the micro loop.
- Map sync points are explicit.
- Validation is planned early.
- The first task is small enough to start.

## Stop Rules

Stop and ask for clarification if:

- the goal is ambiguous
- acceptance criteria are missing
- task dependencies are unclear
- the feature requires product decisions
- the first task cannot be made small enough
- validation cannot be defined