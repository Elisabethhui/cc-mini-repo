---
name: fresh-review
description: Use when reviewing a completed implementation in a fresh, isolated context to avoid context-window overflow and self-review bias.
---

# Fresh Review

## Purpose

Review a completed task in a clean context instead of reusing the noisy implementation session.

Use this skill after implementation, map-sync, and test-gate.

Fresh review reduces token pressure and helps avoid self-review bias.

## Relationship To Review Rollback

`fresh-review` defines the review isolation policy.

`review-rollback` makes the decision after reviewing evidence.

Use fresh review when:

- the implementation session is long
- the diff is non-trivial
- context budget is near the limit
- the task spans multiple files
- tests are partial
- risk is medium or high

## File Boundary

Committed file:

- `.ai-dev/skills/fresh-review/SKILL.md`

Local review notes belong in ignored paths:

- `.ai-dev/worklogs/`
- `.ai-dev/tmp/`

Never commit:

- raw full conversation history
- large diff dumps
- secrets
- API keys
- generated cache files
- `.codegraph/`
- `.codebase-memory/`

## Inputs

Use only the smallest useful review packet:

- original task goal
- acceptance criteria
- context pack summary
- changed files
- diff stat
- focused diff
- test-gate result
- map-sync freshness result
- rollback path

Do not include:

- full chat history
- full CodeGraph raw output
- unrelated brainstorming
- entire source files
- repeated logs
- stale task notes

## Fresh Context Rule

Fresh review should run as a separate review packet.

The review packet should answer:

- What was supposed to change?
- What changed?
- How was it tested?
- What is the impact?
- Can it be rolled back?
- Should it commit, revise, rollback, reslice, or hold?

## Review Packet Budget

For 32k models:

- task summary: short
- context pack summary: short
- changed file list: complete
- diff stat: complete
- diff: focused, not necessarily entire huge diff
- tests: summarized
- risks: explicit

If the diff is too large, split review by file or module.

## Diff Handling

Use this order:

1. `git diff --stat`
2. `git diff --name-only`
3. focused `git diff` for changed files
4. full diff only if it fits the budget

For large diffs, review by file group:

- API/interface changes
- implementation changes
- tests
- docs/workflow files

Do not paste huge diffs into a small-context model.

## Suggested Commands

Use these commands when appropriate:

```bash
git status --short
git diff --stat
git diff --name-only
git diff -- <path>
git diff --check
git diff --name-only | codegraph affected --stdin --quiet
```
If reviewing an existing commit:
```bash
git show --stat --oneline HEAD
git show --name-only HEAD
git show --check HEAD
git show -- <path>
Review Focus
```
Check:

task boundary
changed files
behavior correctness
tests or verification evidence
map-sync freshness
impact/risk
rollback path
secrets or local artifacts
unrelated changes

Do not review style preferences unless they affect correctness or maintainability.

Output Format

Write the fresh review with these sections:

# Fresh Review: task-xxx
## Review Packet
## Changed Files
## Diff Summary
## Verification Evidence
## Map Freshness
## Findings
## Risk
## Recommendation
## Rollback Path

Recommendation must be one of:

commit
revise
rollback
reslice
hold
Quality Check

Before finishing, verify:

Review used a clean packet, not full session history.
Diff evidence is sufficient.
Tests are summarized.
Map freshness is known or explicitly unknown.
Risk is classified.
Recommendation is explicit.
Rollback path is concrete.
Stop Rules

Stop and ask for user decision if:

diff is too large for one review packet
tests failed or were not run for a logic change
map freshness is stale or unknown
secrets may be present
local task artifacts are staged
review cannot determine whether behavior is correct