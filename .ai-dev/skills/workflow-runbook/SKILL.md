---
name: workflow-runbook
description: Use when the user needs to run, explain, audit, or refine the full context-bounded development workflow.
---

# Workflow Runbook

## Purpose

Guide the full context-bounded workflow from large goal to verified, reviewable, reversible task result.

## Workflow Order

1. macro-planning
2. task-slicer
3. surface-search
4. code-intel
5. context-pack
6. implementation
7. map-sync
8. test-gate
9. fresh-review or review-rollback
10. work-log

## Clean Repository Rules

Never stage `.ai-dev/tasks/`, `.ai-dev/context-packs/`, `.ai-dev/worklogs/`, `.ai-dev/checkpoints/`, `.ai-dev/tmp/`, `.codegraph/`, `.codebase-memory/`, `__pycache__/`, or `*.pyc`.
