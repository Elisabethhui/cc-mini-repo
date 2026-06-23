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
