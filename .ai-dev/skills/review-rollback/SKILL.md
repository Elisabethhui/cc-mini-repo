---
name: review-rollback
description: Use after test-gate to review a task diff, classify risk, and decide whether to commit, revise, or roll back.
---

# Review Rollback

## Purpose

Review one context-bounded task before commit or rollback.

## Review Order

1. Task boundary.
2. Changed files.
3. Diff behavior.
4. Verification result.
5. Impact/risk.
6. Rollback path.
7. Commit recommendation.

## Risk Classification

- low
- medium
- high
- blocked

## Decision Rules

Recommend one of: commit, revise, rollback, reslice, or hold.

## Stop Rules

Stop if diff includes files outside task scope, tests failed or were not run for logic changes, rollback path is unclear, secrets may be present, generated/local files are staged, or behavior correctness cannot be determined.
