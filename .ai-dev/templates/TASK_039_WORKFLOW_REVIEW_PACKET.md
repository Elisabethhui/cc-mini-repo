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
