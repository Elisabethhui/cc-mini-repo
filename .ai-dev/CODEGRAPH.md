# CodeGraph Setup

## Purpose

Use CodeGraph for low-token code exploration.

## File Boundary

Never commit `.codegraph/` or `.codebase-memory/`.

## Initialize

```bash
codegraph init
codegraph status
```

## Daily Use

```bash
codegraph status
codegraph sync
codegraph files
codegraph query "<keyword>"
codegraph callers "<symbol>"
codegraph callees "<symbol>"
codegraph impact "<symbol>"
git diff --name-only | codegraph affected --stdin --quiet
```

Use `rg` fallback when CodeGraph is unavailable.
