# Artifact Policy

## Purpose

Define what files belong in the repository and what files are local workflow state.

This prevents the project from becoming cluttered with AI task artifacts.

## Artifact Classes

### Product Code

Committed.

Examples:

- `src/`
- `tests/`
- `pyproject.toml`
- `README.md`
- product docs
- installation scripts

### Committed Workflow Files

Committed.

Examples:

- `AGENTS.md`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/PROJECT_MAP.md`
- `.ai-dev/CODEGRAPH.md`
- `.ai-dev/TESTING.md`
- `.ai-dev/skills/`
- `.ai-dev/templates/`
- `.ai-dev/design/`

### Local Task Artifacts

Ignored.

Examples:

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`

### Local Code Intelligence Indexes

Ignored.

Examples:

- `.codegraph/`
- `.codebase-memory/`

### Generated Or Cache Files

Ignored.

Examples:

- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- build outputs
- raw logs
- temporary command outputs

## Rules

Before creating a new file, classify it as:

- product code
- committed workflow file
- local task artifact
- local code intelligence index
- generated/cache file

If classification is unclear, stop and ask.

## Commit Rules

Allowed in normal commits:

- product code related to the task
- tests related to the task
- committed workflow files intentionally changed

Not allowed in normal commits:

- local task files
- context packs
- work logs
- checkpoints
- temp files
- CodeGraph indexes
- cache files
- raw logs
- secrets

## Local Task Lifecycle

Local task artifacts may be created during work.

They should live under:

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`

They are not committed by default.

If a task artifact becomes durable documentation, move it deliberately to:

- `docs/`
- or `.ai-dev/design/`
- or `.ai-dev/PROJECT_MAP.md`

Do not commit it from local artifact paths.

## Retention Policy

Suggested local cleanup:

- keep active task artifacts
- keep recent work logs while feature branch is active
- remove stale temp files
- archive or delete old local task files after merge

No automatic deletion in first product version.

## Secret Handling

Never commit secrets.

If a secret appears in a local task artifact:

1. redact it immediately
2. rotate the key if it may have been exposed
3. check `git status`
4. check staged files
5. do not commit the artifact

Potential secret patterns:

- API keys
- bearer tokens
- private URLs with credentials
- `.env` values
- access tokens
- cloud credentials

## Review Checklist

Before commit:

- `git status --short`
- `git diff --stat`
- no `.ai-dev/tasks/`
- no `.ai-dev/context-packs/`
- no `.ai-dev/worklogs/`
- no `.ai-dev/tmp/`
- no `.codegraph/`
- no `.codebase-memory/`
- no `__pycache__/`
- no `*.pyc`
- no secrets

## Future Product Support

Future `cc-mini workflow doctor` should enforce this policy.

Checks:

- ignored paths exist in `.gitignore`
- ignored local artifacts are not staged
- cache files are not tracked
- possible secrets are flagged
- workflow files are in approved locations

## Open Questions

- Should workflow doctor block commits?
- Should local artifacts have expiration metadata?
- Should users choose a custom workflow directory?
- Should work logs ever be promoted into committed docs?