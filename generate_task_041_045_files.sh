#!/usr/bin/env bash
set -eu

mkdir -p .ai-dev/design
mkdir -p .ai-dev/templates

cat > .ai-dev/design/ROLLBACK_HELPER_PLAN.md <<'EOF'
# Rollback Helper Plan

## Purpose

Plan a safe rollback helper for context-bounded tasks.

## Goal

Provide user-facing rollback guidance without automatically destroying work.

## Non-Goals

- no automatic `git reset`
- no silent file deletion
- no automatic revert without user confirmation

## Proposed Behavior

The helper should inspect git state and recommend:

- unstaged rollback commands
- staged rollback commands
- commit revert commands
- patch/checkpoint option for uncertain work

## Safety

Commands should be printed, not executed, in v1.
EOF

cat > .ai-dev/templates/TASK_041_ROLLBACK_HELPER.md <<'EOF'
# Current Task: task-041

## Goal

Implement a read-only rollback helper that prints safe rollback suggestions for current workflow task changes.

## Depends On

- `.ai-dev/design/ROLLBACK_HELPER_PLAN.md`
- review-rollback skill

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `.ai-dev/design/ROLLBACK_HELPER_PLAN.md`
- `src/core/commands.py`
- existing git helper patterns if any

## Allowed Edit

- `src/core/rollback_helper.py`
- `tests/test_rollback_helper.py`

Optional:

- `src/core/commands.py`
- `tests/test_commands.py`

## Do Not Do

- Do not execute destructive git commands.
- Do not delete files.
- Do not auto-revert commits.
- Do not hide dirty worktree state.

## Acceptance Criteria

- Detects unstaged/staged changes.
- Prints suggested rollback commands.
- Warns before destructive operations.
- Handles no-git case gracefully.
- Has tests.

## Test Plan

```bash
pytest tests/test_rollback_helper.py -v
```

## Rollback

```bash
git restore src/core/rollback_helper.py tests/test_rollback_helper.py
git restore src/core/commands.py tests/test_commands.py
```
EOF

cat > .ai-dev/templates/TASK_042_WORKFLOW_NEXT_STATE.md <<'EOF'
# Current Task: task-042

## Goal

Implement a read-only `workflow next` state recommendation core.

This is not full automation. It recommends the next workflow step from available artifacts and git state.

## Depends On

- `.ai-dev/design/STATE_ROUTER.md`

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `.ai-dev/design/STATE_ROUTER.md`
- `src/core/workflow_status.py`
- `src/core/workflow_doctor.py`
- `src/core/commands.py`

## Allowed Edit

- `src/core/workflow_next.py`
- `tests/test_workflow_next.py`

Optional:

- `src/core/commands.py`
- `tests/test_commands.py`

## Do Not Do

- Do not execute next step automatically.
- Do not edit files.
- Do not run tests.
- Do not commit.
- Do not rollback.

## Acceptance Criteria

- Infers coarse workflow state.
- Recommends next action.
- Prints stop condition.
- Requires user confirmation for risky actions.
- Has tests.

## Test Plan

```bash
pytest tests/test_workflow_next.py -v
```

## Rollback

```bash
git restore src/core/workflow_next.py tests/test_workflow_next.py
git restore src/core/commands.py tests/test_commands.py
```
EOF

cat > .ai-dev/design/WIKI_STRICT_REDUCTION_PLAN.md <<'EOF'
# Wiki Strict Reduction Plan

## Purpose

Decide how existing wiki_strict behavior should coexist with CodeIntel and context-bounded workflow.

## Goal

Reduce heavy wiki/document generation while preserving the useful low-context safety ideas.

## Keep

- task boundaries
- patch verification
- target identity checks
- archive/reconcile ideas if still useful
- AST/snippet reading where CodeGraph is unavailable

## Reconsider

- large generated wiki documents
- long system prompt sections
- always-on lifecycle work
- duplicated maps that CodeGraph can answer

## Replace With

- surface-search
- code-intel
- context-pack
- map-sync
- test-gate
- fresh-review

## Open Questions

- Which wiki_strict files are still product-critical?
- Which can become optional workflow helpers?
- Which are obsolete after CodeIntel provider exists?
EOF

cat > .ai-dev/templates/TASK_043_WIKI_STRICT_BOUNDARY_REVIEW.md <<'EOF'
# Current Task: task-043

## Goal

Perform a read-only boundary review of existing wiki_strict modules and decide what should be kept, reduced, or replaced by context-bounded workflow.

## Depends On

- `.ai-dev/design/WIKI_STRICT_REDUCTION_PLAN.md`

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 1

## Allowed Read

- `src/core/wiki/`
- `src/core/knowledge/`
- `src/core/flow_state.py`
- `tests/test_wiki_phase1.py`
- `tests/test_wiki_phase3.py`
- `tests/test_wiki_phase6.py`

## Allowed Edit

- `.ai-dev/design/WIKI_STRICT_REDUCTION_PLAN.md`

## Do Not Do

- Do not modify product code.
- Do not delete wiki_strict code.
- Do not change tests.

## Acceptance Criteria

- Produces keep/reduce/replace table.
- Identifies first safe replacement candidate.
- Identifies risks and tests.

## Test Plan

No product tests required. This is read-only/design.

## Rollback

```bash
git restore .ai-dev/design/WIKI_STRICT_REDUCTION_PLAN.md
```
EOF

cat > .ai-dev/design/PROMPT_MINIMIZATION_PLAN.md <<'EOF'
# Prompt Minimization Plan

## Purpose

Plan how to reduce system prompt/token overhead by moving detailed workflow behavior into skills and local files.

## Goal

Keep runtime prompts short while preserving workflow correctness.

## Strategy

- system prompt contains only router-level rules
- detailed steps live in skills
- project facts live in project map
- task specifics live in task/context pack
- logs stay local and ignored

## Risks

- model may not load skill when needed
- too many files create confusion
- critical safety rules may be hidden too deep

## Rule

Safety and file boundary rules stay visible. Long procedural detail moves into skills.
EOF

cat > .ai-dev/templates/TASK_044_PROMPT_MINIMIZATION_REVIEW.md <<'EOF'
# Current Task: task-044

## Goal

Review current prompts/instructions and identify what can be shortened or moved into skills.

## Depends On

- `.ai-dev/design/PROMPT_MINIMIZATION_PLAN.md`

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 1

## Allowed Read

- `AGENTS.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/skills/*/SKILL.md`
- `src/core/flow_state.py`
- prompt construction areas found by surface-search

## Allowed Edit

- `.ai-dev/design/PROMPT_MINIMIZATION_PLAN.md`

## Do Not Do

- Do not change runtime prompts in product code yet.
- Do not remove safety rules.
- Do not modify skills unless explicitly scoped.

## Acceptance Criteria

- Identifies prompt content categories.
- Marks what stays visible vs moves to skills.
- Proposes first implementation task.

## Test Plan

No product tests required. This is design review.
EOF

cat > .ai-dev/templates/TASK_045_WORKFLOW_DOCS_UPDATE.md <<'EOF'
# Current Task: task-045

## Goal

Update durable user-facing docs to describe context-bounded workflow after product commands exist.

This task should run later, after workflow status/init/doctor shape is stable.

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `README.md`
- `docs/`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/design/WORKFLOW_COMMANDS.md`

## Allowed Edit

- `README.md`
- selected docs under `docs/`

## Do Not Do

- Do not document features that are not implemented.
- Do not paste internal task artifacts.
- Do not expose local workflow logs.

## Acceptance Criteria

- Docs explain workflow status/init/doctor.
- Docs explain CodeGraph is optional.
- Docs explain ignored local artifacts.
- Docs are concise.

## Test Plan

Docs-only. Run smoke if docs command examples changed:

```bash
PYTHONPATH=src python -m core.main --help
```

## Rollback

```bash
git restore README.md docs
```
EOF

echo "Generated task 041-045 files."
echo "Next:"
echo "  git add .ai-dev/design/ROLLBACK_HELPER_PLAN.md"
echo "  git add .ai-dev/templates/TASK_041_ROLLBACK_HELPER.md"
echo "  git add .ai-dev/templates/TASK_042_WORKFLOW_NEXT_STATE.md"
echo "  git add .ai-dev/design/WIKI_STRICT_REDUCTION_PLAN.md"
echo "  git add .ai-dev/templates/TASK_043_WIKI_STRICT_BOUNDARY_REVIEW.md"
echo "  git add .ai-dev/design/PROMPT_MINIMIZATION_PLAN.md"
echo "  git add .ai-dev/templates/TASK_044_PROMPT_MINIMIZATION_REVIEW.md"
echo "  git add .ai-dev/templates/TASK_045_WORKFLOW_DOCS_UPDATE.md"
echo "  git commit -m \"Add rollback next state wiki strict prompt and docs tasks\""
