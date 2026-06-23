#!/usr/bin/env bash
set -eu

mkdir -p .ai-dev/templates

cat > .ai-dev/templates/TASK_031_WORKFLOW_INIT_CORE.md <<'EOF'
# Current Task: task-031

## Goal

Implement the core read-only/planned-safe file generation logic for `workflow init`.

This task should add helper functions that calculate what workflow files are missing and prepare write plans. It should not wire the user-facing command yet unless trivial.

## Depends On

- `.ai-dev/design/WORKFLOW_INIT_PLAN.md`
- workflow status implementation

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `src/core/workflow_status.py`
- `src/core/commands.py`
- `tests/test_workflow_status.py`
- `.ai-dev/design/WORKFLOW_INIT_PLAN.md`
- `.ai-dev/WORKFLOW.md`

## Allowed Edit

Preferred:

- `src/core/workflow_init.py`
- `tests/test_workflow_init.py`

Optional:

- `src/core/workflow_status.py`

## Do Not Do

- Do not wire CLI command yet unless clearly tiny.
- Do not overwrite existing files by default.
- Do not modify product source outside allowed files.
- Do not auto-commit.
- Do not initialize CodeGraph.

## Acceptance Criteria

- Can compute missing workflow files for a root.
- Can create missing files in a temporary directory.
- Does not overwrite existing files by default.
- Returns created/skipped/conflict results.
- Has unit tests with temporary directories.

## Test Plan

```bash
pytest tests/test_workflow_init.py -v
```

## Map Sync

After implementation:

```bash
codegraph sync
codegraph status
```

## Rollback

```bash
git restore src/core/workflow_init.py tests/test_workflow_init.py
git restore src/core/workflow_status.py
```
EOF

cat > .ai-dev/templates/TASK_032_WORKFLOW_INIT_COMMAND.md <<'EOF'
# Current Task: task-032

## Goal

Wire the workflow init core logic into the command surface.

## Depends On

- task-031 workflow init core

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `src/core/workflow_init.py`
- `src/core/workflow_status.py`
- `src/core/commands.py`
- `src/core/main.py`
- `tests/test_workflow_init.py`
- `tests/test_commands.py`

## Allowed Edit

- `src/core/commands.py`
- `tests/test_commands.py`

Optional if existing CLI routing requires:

- `src/core/main.py`
- `tests/test_main.py`

## Do Not Do

- Do not add task generation.
- Do not add context pack generation.
- Do not auto-initialize CodeGraph.
- Do not overwrite files without explicit user approval.

## Acceptance Criteria

- User can invoke workflow init through existing command surface.
- Command prints created/skipped/conflict summary.
- Existing files are preserved by default.
- Tests cover command route.

## Test Plan

```bash
pytest tests/test_workflow_init.py -v
pytest tests/test_commands.py -v
```

If `main.py` changes:

```bash
pytest tests/test_main.py -v
```

## Rollback

```bash
git restore src/core/commands.py tests/test_commands.py
git restore src/core/main.py tests/test_main.py
```
EOF

cat > .ai-dev/templates/TASK_033_WORKFLOW_DOCTOR_CORE.md <<'EOF'
# Current Task: task-033

## Goal

Implement core read-only checks for `workflow doctor`.

Start with file boundary, ignored paths, staged local artifacts, and markdown fence checks.

## Depends On

- `.ai-dev/design/WORKFLOW_DOCTOR_PLAN.md`
- workflow status implementation

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `src/core/workflow_status.py`
- `src/core/workflow_init.py`
- `.ai-dev/design/WORKFLOW_DOCTOR_PLAN.md`
- `tests/test_workflow_status.py`
- `tests/test_workflow_init.py`

## Allowed Edit

- `src/core/workflow_doctor.py`
- `tests/test_workflow_doctor.py`

Optional:

- `src/core/workflow_status.py`

## Do Not Do

- Do not auto-fix anything.
- Do not scan entire repository contents deeply.
- Do not implement complex secret scanning.
- Do not modify workflow files at runtime.

## Acceptance Criteria

- Doctor core is read-only.
- Detects missing ignore rules.
- Detects local artifact paths in git status output.
- Detects simple unclosed markdown code fences in workflow files.
- Reports severity: ok / warn / fail / blocked.
- Has unit tests.

## Test Plan

```bash
pytest tests/test_workflow_doctor.py -v
```

## Rollback

```bash
git restore src/core/workflow_doctor.py tests/test_workflow_doctor.py
git restore src/core/workflow_status.py
```
EOF

cat > .ai-dev/templates/TASK_034_WORKFLOW_DOCTOR_COMMAND.md <<'EOF'
# Current Task: task-034

## Goal

Wire workflow doctor into the command surface.

## Depends On

- task-033 workflow doctor core

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `src/core/workflow_doctor.py`
- `src/core/commands.py`
- `src/core/main.py`
- `tests/test_workflow_doctor.py`
- `tests/test_commands.py`

## Allowed Edit

- `src/core/commands.py`
- `tests/test_commands.py`

Optional:

- `src/core/main.py`
- `tests/test_main.py`

## Do Not Do

- Do not add auto-fix.
- Do not change init/status behavior except command registration if required.

## Acceptance Criteria

- User can invoke workflow doctor.
- Output is concise and severity-based.
- Command is read-only.
- Tests cover command route.

## Test Plan

```bash
pytest tests/test_workflow_doctor.py -v
pytest tests/test_commands.py -v
```

## Rollback

```bash
git restore src/core/commands.py tests/test_commands.py
git restore src/core/main.py tests/test_main.py
```
EOF

cat > .ai-dev/templates/TASK_035_CODEINTEL_PROVIDER_CORE.md <<'EOF'
# Current Task: task-035

## Goal

Implement the first small CodeIntel provider core with CodeGraph detection, CodeGraph query, and rg fallback.

## Depends On

- `.ai-dev/design/CODEINTEL_PROVIDER_IMPLEMENTATION_PLAN.md`

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `.ai-dev/design/CODEINTEL_PROVIDER_IMPLEMENTATION_PLAN.md`
- `src/core/tools/grep_tool.py`
- `src/core/commands.py`
- `tests/test_tools.py`
- `pyproject.toml`

## Allowed Edit

- `src/core/codeintel.py`
- `tests/test_codeintel.py`

## Do Not Do

- Do not implement MCP client.
- Do not implement full impact/call graph.
- Do not require CodeGraph for operation.
- Do not expose huge raw output.
- Do not use shell=True unless the project pattern requires it.

## Acceptance Criteria

- Detects CodeGraph unavailable.
- Runs CodeGraph status/query when available.
- Falls back to rg for keyword search.
- Applies timeouts and output limits.
- Returns compact structured results.
- Has tests with mocked subprocess.

## Test Plan

```bash
pytest tests/test_codeintel.py -v
```

## Map Sync

```bash
codegraph sync
codegraph status
```

## Rollback

```bash
git restore src/core/codeintel.py tests/test_codeintel.py
```
EOF

echo "Generated task 031-035 files."
echo "Next:"
echo "  git add .ai-dev/templates/TASK_031_WORKFLOW_INIT_CORE.md"
echo "  git add .ai-dev/templates/TASK_032_WORKFLOW_INIT_COMMAND.md"
echo "  git add .ai-dev/templates/TASK_033_WORKFLOW_DOCTOR_CORE.md"
echo "  git add .ai-dev/templates/TASK_034_WORKFLOW_DOCTOR_COMMAND.md"
echo "  git add .ai-dev/templates/TASK_035_CODEINTEL_PROVIDER_CORE.md"
echo "  git commit -m \"Add workflow init doctor and codeintel implementation tasks\""
