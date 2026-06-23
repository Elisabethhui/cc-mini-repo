# Workflow Doctor Command Plan

## Purpose

Plan a read-only diagnostic command:

`cc-mini workflow doctor`

Doctor should perform deeper checks than `workflow status`.

## Goal

Help users identify workflow setup issues, ignored-file leaks, stale CodeGraph state, malformed workflow files, and possible secret exposure.

## Relationship To Status

`workflow status` is quick and friendly.

`workflow doctor` is deeper and more diagnostic.

Use status before normal work.
Use doctor when something feels wrong or before a major commit.

## Non-Goals

Do not implement yet:

- automatic fixes
- automatic secret removal
- automatic commits
- full markdown parsing engine
- full static analysis
- CodeGraph database inspection

## Checks

Doctor should check:

- required workflow files
- ignored local artifact paths
- tracked cache files
- staged local artifacts
- CodeGraph availability
- CodeGraph initialization
- CodeGraph freshness if possible
- malformed Markdown code fences in `.ai-dev/skills`
- potential secrets in staged diff
- pycache or generated files tracked by git

## Suggested Command

```bash
cc-mini workflow doctor
```

Output shape:

```text
Context-Bounded Workflow Doctor

File boundary:
  OK ignored local task artifacts
  WARN .pytest_cache tracked by git

Markdown:
  OK skill code fences

CodeGraph:
  WARN not installed

Secrets:
  OK no obvious staged secrets

Decision:
  pass-with-warnings
```

## Severity Levels

- `ok`
- `warn`
- `fail`
- `blocked`

Use `blocked` for:

- obvious staged secrets
- local artifact directories staged
- workflow files malformed enough to break use

## Implementation Areas

Likely files:

- `src/core/workflow_status.py`
- maybe new `src/core/workflow_doctor.py`
- `src/core/commands.py`
- `tests/test_workflow_doctor.py`

## Acceptance Criteria

- read-only
- does not mutate files
- works without CodeGraph
- detects ignored path problems
- detects staged local artifacts
- detects simple unclosed code fences in workflow files
- flags obvious secret patterns in staged diff
- has targeted tests

## Test Plan

```bash
pytest tests/test_workflow_doctor.py -v
pytest tests/test_commands.py -v
```

Test cases:

- clean scaffold passes
- missing ignored path warns/fails
- staged local artifact blocks
- unclosed code fence fails
- fake secret in staged diff blocks
- CodeGraph missing warns but does not fail

## Risks

- false positives in secret detection
- too much output for small models
- command becomes slow
- doctor starts fixing things unexpectedly

## First Executable Task

Create task:

`task-028 implement workflow doctor read-only checks`

Start with file boundary and markdown fence checks only.
