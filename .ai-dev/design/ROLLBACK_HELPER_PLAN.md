# Rollback Helper Plan

## Purpose

Plan a safe rollback helper for context-bounded tasks.

## Goal

Provide user-facing rollback guidance without automatically destroying work.

## Non-Goals

- no automatic `git reset`
- no silent file deletion
- no automatic revert without user confirmation

## Proposed Behavior

The helper should inspect git state and recommend:

- unstaged rollback commands
- staged rollback commands
- commit revert commands
- patch/checkpoint option for uncertain work

## Safety

Commands should be printed, not executed, in v1.
