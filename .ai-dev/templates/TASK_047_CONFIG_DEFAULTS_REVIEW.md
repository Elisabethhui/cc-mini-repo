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
