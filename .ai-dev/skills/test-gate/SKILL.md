---
name: test-gate
description: Use after implementation or before review to select and run the smallest useful verification for a context-bounded coding task.
---

# Test Gate

## Purpose

Verify one task with the smallest useful test set.

## Test Selection Order

1. Existing unit test directly covering the changed file or symbol.
2. Affected tests from CodeGraph.
3. Nearby tests in the same feature area.
4. Targeted smoke test.
5. Broader test file.
6. Full suite only when necessary.

## Verification Levels

- none
- manual
- smoke
- unit
- integration
- full

Prefer at least `unit` for logic changes.

## Failure Handling

Classify failures as task-related, pre-existing, environment/dependency, flaky/timeout, or unclear.

Stop after two failed focused fixes.
