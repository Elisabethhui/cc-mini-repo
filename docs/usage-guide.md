# cc-mini Usage Guide

This guide describes how to use the context-bounded workflow features after installation.

## 1. Start The CLI

Preferred:

```bash
cc-mini
```

Fallback:

```bash
PYTHONPATH=src python -m core.main
```

## 2. Basic Health Checks

Inside the REPL:

```text
/workflow-status
/workflow-doctor
/model-health
```

Use these before serious coding work.

## 3. Existing Repository Workflow

Use this when code already exists.

### Step 1: Initialize

```text
/workflow-init
/workflow-doctor
```

### Step 2: Check Code Intelligence

```text
/codeintel-status
/codeintel-query auth
```

If CodeGraph is installed, sync it after code changes:

```bash
codegraph sync || true
codegraph status || true
```

### Step 3: Build Context Pack

```text
/workflow-pack "add validation to the login flow"
```

This writes a local context pack under:

```text
.ai-dev/context-packs/
```

Do not commit generated context packs.

### Step 4: Dry Run

```text
/workflow-run --dry-run "add validation to the login flow"
```

Dry run should show:

- run id
- next action
- budget report
- warnings
- context pack path

### Step 5: Supervised Execution

Only after reviewing dry-run output:

```text
/workflow-run "add validation to the login flow"
```

Supervised execution should:

- use context packs
- respect budget checks
- write runtime state
- not auto-commit
- respect permission checks

### Step 6: Test Gate

```text
/workflow-test
```

This recommends tests. It should not run tests automatically.

Run the recommended tests manually.

### Step 7: Resume If Needed

```text
/workflow-resume <run-id>
```

Use this when the run was interrupted or blocked.

## 4. Empty Repository Workflow

Use this when code does not exist yet.

### Step 1: Initialize

```text
/workflow-init
```

### Step 2: Create PlanGraph

```text
/plan-init "build a small CLI app for managing notes"
```

### Step 3: Inspect Plan

```text
/plan-status
/plan-export
```

### Step 4: Build Context Pack

```text
/workflow-pack "create the first minimal CLI skeleton"
```

### Step 5: Dry Run

```text
/workflow-run --dry-run "create the first minimal CLI skeleton"
```

## 5. Command Summary

### Workflow Setup

```text
/workflow-status
/workflow-init
/workflow-doctor
```

### Model / Runtime

```text
/model-health
```

### Code Intelligence

```text
/codeintel-status
/codeintel-query <keyword>
```

### Planning

```text
/plan-init <goal>
/plan-status
/plan-export
```

### Context Pack

```text
/workflow-pack <goal or task-id>
```

### Execution

```text
/workflow-run --dry-run <goal>
/workflow-run <goal>
/workflow-resume <run-id>
```

### Test Recommendation

```text
/workflow-test
```

## 6. Recommended Task Size

Good task:

```text
Add `/workflow-status` command and tests.
```

Bad task:

```text
Build the whole coding agent runtime.
```

Preferred constraints:

- one behavior change
- one to three files edited
- targeted tests known
- rollback path clear
- context pack under budget

## 7. Review And Rollback

The workflow should help produce:

- review packet
- work log
- rollback suggestions
- next-state recommendation

Do not skip manual review for meaningful changes.

Before commit:

```bash
git diff --stat
git diff --check
pytest <targeted tests> -v
```

If a task fails, prefer reverting only the current task files.

Do not use destructive git commands unless you are certain.

## 8. Suggested Daily Flow

```text
1. git status --short
2. /workflow-status
3. /workflow-doctor
4. /workflow-pack "today's task"
5. /workflow-run --dry-run "today's task"
6. /workflow-run "today's task"
7. /workflow-test
8. run recommended tests
9. review diff
10. commit
```

## 9. Testing

Full non-integration suite:

```bash
pytest tests/ -v -k "not integration"
```

Targeted runtime tests:

```bash
pytest \
  tests/test_runtime_profile.py \
  tests/test_context_budget.py \
  tests/test_runtime_state.py \
  tests/test_preservation.py \
  tests/test_plan_graph.py \
  tests/test_context_pack.py \
  tests/test_batch_runner.py \
  tests/test_commands.py \
  -v
```

## 10. Operational Notes

- Keep local model variables out of committed files.
- Keep runtime artifacts ignored.
- Prefer dry runs before supervised execution.
- Use CodeGraph when available, but do not block if unavailable.
- Keep each coding task small enough for the configured context window.

