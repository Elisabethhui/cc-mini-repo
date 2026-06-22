---
name: review-rollback
description: Use after test-gate to review a task diff, classify risk, and decide whether to commit, revise, or roll back.
---

# Review Rollback

## Purpose

Review one context-bounded task before it is committed or rolled back.

This skill checks whether the implementation stayed inside the task boundary, whether verification is sufficient, and whether the change can be safely committed.

## File Boundary

Committed files:

- `.ai-dev/skills/review-rollback/SKILL.md`
- `.ai-dev/templates/REVIEW_ROLLBACK.md`

Local review notes belong in ignored paths:

- `.ai-dev/worklogs/`
- `.ai-dev/tmp/`

Do not commit raw review dumps unless explicitly requested.

Never include secrets, API keys, raw environment values, or huge terminal output.

## Inputs

Use these inputs when available:

- current task file
- context pack
- test gate result
- `git diff --stat`
- `git diff`
- `git status --short`
- CodeGraph impact or affected test results
- known rollback point

## Review Order

Review in this order:

1. Task boundary.
2. Changed files.
3. Diff behavior.
4. Verification result.
5. Impact/risk.
6. Rollback path.
7. Commit recommendation.

Do not review the whole repository.

## Common Commands

```bash
git status --short
git diff --stat
git diff
git diff --name-only
git diff --name-only | codegraph affected --stdin --quiet
```

If a commit already exists for the task:

```bash
git show --stat --oneline HEAD
git show --name-only HEAD
```

## Boundary Check

Confirm:

- changed files are allowed by the task
- no generated or local task files are staged
- no unrelated formatting churn
- no broad refactor hidden inside the diff
- no secrets or environment values were added
- no `.codegraph/`, `.codebase-memory/`, `.ai-dev/tasks/`, `.ai-dev/context-packs/`, `.ai-dev/worklogs/`, `.ai-dev/tmp/` files are staged

## Risk Classification

Classify risk as one of:

- `low`: small, tested, limited files, obvious rollback
- `medium`: multiple files or partial verification, but scope is clear
- `high`: broad impact, weak tests, public API behavior, config/security changes
- `blocked`: unsafe to commit without more information or user decision

## Decision Rules

Recommend one of:

- `commit`: task is complete, tested enough, and risk is acceptable
- `revise`: small focused fix is needed inside the same task boundary
- `rollback`: change is wrong, too broad, or unsafe
- `reslice`: task is too large or unclear
- `hold`: user decision required

## Rollback Rules

Before commit:

- rollback with `git restore <files>` for task files
- rollback staging with `git restore --staged <files>`

After commit:

- rollback with `git revert <commit>`

For uncertain work:

- create a patch or checkpoint before continuing
- do not bury uncertainty in a final commit

## Output Format

Write the review result with these sections:

- `# Review Rollback: task-xxx`
- `## Task Boundary`
- `## Changed Files`
- `## Diff Summary`
- `## Verification Evidence`
- `## Impact / Risk`
- `## Boundary Violations`
- `## Rollback Path`
- `## Decision`
- `## Follow-up`

## Quality Check

Before finishing, verify:

- Review is based on diff, task, and test evidence.
- The decision is explicit.
- Risk is classified.
- Rollback path is concrete.
- No unrelated cleanup is being smuggled into the task.
- No ignored local state is staged.

## Stop Rules

Stop and ask for user decision if:

- diff includes files outside task scope
- tests failed or were not run for a logic change
- rollback path is unclear
- secrets may have been committed
- generated/cache/local files are staged
- review cannot determine whether behavior is correct