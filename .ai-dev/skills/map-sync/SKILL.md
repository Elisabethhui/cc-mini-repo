---
name: map-sync
description: Use after implementation and before test selection or the next subtask to ensure local code intelligence maps are synced with latest file changes.
---

# Map Sync

## Purpose

Ensure the code intelligence map reflects current working tree after code changes.

## Workflow Position

Run after implementation and before test-gate, review-rollback, next subtask, affected test selection, or impact analysis.

## Freshness States

- fresh
- probably-fresh
- stale
- unavailable
- unknown

Only fresh or probably-fresh may proceed to CodeGraph-based affected test selection.

## Commands

```bash
git diff --name-only
codegraph status
codegraph sync
codegraph status
git diff --name-only | codegraph affected --stdin --quiet
```
