# cc-mini Delivery Closure Design

**Date:** 2026-04-22

## Goal

Add a delivery-closure phase that turns a completed coding task into a verifiable, reviewable, manually confirmed, commit-ready, and closeable unit of work. The objective is to connect the existing coding workflow to the project-level milestone flow without merging the two concerns into one large subsystem.

## Context

The current roadmap already covers:

- Phase 1 minimal startup
- Phase 2 controlled coding workflow
- Phase 3 continuity and maintenance projections
- Phase 4 runtime isolation
- Phase 5 bounded general-agent expansion

What is still missing is the end-of-work product loop: after a task is implemented, the system should help the user verify it, review it, explicitly confirm commit intent, and capture a concise closeout summary that can be reused for milestone audit and later release notes.

This phase is intentionally about closure, not broader intelligence. It should not introduce a new routing engine, a new planner, or a new general-agent capability. It should make the existing work easier to finish cleanly.

## Design Summary

The phase has two layers:

- A command-layer delivery loop for coding work
- A milestone-layer closeout record for audit and review

The command layer is responsible for execution order and user-facing prompts. The milestone layer is responsible for capturing evidence and recording what was completed. They should communicate through structured outputs, not shared mutable state. The implementation must keep commit as a manually confirmed action rather than an automatic side effect.

## Recommended Shape

### 1. Command-Layer Delivery Loop

The coding path should expose a small, explicit sequence:

1. complete the implementation
2. verify the change
3. review the change
4. ask for explicit user confirmation to commit
5. commit the change only after confirmation
6. produce a closeout summary

The key design choice is that verification and review remain distinct:

- Verification proves the code works
- Review checks risk, regressions, and scope
- Commit turns a validated result into a durable git artifact, but only after explicit user confirmation
- Closeout summarizes what shipped and what remains deferred

This should be expressed as a small, bounded flow rather than a monolithic "ship everything" command. The existing `/review`, `/test`, and `/commit` skills already cover parts of the loop; the new work should make the sequence obvious and repeatable without making commit automatic.

### 2. Milestone-Layer Closeout Record

After a task is verified and committed, the system should emit a closeout record that can be reused for:

- milestone audit
- release notes
- carry-forward debt
- future roadmap planning

The closeout record should contain:

- the task or phase name
- the commands or tests that were run
- whether the review passed
- the commit hash if one was created
- known residual risks
- whether the work is ready for milestone review or still has gaps

This record should be append-only and human-readable. It should not mutate source files.

## Components

### Delivery Command Surface

This is the user-facing path that helps a completed task turn into a verified commit.

Responsibilities:

- expose the closure flow clearly
- keep the user informed of each step
- avoid mixing implementation and closure concerns

Dependencies:

- existing task execution and prompt flow
- existing review, test, and commit skills

### Closeout Summary Builder

This is a small record builder that takes validation and review outcomes and turns them into a compact summary.

Responsibilities:

- normalize command results into a standard structure
- capture pass/fail state and residual risk
- prepare a milestone-readable summary

Dependencies:

- test results
- review results
- commit metadata when available

### Milestone Closeout Notes

This is the handoff artifact for audit or later milestone completion.

Responsibilities:

- document what shipped
- document what remains intentionally deferred
- provide a stable summary for review and archive decisions

Dependencies:

- closeout summary builder output
- roadmap phase boundaries

## Data Flow

The expected flow is:

1. A coding task is completed.
2. The user or coordinator requests verification.
3. Tests or smoke checks run and return structured results.
4. A review pass is performed.
5. If review passes, the user is explicitly asked to confirm whether to commit.
6. If the user confirms, the change is committed.
7. A closeout summary is emitted in both human-readable Markdown and machine-readable JSON.
8. The closeout summary is used for milestone audit and any later release-note or archive work.

The important constraint is that the closeout summary is downstream of validation, not a replacement for it. It may report a task as "ready for audit" only if the verification and review steps succeeded.

## Error Handling

The closure flow should fail safely in the following cases:

- If verification fails, the flow stops before review/commit and reports the failing command or test.
- If review finds a risk, the flow stops before commit unless the user explicitly chooses to continue.
- If the user declines commit, the flow stops before any git mutation and records that the task is pending closeout.
- If commit fails, the closeout summary must clearly mark the task as uncommitted.
- If the closeout record cannot be written or rendered, the implementation result remains intact; only the summary step fails.

The closure phase should never hide a failed verification behind a successful closeout note.

## Testing

Validation for this phase should focus on end-to-end closure behavior, not on adding more unit coverage for existing coding features.

Recommended test coverage:

- a minimal coding task can be verified, reviewed, committed, and summarized
- the commit step requires explicit user confirmation before it mutates git state
- the review step cannot be skipped silently
- a failed verification prevents a "ready to close" result
- the closeout summary records the commit hash when present
- the summary distinguishes "ready for audit" from "not yet ready"
- the closeout flow emits both Markdown and JSON records
- a read-only `/milestone-review` command can consume the closeout summary without mutating source files

The tests should use the smallest possible coding example that proves the chain works. The goal is to verify the closure handoff, not to retest the entire product.

## Scope Boundaries

This phase should not:

- add a new routing engine
- replace the existing task, patch, or wiki workflows
- make general-agent behavior broader
- auto-archive milestones
- turn closeout into a hidden background process
- make commit automatic without confirmation

This phase should:

- make the end of work explicit
- produce audit-friendly summaries in both JSON and Markdown
- preserve the separation between implementation and closure
- give the project a clean way to finish a coding task before milestone review
- expose a read-only `/milestone-review` command for audit consumption

## Interfaces

### `/close`

`/close` is the user-facing closure action for coding work. It should:

- run or collect verification results
- present the review outcome
- ask the user to confirm before committing
- emit the closeout summary after the commit decision

`/close` does not itself make a commit without confirmation. It is the orchestration point, not the mutator.

### `/milestone-review`

`/milestone-review` is a read-only audit command. It should:

- read the closeout summary
- summarize whether the work is ready for milestone review
- report residual risks and deferred debt
- never mutate source files or git state

If the closeout summary is missing, `/milestone-review` should say so plainly and point the user back to `/close`.

## Recommended Outcome

After this phase, cc-mini should be able to finish a coding task in a way that is:

- verifiable
- reviewable
- commit-ready after explicit confirmation
- closeout-friendly

That is the missing bridge between "the code works" and "the work can be safely carried forward into the next milestone."
