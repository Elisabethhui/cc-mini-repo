#!/usr/bin/env bash
set -eu

# Regenerate the context-bounded development scaffold for tasks 000-025.
# Run from the repository root.

mkdir -p .ai-dev/skills/task-slicer
mkdir -p .ai-dev/skills/code-intel
mkdir -p .ai-dev/skills/context-pack
mkdir -p .ai-dev/skills/test-gate
mkdir -p .ai-dev/skills/review-rollback
mkdir -p .ai-dev/skills/work-log
mkdir -p .ai-dev/skills/workflow-runbook
mkdir -p .ai-dev/skills/workflow-smoke-review
mkdir -p .ai-dev/skills/surface-search
mkdir -p .ai-dev/skills/map-sync
mkdir -p .ai-dev/skills/context-tier-policy
mkdir -p .ai-dev/skills/fresh-review
mkdir -p .ai-dev/skills/macro-planning
mkdir -p .ai-dev/templates
mkdir -p .ai-dev/design
mkdir -p .ai-dev/tasks .ai-dev/context-packs .ai-dev/worklogs .ai-dev/checkpoints .ai-dev/tmp

ensure_gitignore_line() {
  pattern="$1"
  if [ -f .gitignore ]; then
    grep -qxF "$pattern" .gitignore || printf '%s\n' "$pattern" >> .gitignore
  else
    printf '%s\n' "$pattern" >> .gitignore
  fi
}

ensure_gitignore_line "# AI development local state"
ensure_gitignore_line ".ai-dev/tasks/"
ensure_gitignore_line ".ai-dev/context-packs/"
ensure_gitignore_line ".ai-dev/worklogs/"
ensure_gitignore_line ".ai-dev/checkpoints/"
ensure_gitignore_line ".ai-dev/tmp/"
ensure_gitignore_line "# Local code intelligence indexes"
ensure_gitignore_line ".codegraph/"
ensure_gitignore_line ".codebase-memory/"
ensure_gitignore_line "# Python cache"
ensure_gitignore_line "__pycache__/"
ensure_gitignore_line "*.py[cod]"
ensure_gitignore_line ".pytest_cache/"

cat > AGENTS.md <<'EOF'
# AGENTS.md

## Core Rule

This repository uses context-bounded development. Prefer small, verifiable, reversible changes.

## File Boundary Rules

Every new file must be classified before creation:

- product code
- committed AI workflow file
- local task state
- generated output

Committed AI workflow files belong in `AGENTS.md`, `.ai-dev/skills/`, `.ai-dev/templates/`, `.ai-dev/design/`, or approved `.ai-dev/*.md` guide files.

Local task state belongs in ignored directories:

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`

Do not commit `.codegraph/` or `.codebase-memory/`.

## Code Reading Rules

Before reading large files:

1. Check the current task.
2. Use surface-search if there is no anchor.
3. Use code intelligence if available.
4. Use `rg` for exact search.
5. Read small snippets.
6. Read whole files only when necessary.

## Implementation Rules

Before editing, identify target behavior, target files, edit scope, test command, and rollback method.

Do not make unrelated refactors.

## Verification Rules

Every task must end with one of: unit test passed, integration test passed, smoke test passed, manual verification documented, or unable to verify with reason.

## Final Check

Before finishing, run `git status --short` and confirm no local task state, cache, or generated output is staged.
EOF

cat > .ai-dev/README.md <<'EOF'
# AI Development Workspace

This directory contains AI-assisted context-bounded development workflow files.

## Committed

- `README.md`
- `WORKFLOW.md`
- `PROJECT_MAP.md`
- `CODEGRAPH.md`
- `TESTING.md`
- `skills/`
- `templates/`
- `design/`

## Not Committed

- `tasks/`
- `context-packs/`
- `worklogs/`
- `checkpoints/`
- `tmp/`

## Boundary Rule

Product code and AI development state must stay separate. Before creating any new file, classify it as product code, committed workflow file, local task state, or generated output.
EOF

cat > .ai-dev/WORKFLOW.md <<'EOF'
# Context-Bounded Development Workflow

## Goal

Make coding tasks small, code-intelligence guided, context-bounded, testable, reviewable, reversible, and recoverable.

## Workflow

1. Macro-plan large goals.
2. Slice into one small task.
3. Use surface-search to find anchors.
4. Use code-intel to inspect precise code relationships.
5. Build a context pack with context tiers.
6. Implement only the current task.
7. Run map-sync after code changes.
8. Run test-gate.
9. Run fresh-review or review-rollback.
10. Record work-log.

## Context Modes

For 32k models: one behavior per task, up to 5 read files, up to 3 edit files, prefer snippets/signatures over full files, and stop if impact radius is broad.

Larger models may widen context, but testing, review, rollback, and file boundaries remain mandatory.

## Recovery

To resume a future session, read in this order:

1. `AGENTS.md`
2. `.ai-dev/WORKFLOW.md`
3. `.ai-dev/PROJECT_MAP.md`
4. relevant local task/worklog if available
5. `git status --short`
EOF

cat > .ai-dev/skills/task-slicer/SKILL.md <<'EOF'
---
name: task-slicer
description: Split large coding goals into small, context-bounded, testable, reviewable, reversible tasks.
---

# Task Slicer

## Purpose

Turn a large development goal into small tasks that fit a limited model context.

## Default Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Process

1. Restate the goal.
2. Identify the smallest useful milestone.
3. Split the milestone into ordered tasks.
4. Define allowed read/edit files.
5. Define minimum verification.
6. Define rollback.
7. Stop before implementation.

## Task Size Rules

A task is too large if it needs more than 5 files, edits more than 3 files, mixes unrelated concerns, cannot be tested, or cannot be rolled back.

## Output Format

For each task include: goal, allowed read, allowed edit, do not do, code intelligence, acceptance, tests, rollback, dependencies, and estimated context.
EOF

cat > .ai-dev/skills/code-intel/SKILL.md <<'EOF'
---
name: code-intel
description: Use when exploring code with a strict context budget. Prefer CodeGraph and precise searches before reading source files.
---

# Code Intel

## Purpose

Reduce token usage during code exploration by querying local code intelligence before reading source files.

## File Boundary

Do not write query outputs into committed files by default. Temporary outputs belong in `.ai-dev/context-packs/`, `.ai-dev/tmp/`, or `.ai-dev/worklogs/`.

Never commit `.codegraph/`, `.codebase-memory/`, raw query dumps, or local task notes.

## Query Order

1. `codegraph status`
2. `codegraph files`
3. `codegraph query <keyword>`
4. `codegraph callers <symbol>`
5. `codegraph callees <symbol>`
6. `codegraph impact <symbol>`
7. `codegraph affected`

Use `codegraph explore "<question>"` only when narrower queries cannot locate the relevant code.

## Common Commands

```bash
codegraph status
codegraph files
codegraph query "<keyword>"
codegraph callers "<symbol>"
codegraph callees "<symbol>"
codegraph impact "<symbol>"
git diff --name-only | codegraph affected --stdin --quiet
```

## Output

Summarize results with task, queries run, relevant files, relevant symbols, callers/callees, impact, affected tests, and what still needs source read.

## Stop Rules

Stop and ask for task slicing if more than 5 files seem necessary, impact radius is broad, no clear target symbol is found, or query results conflict with repository structure.
EOF

cat > .ai-dev/skills/context-pack/SKILL.md <<'EOF'
---
name: context-pack
description: Use when preparing a minimal task-specific context package for a small-context coding model after code intelligence queries.
---

# Context Pack

## Purpose

Create a compact, task-specific packet that lets a small-context model implement one task without reading the whole codebase.

## File Boundary

Committed files are this skill and `.ai-dev/templates/CONTEXT_PACK.md`. Local outputs belong in `.ai-dev/context-packs/` and are not committed by default.

Never include secrets, API keys, raw environment values, or long logs.

## Budget Defaults

For 32k: max 5 relevant files, max 3 editable files, max 5 source snippets, max 80 lines each, and about 300-600 lines total.

## Build Process

Read the current task, summarize goal, collect code-intel results, identify relevant files/symbols, include minimum snippets, list tests, list exclusions, list blockers, then stop before implementation.

## Compression Rules

Keep paths, symbols, responsibilities, call relationships, constraints, test commands, and exact snippets only when needed.

Remove duplicate explanation, long history, raw logs, unrelated architecture commentary, raw grep dumps, secrets, and generated cache content.

## Output Format

Sections: goal, current constraints, code intelligence summary, required source snippets, allowed edits, do not touch, verification plan, rollback plan, open questions.
EOF

cat > .ai-dev/skills/test-gate/SKILL.md <<'EOF'
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
EOF

cat > .ai-dev/skills/review-rollback/SKILL.md <<'EOF'
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
EOF

cat > .ai-dev/skills/work-log/SKILL.md <<'EOF'
---
name: work-log
description: Use after review or commit to record a compact task result, verification evidence, risk, rollback point, and next step for future small-context sessions.
---

# Work Log

## Purpose

Record the outcome of one context-bounded task in compact form for future recovery.

## What To Record

- task id and goal
- files changed
- code intelligence used
- tests or verification run
- review decision
- commit or rollback point
- remaining risk
- next recommended task

Keep under 100 lines unless explicitly asked for more.
EOF

cat > .ai-dev/skills/workflow-runbook/SKILL.md <<'EOF'
---
name: workflow-runbook
description: Use when the user needs to run, explain, audit, or refine the full context-bounded development workflow.
---

# Workflow Runbook

## Purpose

Guide the full context-bounded workflow from large goal to verified, reviewable, reversible task result.

## Workflow Order

1. macro-planning
2. task-slicer
3. surface-search
4. code-intel
5. context-pack
6. implementation
7. map-sync
8. test-gate
9. fresh-review or review-rollback
10. work-log

## Clean Repository Rules

Never stage `.ai-dev/tasks/`, `.ai-dev/context-packs/`, `.ai-dev/worklogs/`, `.ai-dev/checkpoints/`, `.ai-dev/tmp/`, `.codegraph/`, `.codebase-memory/`, `__pycache__/`, or `*.pyc`.
EOF

cat > .ai-dev/skills/workflow-smoke-review/SKILL.md <<'EOF'
---
name: workflow-smoke-review
description: Use before product development to audit the context-bounded workflow scaffold for file boundary problems, malformed markdown, missing templates, ignored-path mistakes, and workflow inconsistency.
---

# Workflow Smoke Review

## Purpose

Review the context-bounded scaffold before using it for real coding tasks.

## Scope

Review only `AGENTS.md`, `.gitignore`, `.ai-dev/README.md`, `.ai-dev/WORKFLOW.md`, `.ai-dev/skills/*/SKILL.md`, `.ai-dev/templates/*.md`, and `.ai-dev/design/*.md`.

## Checks

Check file boundaries, markdown structure, workflow consistency, template coverage, secrets, generated files, and excessive wiki-like bloat.

## Decision

Return pass, pass-with-minor-fixes, fix-before-use, or blocked.
EOF

cat > .ai-dev/skills/surface-search/SKILL.md <<'EOF'
---
name: surface-search
description: Use when a coding task does not yet have a clear file, symbol, route, command, error string, or module anchor.
---

# Surface Search

## Purpose

Find initial code anchors before precise CodeGraph exploration.

## Search Order

1. Extract keywords from user goal.
2. Search exact error strings or command names with `rg`.
3. Search likely filenames or directories.
4. Use `codegraph query <keyword>` for symbol candidates.
5. Use `codegraph files` for project surface.
6. Identify 1-3 likely anchors.
7. Hand off to code-intel.

## Stop Rules

Stop if no anchor can be found, more than 3 unrelated anchors are equally likely, the task is too broad, or finding the anchor requires reading many large files.
EOF

cat > .ai-dev/skills/map-sync/SKILL.md <<'EOF'
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
EOF

cat > .ai-dev/skills/context-tier-policy/SKILL.md <<'EOF'
---
name: context-tier-policy
description: Use when a task has more relevant code than the model context can safely hold. Classify context into core, support, and peripheral tiers instead of hard-dropping files.
---

# Context Tier Policy

## Purpose

Prevent context loss when a task touches more code than a small-context model can read.

## Tiers

- Core: likely edit targets; include short source snippets.
- Support: direct dependencies; include signatures, responsibilities, constraints.
- Peripheral: broad impact; include paths, symbol names, one-line responsibility, and risk note.

## Degradation Policy

Full snippet -> short snippet -> signature -> responsibility summary -> path plus risk note. Never silently drop high-risk dependencies.
EOF

cat > .ai-dev/skills/fresh-review/SKILL.md <<'EOF'
---
name: fresh-review
description: Use when reviewing a completed implementation in a fresh, isolated context to avoid context-window overflow and self-review bias.
---

# Fresh Review

## Purpose

Review completed work in a clean context instead of the noisy implementation session.

## Inputs

Use only task goal, acceptance criteria, context summary, changed files, diff stat, focused diff, test result, map-sync freshness, and rollback path.

Do not include full chat history, full raw CodeGraph output, entire source files, or repeated logs.

## Recommendation

Return commit, revise, rollback, reslice, or hold.
EOF

cat > .ai-dev/skills/macro-planning/SKILL.md <<'EOF'
---
name: macro-planning
description: Use before implementation of a complex feature or module to turn brainstorm output or a PRD into a task DAG that can be executed by small-context coding loops.
---

# Macro Planning

## Purpose

Turn a broad feature idea, brainstorm result, or PRD into an ordered set of small implementation tasks.

## Outputs

Feature goal, non-goals, assumptions, acceptance criteria, task DAG, map-sync points, validation strategy, rollback strategy, risks, and first executable task.

## Map Sync Planning

Mark map-sync after tasks that add modules, add/remove functions/classes, change imports, change commands/routes, change public interfaces, add tests, or move/rename files.
EOF

cat > .ai-dev/templates/CURRENT_TASK.md <<'EOF'
# Current Task

## Task ID
task-000

## Goal
-

## Context Budget
- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3
- max_iterations: 2

## Allowed Read
-

## Allowed Edit
-

## Do Not Do
-

## Code Intelligence Needed
- surface search:
- symbol search:
- callers:
- callees:
- impact:
- affected tests:

## Acceptance Criteria
-

## Test Plan
-

## Rollback
-
EOF

cat > .ai-dev/templates/CONTEXT_PACK.md <<'EOF'
# Context Pack: task-000

## Goal
-

## Current Constraints
- model_context:
- max_files_to_read:
- max_files_to_edit:

## Code Intelligence Summary

### Queries Run
-

### Relevant Files
-

### Relevant Symbols
-

### Callers / Callees
-

### Impact Radius
-

### Affected Tests
-

## Required Source Snippets
-

## Allowed Edits
-

## Do Not Touch
-

## Verification Plan
-

## Rollback Plan
-

## Open Questions
-
EOF

cat > .ai-dev/templates/TEST_GATE.md <<'EOF'
# Test Gate: task-000

## Changed Files
-

## Candidate Tests
-

## Selected Verification
-

## Commands Run
-

## Result
pass / fail / partial / not run

## Verification Level
none / manual / smoke / unit / integration / full

## Failures
-

## Risk
-

## Next Step
-
EOF

cat > .ai-dev/templates/REVIEW_ROLLBACK.md <<'EOF'
# Review Rollback: task-000

## Task Boundary
-

## Changed Files
-

## Diff Summary
-

## Verification Evidence
-

## Impact / Risk
low / medium / high / blocked

## Boundary Violations
-

## Rollback Path
-

## Decision
commit / revise / rollback / reslice / hold

## Follow-up
-
EOF

cat > .ai-dev/templates/WORK_LOG.md <<'EOF'
# Work Log: task-000

## Goal
-

## Changed Files
-

## Code Intelligence Used
-

## Verification
-

## Review Decision
commit / revise / rollback / reslice / hold

## Commit / Rollback Point
-

## Remaining Risk
-

## Next Task
-
EOF

cat > .ai-dev/templates/WORKFLOW_SMOKE_REVIEW.md <<'EOF'
# Workflow Smoke Review

## Files Reviewed
-

## Boundary Check
pass / fail / unclear

## Markdown Check
pass / fail / unclear

## Workflow Consistency
pass / fail / unclear

## Template Coverage
pass / fail / unclear

## Safety Findings
-

## Required Fixes
-

## Recommended Fixes
-

## Decision
pass / pass-with-minor-fixes / fix-before-use / blocked
EOF

cat > .ai-dev/templates/SURFACE_SEARCH.md <<'EOF'
# Surface Search: task-000

## User Goal
-

## Extracted Keywords
-

## Searches Run
-

## Candidate Anchors
-

## Best Anchor
-

## Why This Anchor
-

## Next Code Intel Queries
-

## Open Questions
-
EOF

cat > .ai-dev/templates/MAP_SYNC.md <<'EOF'
# Map Sync: task-000

## Changed Files
-

## Sync Needed
yes / no / unclear

## Commands Run
-

## Freshness
fresh / probably-fresh / stale / unavailable / unknown

## Affected Tests Check
-

## Fallback Used
-

## Decision
proceed-to-test-gate / use-fallback-search / stop-and-fix-sync / skip-not-needed

## Notes
-
EOF

cat > .ai-dev/templates/CONTEXT_TIER_POLICY.md <<'EOF'
# Context Tier Policy: task-000

## Task
-

## Context Budget
- model_context:
- max_core_files:
- max_support_files:
- peripheral_summary_only:

## Core Context
-

## Support Context
-

## Peripheral Context
-

## Excluded Context
-

## Degradation Decisions
-

## Risk Notes
-

## Recommendation For Context Pack
-
EOF

cat > .ai-dev/templates/FRESH_REVIEW.md <<'EOF'
# Fresh Review: task-000

## Review Packet
-

## Changed Files
-

## Diff Summary
-

## Verification Evidence
-

## Map Freshness
fresh / probably-fresh / stale / unavailable / unknown

## Findings
-

## Risk
low / medium / high / blocked

## Recommendation
commit / revise / rollback / reslice / hold

## Rollback Path
-
EOF

cat > .ai-dev/templates/MACRO_PLAN.md <<'EOF'
# Macro Plan

## Feature Goal
-

## Non-Goals
-

## Assumptions
-

## Acceptance Criteria
-

## Task DAG
-

## Map Sync Points
-

## Validation Strategy
-

## Rollback Strategy
-

## Risks
-

## First Executable Task
-
EOF

cat > .ai-dev/templates/DRY_RUN.md <<'EOF'
# Dry Run: task-000

## Purpose

Use this file to run a read-only workflow test before modifying product code.

## User Goal
-

## Task Slice
-

## Surface Search
-

## Code Intel
-

## Context Pack
-

## Map Sync Decision
-

## Test Gate
-

## Review
-

## Work Log
-

## Dry Run Result
pass / pass-with-fixes / failed / blocked
EOF

cat > .ai-dev/PROJECT_MAP.md <<'EOF'
# Project Map

## Purpose

Compact navigation map for cc-mini. This is not a full wiki.

## Repository Shape

- `src/core/` product source
- `tests/` test suite
- `docs/` durable docs
- `assets/` static assets
- `pyproject.toml` package metadata
- `install.sh` installer
- `AGENTS.md` agent rules
- `.ai-dev/` context-bounded workflow files

## Main Anchors

- CLI/REPL: `src/core/main.py`
- Engine/tool loop: `src/core/engine.py`
- Provider abstraction: `src/core/llm.py`
- Config: `src/core/config.py`
- Commands: `src/core/commands.py`
- Tools: `src/core/tools/`
- Permissions: `src/core/permissions.py`
- Sandbox: `src/core/sandbox/`
- Session: `src/core/session.py`
- Memory: `src/core/memory.py`
- Token budget: `src/core/token_budget.py`
- Compact: `src/core/compact.py`
- Skills: `src/core/skills.py`, `src/core/skills_bundled.py`
- Wiki strict: `src/core/wiki/`, `src/core/knowledge/`

## Risk Areas

High-risk areas include `main.py`, `engine.py`, `llm.py`, `permissions.py`, `sandbox/`, `token_budget.py`, `compact.py`, `session.py`, `memory.py`, `wiki/`, and `tools/`.

## Starting Anchors

- CLI command changes: `src/core/main.py`, `src/core/commands.py`, `tests/test_main.py`, `tests/test_commands.py`
- Tool changes: `src/core/tools/`, `src/core/permissions.py`, `tests/test_tools.py`
- Token/context: `src/core/token_budget.py`, `src/core/context.py`, `src/core/compact.py`, `src/core/dehydration.py`
- Wiki strict: `src/core/wiki/`, `src/core/knowledge/`, `tests/test_wiki_phase*.py`
EOF

cat > .ai-dev/CODEGRAPH.md <<'EOF'
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
EOF

cat > .ai-dev/TESTING.md <<'EOF'
# Testing Registry

## Principle

Run the smallest useful verification first.

## Main Commands

```bash
pytest tests/ -v
pytest tests/ -v -k "not integration"
pytest tests/test_engine.py -v
pytest tests/test_engine.py::test_name -v
pytest tests/core/ -v
```

## Smoke

```bash
PYTHONPATH=src python -m core.main --help
PYTHONPATH=src python -c "import core; print('ok')"
```

## Mapping

- `src/core/engine.py` -> `tests/test_engine.py`
- `src/core/config.py` -> `tests/test_config.py`
- `src/core/context.py` -> `tests/test_context.py`
- `src/core/commands.py` -> `tests/test_commands.py`
- `src/core/permissions.py` -> `tests/test_permissions.py`
- `src/core/skills.py` -> `tests/test_skills.py`
- `src/core/token_budget.py` -> `tests/core/test_token_budget.py`
- `src/core/wiki/` -> `tests/test_wiki_phase1.py`, `tests/test_wiki_phase3.py`, `tests/test_wiki_phase6.py`
EOF

cat > .ai-dev/design/WORKFLOW_COMMANDS.md <<'EOF'
# Workflow Command Design

## Goal

Design `cc-mini workflow` commands.

## Proposed Commands

- `cc-mini workflow status`
- `cc-mini workflow init`
- `cc-mini workflow doctor`
- `cc-mini workflow task new`
- `cc-mini workflow surface`
- `cc-mini workflow code-intel`
- `cc-mini workflow pack`
- `cc-mini workflow sync`
- `cc-mini workflow test`
- `cc-mini workflow review`
- `cc-mini workflow log`

## First Implementation Target

Implement `cc-mini workflow status` first because it is read-only, low risk, and validates file boundaries.
EOF

cat > .ai-dev/design/CODEINTEL_PROVIDER.md <<'EOF'
# CodeIntel Provider Design

## Goal

Avoid binding cc-mini to one code intelligence tool.

## Provider Interface

- available
- status
- sync
- files
- query
- callers
- callees
- impact
- affected_tests
- snippet

## Provider Priority

1. CodeGraph
2. Codebase-Memory-MCP
3. rg fallback
4. manual file read fallback
EOF

cat > .ai-dev/design/ARTIFACT_POLICY.md <<'EOF'
# Artifact Policy

## Classes

- Product code: committed.
- Committed workflow files: committed.
- Local task artifacts: ignored.
- Local code intelligence indexes: ignored.
- Generated/cache files: ignored.

## Commit Rules

Do not commit `.ai-dev/tasks/`, `.ai-dev/context-packs/`, `.ai-dev/worklogs/`, `.ai-dev/checkpoints/`, `.ai-dev/tmp/`, `.codegraph/`, `.codebase-memory/`, cache files, raw logs, or secrets.
EOF

cat > .ai-dev/design/STATE_ROUTER.md <<'EOF'
# State Router Design

## Current Mode

Human-driven and AI-assisted.

## Future Mode

AI-assisted router recommends next step but does not silently write, commit, delete, or rollback.

## States

no_goal, needs_macro_plan, needs_task_slice, needs_surface_search, needs_code_intel, needs_context_pack, ready_to_implement, implementation_done, needs_map_sync, needs_test_gate, needs_fresh_review, needs_review_decision, needs_work_log, ready_to_commit, blocked, done.
EOF

cat > .ai-dev/templates/WORKFLOW_SMOKE_REVIEW_EXECUTION.md <<'EOF'
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
EOF

cat > .ai-dev/templates/FIRST_DRY_RUN_EXECUTION.md <<'EOF'
# First Dry Run Execution: task-022

## Dry Run Goal

Use the workflow to answer this read-only question:

"How would cc-mini implement a read-only `workflow status` command?"

## Rules

Do not edit product code.

## Steps

macro-planning, task-slicing, surface-search, code-intel, context-pack, map-sync decision, test-gate planning, fresh-review, work-log.
EOF

cat > .ai-dev/design/WORKFLOW_STATUS_PLAN.md <<'EOF'
# Workflow Status Implementation Plan

## Goal

Implement `cc-mini workflow status`, a read-only command that reports workflow readiness.

## Non-Goals

Do not implement init, task generation, context pack generation, CodeGraph wrapper, automatic testing, automatic review, automatic commit, or state router.

## Likely Areas

- `src/core/main.py`
- `src/core/commands.py`
- possible `src/core/workflow_status.py`
- `tests/test_workflow_status.py`
- `tests/test_commands.py`

## Acceptance Criteria

Read-only, works without CodeGraph, works when `.ai-dev/` is partially missing, does not create files, has targeted tests.
EOF

cat > .ai-dev/templates/TASK_024_WORKFLOW_STATUS_CORE.md <<'EOF'
# Current Task: task-024

## Goal

Implement core read-only workflow status logic.

## Allowed Edit

- `src/core/workflow_status.py`
- `tests/test_workflow_status.py`

## Do Not Do

Do not wire full CLI unless trivial. Do not require CodeGraph. Do not modify `.ai-dev/` at runtime.

## Acceptance Criteria

Collects required files, ignored paths, CodeGraph availability, `.codegraph/` presence, git summary, warnings. Has unit tests.
EOF

cat > .ai-dev/templates/TASK_025_WORKFLOW_STATUS_COMMAND.md <<'EOF'
# Current Task: task-025

## Goal

Wire workflow status logic into command surface.

## Depends On

- task-024

## Allowed Edit

- `src/core/commands.py`
- `tests/test_commands.py`

Optional:

- `src/core/main.py`
- `tests/test_main.py`

## Acceptance Criteria

Command is reachable, readable, read-only, handles missing CodeGraph and missing `.ai-dev/`, and tests cover route.
EOF

echo "Generated task 000-025 workflow files."
echo "Next:"
echo "  git add AGENTS.md .gitignore .ai-dev"
echo "  git commit -m \"Regenerate context-bounded workflow tasks 000-025\""
