# Current Task: task-044

## Goal

Review current prompts/instructions and identify what can be shortened or moved into skills.

## Depends On

- `.ai-dev/design/PROMPT_MINIMIZATION_PLAN.md`

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 1

## Allowed Read

- `AGENTS.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/skills/*/SKILL.md`
- `src/core/flow_state.py`
- prompt construction areas found by surface-search

## Allowed Edit

- `.ai-dev/design/PROMPT_MINIMIZATION_PLAN.md`

## Do Not Do

- Do not change runtime prompts in product code yet.
- Do not remove safety rules.
- Do not modify skills unless explicitly scoped.

## Acceptance Criteria

- Identifies prompt content categories.
- Marks what stays visible vs moves to skills.
- Proposes first implementation task.

## Test Plan

No product tests required. This is design review.
