---
name: task-slicer
description: Split large coding goals into small, context-bounded, testable, reviewable, reversible tasks.
---

# Task Slicer

## Purpose

Turn a large development goal into small tasks that can fit a limited model context.

## Default Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Process

1. Restate the large goal.
2. Identify the smallest useful milestone.
3. Split the milestone into ordered tasks.
4. For each task, define allowed read files.
5. Define allowed edit files.
6. Define code intelligence queries.
7. Define the minimum test.
8. Define rollback method.
9. Stop before implementation.

## Task Size Rules

A task is too large if it:

- needs more than 5 files of context
- edits more than 3 files
- mixes design, implementation, and refactor
- cannot be tested
- cannot be rolled back independently

## Output Format

```markdown
### task-001: short name

Goal:
-

Allowed Read:
-

Allowed Edit:
-

Do Not Do:
-

Code Intelligence:
-

Acceptance:
-

Tests:
-

Rollback:
-

Estimated Context:
- 32k / 64k / 128k