# State Router Design

## Purpose

Design a future AI-assisted state router for the context-bounded workflow.

The router should help decide the next workflow step without making the system fully autonomous.

## Current Mode

The current workflow is human-driven and AI-assisted.

Human decides:

- branch
- task approval
- edits
- test execution
- commit
- rollback
- merge

AI assists with:

- task slicing
- surface search
- code intelligence summaries
- context packing
- test selection
- review packets
- work logs

## Future Mode

Future mode may add an AI-assisted state router.

The router recommends the next step based on workflow state.

It should not silently write, commit, delete, or rollback.

## Workflow States

Suggested states:

- `no_goal`
- `needs_macro_plan`
- `needs_task_slice`
- `needs_surface_search`
- `needs_code_intel`
- `needs_context_pack`
- `ready_to_implement`
- `implementation_done`
- `needs_map_sync`
- `needs_test_gate`
- `needs_fresh_review`
- `needs_review_decision`
- `needs_work_log`
- `ready_to_commit`
- `blocked`
- `done`

## State Transitions

Basic transition rules:

- no clear goal -> macro planning or user clarification
- large goal -> macro planning
- clear small goal -> task slicing
- no anchor -> surface search
- anchor found -> code intel
- code intel complete -> context pack
- context pack complete -> implementation
- product code changed -> map sync
- map fresh -> test gate
- tests complete -> fresh review or review rollback
- review decision commit -> work log then commit
- review decision revise -> implementation
- review decision rollback -> rollback
- review decision reslice -> task slicing
- review decision hold -> user decision

## Router Inputs

The router may inspect:

- current task
- macro plan
- context pack
- git status
- changed files
- map sync status
- test gate result
- review result
- work log presence
- user instruction

## Router Outputs

The router should output:

- current state
- missing artifact
- next recommended step
- required user decision
- risk
- stop condition

## Safety Rules

The router must not:

- auto-commit
- auto-delete
- auto-rollback
- hide failed tests
- continue after secret detection
- continue with stale map for affected test selection
- expand scope without user confirmation

## Human-In-The-Loop Rules

Require user confirmation before:

- product code edits
- dependency changes
- file deletion
- broad refactor
- commit
- rollback
- modifying workflow policy
- changing ignored paths

## First Implementation

Do not implement full router first.

Recommended first implementation:

`cc-mini workflow status`

It should infer a coarse state:

- workflow missing
- workflow ready
- dirty branch
- codegraph unavailable
- local artifacts staged
- ready for task

## Later Implementation

Later add:

- `cc-mini workflow next`
- reads current artifacts
- recommends next workflow step
- prints exact command suggestions
- does not execute risky actions automatically

## Output Format

Future router output should look like:

Current State:

Next Action:

Why:

Risk:

Requires User Confirmation:

Suggested Command:

Stop Condition:

## Open Questions

- Should router state live in a file?
- Should router infer from files only?
- Should router integrate with session state?
- Should router be available as a slash command?
- Should router support multiple concurrent tasks?