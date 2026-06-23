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
