# Merge Plan

## Purpose

Prepare the feature branch for merge after final review.

## Pre-Merge Checklist

- working tree clean
- tests pass or failures documented
- workflow docs are accurate
- no local artifacts committed
- no secrets
- branch history is understandable

## Merge Strategy

Prefer normal merge or PR review.

Avoid squash only if preserving task-level history is useful.

## Post-Merge

- run workflow status
- run workflow doctor
- update CodeGraph index locally
- remove stale local task artifacts if desired
