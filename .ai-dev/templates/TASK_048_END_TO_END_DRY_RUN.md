# Current Task: task-048

## Goal

Run an end-to-end dry run of the implemented workflow commands on a small safe task.

## Rules

Prefer a docs-only or read-only task first.

Do not run broad automation.

## Steps

1. `workflow status`
2. `workflow doctor`
3. task slice
4. surface search
5. code-intel
6. context pack
7. implementation if approved
8. map sync
9. test gate
10. fresh review
11. work log

## Evidence To Collect

- commands run
- changed files
- tests run
- review decision
- rollback path

## Acceptance Criteria

- workflow is understandable
- no local artifacts staged
- tests selected correctly
- review packet stays small
- work log can resume next session
