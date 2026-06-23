#!/usr/bin/env bash
set -eu

mkdir -p .ai-dev/design
mkdir -p .ai-dev/templates

cat > .ai-dev/templates/TASK_036_CODEINTEL_COMMANDS.md <<'EOF'
# Current Task: task-036

## Goal

Expose the CodeIntel provider through a small command surface.

Start with read-only commands for status and query.

## Depends On

- task-035 CodeIntel provider core

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `src/core/codeintel.py`
- `src/core/commands.py`
- `src/core/main.py`
- `tests/test_codeintel.py`
- `tests/test_commands.py`

## Allowed Edit

- `src/core/commands.py`
- `tests/test_commands.py`

Optional:

- `src/core/main.py`
- `tests/test_main.py`

## Do Not Do

- Do not add context pack generation.
- Do not add automatic source reading.
- Do not require CodeGraph to be installed.
- Do not output huge raw query results.

## Acceptance Criteria

- User can ask for CodeIntel status.
- User can run a keyword query.
- Output is compact.
- Missing CodeGraph falls back or warns clearly.
- Tests cover command route.

## Test Plan

```bash
pytest tests/test_codeintel.py -v
pytest tests/test_commands.py -v
```

## Rollback

```bash
git restore src/core/commands.py tests/test_commands.py
git restore src/core/main.py tests/test_main.py
```
EOF

cat > .ai-dev/design/TEST_SELECTOR_PLAN.md <<'EOF'
# Test Selector Plan

## Purpose

Plan the product logic for choosing the smallest useful tests after code changes.

## Goal

Use changed files, CodeGraph affected tests, and manual mapping rules to recommend targeted verification.

## Inputs

- changed files
- CodeIntel provider freshness
- CodeGraph affected tests
- `.ai-dev/TESTING.md`
- known test files

## Provider Order

1. CodeGraph affected tests when map is fresh.
2. Manual mapping from `.ai-dev/TESTING.md`.
3. Nearby tests by filename similarity.
4. Smoke command.
5. Broad suite as last resort.

## Proposed Module

```text
src/core/test_selector.py
```

## Acceptance Criteria

- recommends test commands for changed files
- works without CodeGraph
- explains confidence and fallback
- avoids running tests automatically
- has tests

## Risks

- false confidence from empty affected tests
- environment-specific test failures
- over-selecting broad tests
EOF

cat > .ai-dev/templates/TASK_037_TEST_SELECTOR_CORE.md <<'EOF'
# Current Task: task-037

## Goal

Implement a read-only test selector core that recommends targeted tests from changed files.

## Depends On

- `.ai-dev/design/TEST_SELECTOR_PLAN.md`
- task-035 CodeIntel provider core

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `.ai-dev/TESTING.md`
- `.ai-dev/design/TEST_SELECTOR_PLAN.md`
- `src/core/codeintel.py`
- `tests/`

## Allowed Edit

- `src/core/test_selector.py`
- `tests/test_test_selector.py`

## Do Not Do

- Do not run tests automatically.
- Do not wire command yet.
- Do not require CodeGraph.
- Do not inspect huge files.

## Acceptance Criteria

- Recommends tests for known cc-mini source areas.
- Uses CodeGraph affected tests if available and fresh.
- Falls back to manual mapping.
- Returns confidence and warnings.
- Has unit tests.

## Test Plan

```bash
pytest tests/test_test_selector.py -v
```

## Rollback

```bash
git restore src/core/test_selector.py tests/test_test_selector.py
```
EOF

cat > .ai-dev/templates/TASK_038_WORKFLOW_TEST_COMMAND.md <<'EOF'
# Current Task: task-038

## Goal

Wire test selector into a read-only workflow test recommendation command.

The command recommends tests; it does not run them automatically in v1.

## Depends On

- task-037 test selector core

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `src/core/test_selector.py`
- `src/core/commands.py`
- `tests/test_test_selector.py`
- `tests/test_commands.py`

## Allowed Edit

- `src/core/commands.py`
- `tests/test_commands.py`

Optional:

- `src/core/main.py`
- `tests/test_main.py`

## Do Not Do

- Do not execute tests automatically.
- Do not add review or logging.
- Do not mutate local task files.

## Acceptance Criteria

- Command recommends test commands from current diff or passed files.
- Output includes confidence and fallback reason.
- Missing CodeGraph does not fail.
- Tests cover route.

## Test Plan

```bash
pytest tests/test_test_selector.py -v
pytest tests/test_commands.py -v
```

## Rollback

```bash
git restore src/core/commands.py tests/test_commands.py
git restore src/core/main.py tests/test_main.py
```
EOF

cat > .ai-dev/templates/TASK_039_WORKFLOW_REVIEW_PACKET.md <<'EOF'
# Current Task: task-039

## Goal

Implement a read-only helper that builds a compact fresh-review packet from task goal, diff stat, changed files, and test evidence.

## Depends On

- fresh-review skill
- review-rollback skill

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `.ai-dev/skills/fresh-review/SKILL.md`
- `.ai-dev/skills/review-rollback/SKILL.md`
- `src/core/commands.py`
- existing git helper patterns if any

## Allowed Edit

- `src/core/review_packet.py`
- `tests/test_review_packet.py`

## Do Not Do

- Do not call an LLM.
- Do not perform review automatically.
- Do not commit or rollback.
- Do not include huge diffs by default.

## Acceptance Criteria

- Builds compact packet from git diff metadata.
- Supports focused diff by file.
- Truncates large diff safely.
- Flags local artifact paths.
- Has tests.

## Test Plan

```bash
pytest tests/test_review_packet.py -v
```

## Rollback

```bash
git restore src/core/review_packet.py tests/test_review_packet.py
```
EOF

cat > .ai-dev/templates/TASK_040_WORKLOG_GENERATOR.md <<'EOF'
# Current Task: task-040

## Goal

Implement a local ignored work-log generator for completed workflow tasks.

## Depends On

- work-log skill

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `.ai-dev/templates/WORK_LOG.md`
- `.ai-dev/skills/work-log/SKILL.md`
- `src/core/commands.py`

## Allowed Edit

- `src/core/work_log.py`
- `tests/test_work_log.py`

Optional command wiring:

- `src/core/commands.py`
- `tests/test_commands.py`

## Do Not Do

- Do not commit generated logs.
- Do not write outside `.ai-dev/worklogs/` by default.
- Do not include secrets or raw huge logs.

## Acceptance Criteria

- Can render compact work log text.
- Can write to `.ai-dev/worklogs/task-xxx.md`.
- Creates parent directory if needed.
- Keeps output short.
- Has tests with temporary directories.

## Test Plan

```bash
pytest tests/test_work_log.py -v
```

If command wiring is included:

```bash
pytest tests/test_commands.py -v
```

## Rollback

```bash
git restore src/core/work_log.py tests/test_work_log.py
git restore src/core/commands.py tests/test_commands.py
```
EOF

echo "Generated task 036-040 files."
echo "Next:"
echo "  git add .ai-dev/templates/TASK_036_CODEINTEL_COMMANDS.md"
echo "  git add .ai-dev/design/TEST_SELECTOR_PLAN.md"
echo "  git add .ai-dev/templates/TASK_037_TEST_SELECTOR_CORE.md"
echo "  git add .ai-dev/templates/TASK_038_WORKFLOW_TEST_COMMAND.md"
echo "  git add .ai-dev/templates/TASK_039_WORKFLOW_REVIEW_PACKET.md"
echo "  git add .ai-dev/templates/TASK_040_WORKLOG_GENERATOR.md"
echo "  git commit -m \"Add codeintel test selector review packet and worklog tasks\""
