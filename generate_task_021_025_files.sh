#!/usr/bin/env bash
set -eu

mkdir -p .ai-dev/design
mkdir -p .ai-dev/templates
mkdir -p .ai-dev/tasks
mkdir -p .ai-dev/worklogs

cat > .ai-dev/templates/WORKFLOW_SMOKE_REVIEW_EXECUTION.md <<'EOF'
# Workflow Smoke Review Execution: task-021

## Purpose

Execute a real smoke review of the context-bounded workflow scaffold.

This is a read-only workflow validation task.

## Goal

Verify that the workflow scaffold is complete, clean, ignored correctly, and ready for real dry-run use.

## Allowed Read

- `AGENTS.md`
- `.gitignore`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/PROJECT_MAP.md`
- `.ai-dev/CODEGRAPH.md`
- `.ai-dev/TESTING.md`
- `.ai-dev/skills/*/SKILL.md`
- `.ai-dev/templates/*.md`
- `.ai-dev/design/*.md`

## Allowed Edit

Only if fixes are required:

- `AGENTS.md`
- `.gitignore`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/skills/*/SKILL.md`
- `.ai-dev/templates/*.md`
- `.ai-dev/design/*.md`

## Do Not Do

- Do not edit `src/`
- Do not edit `tests/`
- Do not add product behavior
- Do not run product implementation
- Do not commit local task artifacts

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

## Checks

### File Boundary

- [ ] committed workflow files are in approved locations
- [ ] ignored local task paths are ignored
- [ ] CodeGraph indexes are ignored
- [ ] generated/cache files are ignored
- [ ] no local task artifacts are staged

### Markdown

- [ ] each `SKILL.md` has frontmatter
- [ ] code fences are closed
- [ ] headings are readable
- [ ] no pasted command output is inside a code block by accident

### Workflow

- [ ] macro-planning exists
- [ ] task-slicer exists
- [ ] surface-search exists
- [ ] code-intel exists
- [ ] context-pack exists
- [ ] map-sync exists
- [ ] test-gate exists
- [ ] fresh-review/review-rollback exist
- [ ] work-log exists

### Safety

- [ ] no secrets
- [ ] no API keys
- [ ] no raw environment values
- [ ] no `.codegraph/`
- [ ] no `.codebase-memory/`

## Result

pass / pass-with-minor-fixes / fix-before-use / blocked

## Required Fixes

-

## Recommended Fixes

-

## Decision

-
EOF

cat > .ai-dev/templates/FIRST_DRY_RUN_EXECUTION.md <<'EOF'
# First Dry Run Execution: task-022

## Purpose

Run the full context-bounded workflow on a read-only task before editing product code.

This verifies that the process is understandable and usable end to end.

## Dry Run Goal

Use the workflow to answer this read-only question:

"How would cc-mini implement a read-only `workflow status` command?"

## Rules

This task must not edit product code.

Allowed outputs:

- local task note under `.ai-dev/tasks/`
- local context pack under `.ai-dev/context-packs/`
- local work log under `.ai-dev/worklogs/`

These outputs are ignored and should not be committed.

## Step 1: Macro Planning

Question:

What product capability is being explored?

Expected output:

- feature goal
- non-goals
- first executable task

## Step 2: Task Slicing

Create one small task:

Task ID:

Goal:

Allowed Read:

Allowed Edit:

Acceptance:

Rollback:

## Step 3: Surface Search

Extract keywords:

-

Run searches:

```bash
rg -n "workflow|status|commands|argparse|slash"
codegraph query "workflow"
codegraph query "status"
codegraph query "commands"
```

Candidate anchors:

-

Best anchor:

-

## Step 4: Code Intel

Run targeted queries:

```bash
codegraph status
codegraph query "commands"
codegraph query "main"
codegraph query "argparse"
```

Optional:

```bash
codegraph callers "<symbol>"
codegraph callees "<symbol>"
```

Relevant files:

-

Relevant symbols:

-

## Step 5: Context Pack

Context Tier:

Core Context:

Support Context:

Peripheral Context:

Excluded Context:

## Step 6: Map Sync Decision

Since no product code is changed:

Sync needed:

no

Decision:

skip-not-needed

## Step 7: Test Gate Planning

Candidate tests for future implementation:

-

Selected likely verification:

-

## Step 8: Fresh Review

Review whether the dry run identified:

- likely implementation files
- likely tests
- clear next implementation task
- risks

Decision:

pass / revise / reslice / hold

## Step 9: Work Log

Summary:

-

Next task:

-

## Dry Run Result

pass / pass-with-fixes / failed / blocked
EOF

cat > .ai-dev/design/WORKFLOW_STATUS_PLAN.md <<'EOF'
# Workflow Status Implementation Plan

## Purpose

Plan the first product implementation task for the context-bounded workflow feature.

Target command:

`cc-mini workflow status`

## Goal

Implement a read-only workflow status command that helps users understand whether their repository is ready to use the context-bounded development workflow.

## Why This First

This is the safest first product feature because it:

- is read-only
- does not require model calls
- does not require CodeGraph to be installed
- validates file boundaries
- gives immediate user value
- creates a foundation for later workflow commands

## Non-Goals

Do not implement yet:

- workflow init
- task generation
- context pack generation
- CodeGraph query wrapper
- automatic testing
- automatic review
- automatic commit
- state router
- background daemon management

## Expected User Experience

Example command:

```bash
cc-mini workflow status
```

Expected output shape:

```text
Context-Bounded Workflow Status

Branch:
  feature/context-bounded-dev-bootstrap

Workflow files:
  OK AGENTS.md
  OK .ai-dev/WORKFLOW.md
  OK .ai-dev/skills/
  OK .ai-dev/templates/

Local artifact ignores:
  OK .ai-dev/tasks/
  OK .ai-dev/context-packs/
  OK .ai-dev/worklogs/
  OK .codegraph/

CodeGraph:
  installed / not installed
  initialized / not initialized

Git:
  clean / dirty
  staged local artifacts: none / found

Next:
  Run task-slicer or initialize CodeGraph
```

## Likely Implementation Areas

Use surface-search and CodeGraph to confirm.

Likely files:

- `src/core/main.py`
- `src/core/commands.py`
- maybe new file: `src/core/workflow_status.py`
- tests under `tests/`

## Design Preference

Prefer a small new module:

```text
src/core/workflow_status.py
```

Why:

- keeps status logic separate
- easier to test
- avoids bloating `main.py`
- allows later reuse by slash commands or CLI commands

## Proposed Internal Functions

Possible functions:

```python
def collect_workflow_status(root: Path) -> WorkflowStatus:
    ...

def format_workflow_status(status: WorkflowStatus) -> str:
    ...

def check_required_files(root: Path) -> list[CheckResult]:
    ...

def check_ignored_paths(root: Path) -> list[CheckResult]:
    ...

def check_codegraph(root: Path) -> CodeGraphCheck:
    ...

def check_git_state(root: Path) -> GitCheck:
    ...
```

Keep implementation smaller if possible.

## Required Checks

### Required Files

- `AGENTS.md`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/skills/`
- `.ai-dev/templates/`

### Ignored Local Paths

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`
- `.codegraph/`
- `.codebase-memory/`

### CodeGraph

Check:

- whether `codegraph` command exists
- whether `.codegraph/` exists

Do not fail if CodeGraph is unavailable.

### Git

Check:

- `git status --short`
- whether ignored local artifact paths appear staged or modified
- whether pycache or generated files appear

## Acceptance Criteria

- `cc-mini workflow status` prints a readable status report.
- The command is read-only.
- It works when CodeGraph is not installed.
- It works when `.ai-dev/` is partially missing.
- It does not create files.
- It does not modify git state.
- It has targeted tests.

## Test Plan

Likely tests:

- status detects required files
- status detects missing files
- status detects ignored path configuration
- status handles CodeGraph missing
- status formatting is stable
- command route invokes status logic

Possible test files:

- `tests/test_workflow_status.py`
- `tests/test_commands.py`
- `tests/test_main.py`

## Risks

- CLI routing may be more complex than expected.
- Existing command system may not support nested commands cleanly.
- Checking git may make tests environment-dependent.
- CodeGraph detection should not make tests flaky.
- Formatting should be stable but not over-specified.

## First Executable Product Task

Implement a pure read-only status module with tests, without wiring CLI yet.

Suggested next task:

`task-024 implement workflow status core module`

## Map Sync Points

Map sync required after product code is added.

After task-024 implementation:

```bash
codegraph sync
codegraph status
```

## Review Strategy

Use fresh review with:

- task goal
- changed files
- tests run
- diff stat
- focused diff
- rollback path
EOF

cat > .ai-dev/templates/TASK_024_WORKFLOW_STATUS_CORE.md <<'EOF'
# Current Task: task-024

## Goal

Implement the core read-only workflow status logic for `cc-mini workflow status`.

This task should add a small, testable module but should not wire the full CLI command unless the codebase clearly makes that trivial.

## Why

The workflow status command is the safest first product feature for the context-bounded workflow system.

It validates the local workflow scaffold without modifying files.

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3
- max_iterations: 2

## Allowed Read

Start with:

- `src/core/commands.py`
- `src/core/main.py`
- `pyproject.toml`
- `tests/test_commands.py`
- `tests/test_main.py`

Use CodeGraph/surface-search to adjust if needed.

## Allowed Edit

Preferred:

- `src/core/workflow_status.py`
- `tests/test_workflow_status.py`

Optional only if needed:

- `src/core/commands.py`

Do not edit `src/core/main.py` unless CLI wiring is intentionally included in this task.

## Do Not Do

- Do not implement workflow init.
- Do not generate task files.
- Do not call LLM APIs.
- Do not require CodeGraph to be installed.
- Do not modify `.ai-dev/` at runtime.
- Do not auto-fix `.gitignore`.
- Do not commit local artifacts.
- Do not implement state router.

## Code Intelligence Needed

Before editing, run or collect:

```bash
codegraph status
codegraph query "commands"
codegraph query "main"
codegraph query "argparse"
```

If CodeGraph is unavailable, fallback:

```bash
rg -n "commands|argparse|def main|slash|status" src/core tests
```

## Expected Behavior

The core module should be able to inspect a repository root and report:

- required workflow files present/missing
- ignored local artifact paths configured or missing
- CodeGraph command availability
- `.codegraph/` initialization presence
- git dirty/clean summary if available
- warnings for staged or visible local artifacts

## Suggested Types

Keep simple. Possible structures:

```python
@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""

@dataclass
class WorkflowStatus:
    required_files: list[CheckResult]
    ignored_paths: list[CheckResult]
    codegraph: list[CheckResult]
    git: list[CheckResult]
    warnings: list[str]
```

Adjust to existing project style.

## Acceptance Criteria

- Adds read-only workflow status collection.
- Adds stable formatting function.
- Does not mutate files.
- Handles missing `.ai-dev/`.
- Handles missing `git`.
- Handles missing `codegraph`.
- Has targeted unit tests.

## Test Plan

Run targeted tests:

```bash
pytest tests/test_workflow_status.py -v
```

If command logic is touched:

```bash
pytest tests/test_commands.py -v
```

Optional smoke:

```bash
PYTHONPATH=src python -m core.main --help
```

## Map Sync

After implementation and before test selection:

```bash
codegraph sync
codegraph status
```

If CodeGraph is unavailable, record fallback.

## Review Checklist

- [ ] stayed inside allowed files
- [ ] no runtime writes
- [ ] no local artifacts staged
- [ ] tests passed or failure classified
- [ ] rollback path clear

## Rollback

Before commit:

```bash
git restore src/core/workflow_status.py tests/test_workflow_status.py
```

If `src/core/commands.py` is touched:

```bash
git restore src/core/commands.py
```
EOF

cat > .ai-dev/templates/TASK_025_WORKFLOW_STATUS_COMMAND.md <<'EOF'
# Current Task: task-025

## Goal

Wire the workflow status logic into the cc-mini command surface and complete targeted tests.

This task should only run after task-024 creates tested core workflow status logic.

## Why

Users need an accessible command, not only an internal module.

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3
- max_iterations: 2

## Depends On

- task-024 workflow status core module

## Allowed Read

Start with:

- `src/core/workflow_status.py`
- `src/core/commands.py`
- `src/core/main.py`
- `tests/test_workflow_status.py`
- `tests/test_commands.py`
- `tests/test_main.py`

Use CodeGraph/surface-search to adjust if needed.

## Allowed Edit

Likely:

- `src/core/commands.py`
- `tests/test_commands.py`

Optional if CLI routing requires:

- `src/core/main.py`
- `tests/test_main.py`

Do not edit workflow status core unless a small integration issue is found.

## Do Not Do

- Do not add workflow init.
- Do not add task generation.
- Do not add CodeGraph wrappers beyond status detection.
- Do not implement state router.
- Do not auto-run tests from the command.
- Do not commit local `.ai-dev/tasks/` or `.codegraph/`.

## Code Intelligence Needed

Before editing, run or collect:

```bash
codegraph status
codegraph query "commands"
codegraph query "workflow"
codegraph query "status"
codegraph callers "commands"
```

Fallback:

```bash
rg -n "command|slash|status|help|argparse|workflow" src/core tests
```

## Expected Behavior

The user should be able to run a workflow status command from the normal command surface.

Possible forms depend on existing architecture:

- `cc-mini workflow status`
- or slash command equivalent
- or command registry entry

Prefer the least invasive route that matches existing command patterns.

## Acceptance Criteria

- Workflow status command is reachable.
- Command output is readable.
- Command is read-only.
- Missing CodeGraph does not fail the command.
- Missing `.ai-dev/` produces warnings, not crashes.
- Tests cover the command route.

## Test Plan

Run:

```bash
pytest tests/test_workflow_status.py -v
pytest tests/test_commands.py -v
```

If `main.py` changes:

```bash
pytest tests/test_main.py -v
PYTHONPATH=src python -m core.main --help
```

## Map Sync

After implementation:

```bash
codegraph sync
codegraph status
git diff --name-only | codegraph affected --stdin --quiet
```

If CodeGraph is unavailable, use manual test mapping.

## Fresh Review Packet

Include:

- task goal
- changed files
- command route
- tests run
- output example
- diff stat
- rollback path

## Review Checklist

- [ ] route matches existing command architecture
- [ ] no unrelated command changes
- [ ] no write behavior introduced
- [ ] tests cover route and missing dependency cases
- [ ] output remains concise
- [ ] rollback path clear

## Rollback

Before commit:

```bash
git restore src/core/commands.py tests/test_commands.py
```

If touched:

```bash
git restore src/core/main.py tests/test_main.py
```

If task-024 files were modified:

```bash
git restore src/core/workflow_status.py tests/test_workflow_status.py
```
EOF

echo "Generated task 021-025 files."
echo "Next:"
echo "  git add .ai-dev/templates/WORKFLOW_SMOKE_REVIEW_EXECUTION.md"
echo "  git add .ai-dev/templates/FIRST_DRY_RUN_EXECUTION.md"
echo "  git add .ai-dev/design/WORKFLOW_STATUS_PLAN.md"
echo "  git add .ai-dev/templates/TASK_024_WORKFLOW_STATUS_CORE.md"
echo "  git add .ai-dev/templates/TASK_025_WORKFLOW_STATUS_COMMAND.md"
echo "  git commit -m \"Add dry run execution and workflow status task plans\""
