---
name: test-gate
description: Use after implementation or before review to select and run the smallest useful verification for a context-bounded coding task.
---

# Test Gate

## Purpose

Verify one task with the smallest useful test set.

A test gate is not a full QA process. It is a task-level verification step that proves whether the current change works well enough to review or commit.

## File Boundary

Committed files:

- `.ai-dev/skills/test-gate/SKILL.md`
- `.ai-dev/templates/TEST_GATE.md`

Local test notes belong in ignored paths:

- `.ai-dev/worklogs/`
- `.ai-dev/tmp/`

Do not commit raw logs unless explicitly requested.

Never include secrets, API keys, raw environment values, or huge terminal output.

## Inputs

Use these inputs when available:

- current task file
- context pack
- changed files from `git diff --name-only`
- CodeGraph affected test results
- existing test commands from README, pyproject, AGENTS, or docs
- recent test failures

## Test Selection Order

Choose the smallest useful verification first:

1. Existing unit test directly covering the changed file or symbol.
2. Affected tests from CodeGraph.
3. Nearby tests in the same module or feature area.
4. Targeted smoke test for the changed behavior.
5. Broader test file.
6. Full test suite only when necessary.

## Common Commands

```bash
git diff --name-only
git diff --name-only | codegraph affected --stdin --quiet
pytest tests/ -v -k "not integration"
pytest tests/path/to/test_file.py -v
pytest tests/path/to/test_file.py::test_name -v
```

## Verification Levels

Classify the result as one of:

- `none`: no verification was run
- `manual`: behavior was checked manually
- `smoke`: basic command or startup path passed
- `unit`: targeted unit tests passed
- `integration`: integration-level tests passed
- `full`: full relevant suite passed

Prefer at least `unit` for logic changes.

Use `manual` or `smoke` only when automated tests are unavailable or too expensive.

## Process

1. Identify changed files.
2. Ask CodeGraph for affected tests when available.
3. Inspect existing tests only as needed.
4. Choose the smallest useful test command.
5. Run or recommend the command.
6. Summarize pass/fail without dumping full logs.
7. If failure occurs, identify whether it is related to the current task.
8. Stop after two failed fix attempts and return to task slicing or context packing.

## Failure Handling

If tests fail, classify the failure:

- task-related failure
- pre-existing failure
- environment/dependency failure
- flaky or timeout failure
- unclear failure

For task-related failures, allow a focused fix if it stays inside the task boundary.

For unrelated or unclear failures, record the failure and stop before expanding scope.

## Output Format

Write the test gate result with these sections:

- `# Test Gate: task-xxx`
- `## Changed Files`
- `## Candidate Tests`
- `## Selected Verification`
- `## Commands Run`
- `## Result`
- `## Verification Level`
- `## Failures`
- `## Risk`
- `## Next Step`

## Quality Check

Before finishing, verify:

- The selected test matches the task.
- The command is as narrow as practical.
- Failures are not hidden.
- The result can be used by review.
- The task is not expanding into unrelated debugging.

## Stop Rules

Stop and ask for help or reslicing if:

- no relevant test can be identified
- affected tests are too broad
- the same test fails twice after focused fixes
- the failure appears unrelated to the task
- verification requires changing more files than the task allows