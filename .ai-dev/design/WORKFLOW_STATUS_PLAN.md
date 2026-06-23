# Workflow Status Implementation Plan

## Goal

Implement `cc-mini workflow status`, a read-only command that reports workflow readiness.

## Non-Goals

Do not implement init, task generation, context pack generation, CodeGraph wrapper, automatic testing, automatic review, automatic commit, or state router.

## Likely Areas

- `src/core/main.py`
- `src/core/commands.py`
- possible `src/core/workflow_status.py`
- `tests/test_workflow_status.py`
- `tests/test_commands.py`

## Acceptance Criteria

Read-only, works without CodeGraph, works when `.ai-dev/` is partially missing, does not create files, has targeted tests.
