---
name: task-slicer
description: Split large coding goals into small, context-bounded, testable, reviewable, reversible tasks.
---

# Task Slicer

## Purpose

Turn a large development goal into small tasks that fit a limited model context.

## Default Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Process

1. Restate the goal.
2. Identify the smallest useful milestone.
3. Split the milestone into ordered tasks.
4. Define allowed read/edit files.
5. Define minimum verification.
6. Define rollback.
7. Stop before implementation.

## Task Size Rules

A task is too large if it needs more than 5 files, edits more than 3 files, mixes unrelated concerns, cannot be tested, or cannot be rolled back.

## Output Format

For each task include: goal, allowed read, allowed edit, do not do, code intelligence, acceptance, tests, rollback, dependencies, and estimated context.
