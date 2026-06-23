# Workflow Smoke Review Execution: task-021

## Goal

Verify that the workflow scaffold is complete, clean, ignored correctly, and ready for real dry-run use.

## Commands

```bash
git status --short
find .ai-dev -maxdepth 3 -type f | sort
git diff --check
git check-ignore .ai-dev/tasks/example.md
git check-ignore .ai-dev/context-packs/example.md
git check-ignore .ai-dev/worklogs/example.md
git check-ignore .ai-dev/checkpoints/example.md
git check-ignore .ai-dev/tmp/example.md
git check-ignore .codegraph/example.db
git check-ignore .codebase-memory/example.db
```

## Decision
pass / pass-with-minor-fixes / fix-before-use / blocked
