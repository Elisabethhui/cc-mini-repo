# Current Task: task-049

## Goal

Perform final branch review before merging context-bounded workflow work.

## Allowed Read

- git log
- git diff against base branch
- workflow files
- product code changes
- tests
- docs

## Checks

- file boundary clean
- no secrets
- no local artifacts staged
- tests pass or failures explained
- docs match implemented behavior
- CodeGraph optional
- rollback path clear

## Suggested Commands

```bash
git status --short
git log --oneline --decorate -20
git diff --stat origin/codex/phase...HEAD
git diff --check origin/codex/phase...HEAD
pytest tests/ -v -k "not integration"
```

## Decision

merge / revise / hold / rollback
