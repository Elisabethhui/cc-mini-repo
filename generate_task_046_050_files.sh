#!/usr/bin/env bash
set -eu

mkdir -p .ai-dev/design
mkdir -p .ai-dev/templates

cat > .ai-dev/design/MIGRATION_GUIDE_PLAN.md <<'EOF'
# Migration Guide Plan

## Purpose

Plan migration guidance from heavy wiki_strict workflows to context-bounded workflow.

## Goal

Help users understand which old artifacts are still useful and which new workflow commands replace them.

## Audience

- existing cc-mini users
- developers using local 32k models
- maintainers of workflow files

## Topics

- why context-bounded workflow exists
- what changes from wiki_strict
- how CodeGraph fits in
- how to keep files clean
- how to run status/init/doctor
- how to use task/context/test/review/log loop
EOF

cat > .ai-dev/templates/TASK_046_MIGRATION_GUIDE.md <<'EOF'
# Current Task: task-046

## Goal

Write a concise migration guide after workflow commands and wiki_strict reduction decisions are stable.

## Allowed Read

- `.ai-dev/design/MIGRATION_GUIDE_PLAN.md`
- `.ai-dev/design/WIKI_STRICT_REDUCTION_PLAN.md`
- `.ai-dev/WORKFLOW.md`
- `README.md`
- `docs/`

## Allowed Edit

- `docs/`
- `README.md` if needed

## Do Not Do

- Do not document unimplemented commands.
- Do not remove old docs without explicit review.

## Acceptance Criteria

- Explains old vs new workflow.
- Explains migration path.
- Explains ignored artifacts.
- Stays concise.

## Test Plan

Docs-only.
EOF

cat > .ai-dev/templates/TASK_047_CONFIG_DEFAULTS_REVIEW.md <<'EOF'
# Current Task: task-047

## Goal

Review workflow-related config defaults before enabling product workflow commands broadly.

## Allowed Read

- `src/core/config.py`
- `pyproject.toml`
- workflow command implementation files
- `.ai-dev/design/ARTIFACT_POLICY.md`
- `.ai-dev/design/STATE_ROUTER.md`

## Allowed Edit

- design docs first
- product config only in a later scoped implementation task

## Do Not Do

- Do not change defaults without user approval.
- Do not enable automatic writes by default.
- Do not require CodeGraph by default.

## Acceptance Criteria

- Defines safe defaults.
- Confirms CodeGraph is optional.
- Confirms workflow commands are explicit.
- Identifies any config changes needed.

## Test Plan

Design review only unless product config changes are explicitly approved.
EOF

cat > .ai-dev/templates/TASK_048_END_TO_END_DRY_RUN.md <<'EOF'
# Current Task: task-048

## Goal

Run an end-to-end dry run of the implemented workflow commands on a small safe task.

## Rules

Prefer a docs-only or read-only task first.

Do not run broad automation.

## Steps

1. `workflow status`
2. `workflow doctor`
3. task slice
4. surface search
5. code-intel
6. context pack
7. implementation if approved
8. map sync
9. test gate
10. fresh review
11. work log

## Evidence To Collect

- commands run
- changed files
- tests run
- review decision
- rollback path

## Acceptance Criteria

- workflow is understandable
- no local artifacts staged
- tests selected correctly
- review packet stays small
- work log can resume next session
EOF

cat > .ai-dev/templates/TASK_049_FINAL_REVIEW.md <<'EOF'
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
EOF

cat > .ai-dev/design/MERGE_PLAN.md <<'EOF'
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
EOF

cat > .ai-dev/templates/TASK_050_MERGE_PLAN.md <<'EOF'
# Current Task: task-050

## Goal

Prepare merge of the context-bounded workflow branch.

## Allowed Read

- `.ai-dev/design/MERGE_PLAN.md`
- git status/log/diff
- test results
- final review result

## Allowed Edit

- `.ai-dev/design/MERGE_PLAN.md`
- release/PR notes if needed

## Do Not Do

- Do not merge with dirty working tree.
- Do not merge with unexplained failing tests.
- Do not include local artifacts.

## Acceptance Criteria

- Merge plan is clear.
- Risks are documented.
- Next post-merge actions are listed.
EOF

echo "Generated task 046-050 files."
echo "Next:"
echo "  git add .ai-dev/design/MIGRATION_GUIDE_PLAN.md"
echo "  git add .ai-dev/templates/TASK_046_MIGRATION_GUIDE.md"
echo "  git add .ai-dev/templates/TASK_047_CONFIG_DEFAULTS_REVIEW.md"
echo "  git add .ai-dev/templates/TASK_048_END_TO_END_DRY_RUN.md"
echo "  git add .ai-dev/templates/TASK_049_FINAL_REVIEW.md"
echo "  git add .ai-dev/design/MERGE_PLAN.md"
echo "  git add .ai-dev/templates/TASK_050_MERGE_PLAN.md"
echo "  git commit -m \"Add migration config e2e final review and merge tasks\""
