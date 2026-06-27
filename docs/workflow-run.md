# Workflow Run Commands

The `/workflow-run` family of commands provides bounded, recoverable, and supervised execution for coding tasks.

## Commands

### `/workflow-pack <goal>`

Generate a bounded context pack for a goal or task-id.

- Loads the latest PlanGraph from `.ai-dev/runtime/` if available.
- Queries CodeGraph (or falls back to `rg`) if code exists.
- Builds a prioritized context pack (P0–P4) within the configured `context_window`.
- Saves the pack to `.ai-dev/context-packs/<run-id>.md`.

Example:

```
> /workflow-pack "Add user authentication"

✓ Context pack generated: .ai-dev/context-packs/20240115-120000.md
  Goal: Add user authentication
  Tokens: 4,231 / 32,768
  State: ok
```

### `/workflow-run --dry-run <goal>`

Preview the execution plan without calling any model or modifying code.

- Creates a runtime run under `.ai-dev/runtime/<run-id>/`.
- Initializes PlanGraph and context pack.
- Computes budget reports for the initial state.
- Shows planned phases: intake → plan → retrieve → pack → implement → test → review.

Example:

```
> /workflow-run --dry-run "Add user authentication"

✓ Dry-run plan created: 20240115-120000
  Goal: Add user authentication
  Phase: intake
  Next Action: Start intake

  Context Pack: .ai-dev/context-packs/20240115-120000.md
  Tokens: 4,231 / 32,768
  Pack State: ok

  Budget: ok (1,234/32,768)

Planned Phases:
  1. intake
  2. plan
  3. retrieve
  4. pack
  5. implement
  6. test
  7. review

Run without --dry-run to execute.
```

### `/workflow-run <goal>`

Run supervised execution.

- One context pack + one model call per step.
- Each step writes a `StepResult` artifact to `.ai-dev/runtime/<run-id>/artifacts/`.
- Test gate: failing tests route to `revise`, not `done`.
- Review gate: only `commit` decision allows `done`; `revise`/`rollback`/`hold` block.
- After completion, runs workflow gates (test selector, review packet, rollback helper, work log, workflow next).

Example:

```
> /workflow-run "Add user authentication"

Starting supervised execution: 20240115-120000
...
✓ Supervised execution complete: 20240115-120000
  Final phase: done
  Next action: Task completed
  Step results: 7 artifacts

Workflow Gates
Test Selector
Confidence: medium
...

Workflow Next
State: done
Next action: No further workflow action is required for this task.
```

### `/workflow-resume <run-id>`

Resume a workflow run from saved runtime state.

- Loads existing `state.json` from `.ai-dev/runtime/<run-id>/`.
- If phase is `done` or `blocked`, reports status without calling the model.
- Rebuilds context pack from preserved state and continues execution.
- Step numbering continues monotonically from existing artifacts.

Without a run-id, lists all available runs:

```
> /workflow-resume

Available workflow runs:
  • 20240115-120000
  • 20240115-113000
Usage: /workflow-resume <run-id>
```

With a run-id:

```
> /workflow-resume 20240115-120000

Resuming run 20240115-120000 from phase 'plan'…
  Goal: Add user authentication
  Previous steps: 2
...
✓ Resume complete: 20240115-120000
  Final phase: done
  Next action: Task completed
```

## Gates

After `/workflow-run` completes, the following gates run automatically:

1. **Test Selector** — Recommends tests based on changed files.
2. **Review Packet** — Builds a compact diff summary and risk notes.
3. **Rollback Helper** — Suggests safe rollback commands.
4. **Work Log** — Writes a summary to `.ai-dev/worklogs/<run-id>.md`.
5. **Workflow Next** — Recommends the next state (done, blocked, needs_test_gate, etc.).

## Safety Boundaries

The runtime **never** automatically:
- `git commit`
- `git push`
- `git reset --hard`
- Delete files broadly
- Run destructive shell commands
- Modify credentials or CI/CD secrets

These require explicit user confirmation.

## Local Artifacts

All runtime output stays under `.ai-dev/` and must not be committed:

- `.ai-dev/runtime/<run-id>/state.json`
- `.ai-dev/runtime/<run-id>/plan-graph.json`
- `.ai-dev/runtime/<run-id>/steps/step-xxx.md`
- `.ai-dev/runtime/<run-id>/artifacts/step-result-xxx.json`
- `.ai-dev/context-packs/<run-id>.md`
- `.ai-dev/worklogs/<run-id>.md`

These directories are already in `.gitignore`.
