# Final N-Context Runtime Review

## Scope

This review covers Tasks 051–070: the N-Context Graph-First Coding Runtime for cc-mini.

## What Was Built

### Core Components

1. **Runtime Profile** (`src/core/runtime_profile.py`) — Configurable `context_window=N` with provider/model-specific defaults.
2. **Context Budget Calculator** (`src/core/context_budget.py`) — Ratio-based budget decisions: ok → warning → preserve → split → hard_stop.
3. **Preservation Pipeline** (`src/core/preservation.py`) — Deterministic freeze/extract/persist/repack/continue cycle when budget pressure hits.
4. **Runtime State Store** (`src/core/runtime_state.py`) — JSON state, JSONL budget reports, markdown step logs, artifact files. All confined to `.ai-dev/runtime/<run-id>/`.
5. **PlanGraph** (`src/core/plan_graph.py`) — Empty-repo planning graph with task DAG, decisions, risks, open questions. JSON round-trip and Kahn topological sort.
6. **Plan Preservation** (`src/core/plan_preservation.py`) — Deterministic planning pack externalization.
7. **CodeGraph Retrieval Adapter** (`src/core/code_retrieval.py`) — CodeGraph-first with graceful `rg` fallback. Six query methods + fallback.
8. **Context Pack Builder** (`src/core/context_pack.py`) — P0–P4 priority packing with budget-aware assembly and artifact externalization.
9. **Batch Runner** (`src/core/batch_runner.py`) — Deterministic state machine: intake → plan → retrieve → pack → implement → test → review → done/blocked. Supports supervised execution (one model call per step) and resume.
10. **Agent Protocol** (`src/core/agent_protocol.py`) — Six bounded agent specs with permission enforcement, spawn guard (max_depth=3), and prompt templates.
11. **Workflow Gates Integration** (Task 069) — Test selector, review packet, work log, rollback helper, and workflow next automatically run after execution.

### Commands

| Command | Task | Status |
|---------|------|--------|
| `/plan-init <goal>` | 059 | ✅ |
| `/plan-status` | 059 | ✅ |
| `/plan-export` | 059 | ✅ |
| `/workflow-pack <goal>` | 063 | ✅ |
| `/workflow-run --dry-run <goal>` | 066 | ✅ |
| `/workflow-run <goal>` | 067 | ✅ |
| `/workflow-resume <run-id>` | 068 | ✅ |

### E2E Verification

Two dry-run paths are verified:

1. **Empty repository** (`tests/test_e2e_empty_repo_workflow.py`):
   - Goal → PlanGraph → task DAG → context pack → runtime state persistence
   - No CodeGraph required; no LLM calls

2. **Existing repository** (`tests/test_e2e_existing_repo_workflow.py`):
   - Goal → CodeGraph retrieval (or rg fallback) → context pack → batch runner dry-run
   - Budget reports recorded; runtime state survives resume

## Design Decisions

### context_window = N, not 32K fixed

The runtime treats `context_window` as a configurable parameter. All budget calculations use the user-provided value. Default is 32K for backward compatibility, but 200K, 8K, or 4K models are equally supported.

### CC_MINI_MAX_TOKENS = output tokens only

This variable controls the model's `max_tokens` API parameter (output budget). It does not affect the context window size. This separation prevents the common mistake of setting `--max-tokens 32000` on a 32K model and leaving no room for the prompt.

### CodeGraph-first, PlanGraph-first

- **Before code exists**: PlanGraph-only. Task DAG, decisions, and architecture slices drive planning.
- **After code exists**: CodeGraph locates symbols/files/callers; PlanGraph explains intent and task dependencies.
- **Transition**: Explicit. After scaffold exists, both graphs work together.

### Preservation before hard_stop

The pipeline attempts `preserve` (externalize state, repack, continue) before reaching `hard_stop`. This means most context pressure is handled automatically; hard_stop is reserved for pathological cases.

### Resume from runtime state, not chat history

`/workflow-resume` loads `state.json` and `step-result-*.json` artifacts, then rebuilds a fresh context pack. It does not replay the full chat history. This keeps resumes bounded and deterministic.

### Gates prevent premature done

- Test gate: failures route to `revise`, never `done`.
- Review gate: only explicit `commit` decision allows `done`. `revise`/`rollback`/`hold` block.
- Workflow next: recommends `blocked`, `needs_test_gate`, `needs_fresh_review`, or `done` based on artifact evidence.

## Safety Boundaries

The runtime never automatically:
- `git commit`
- `git push`
- `git reset --hard`
- Delete files broadly
- Run destructive shell commands
- Modify credentials or CI/CD secrets

These require explicit user confirmation.

## Test Coverage

- ~850+ tests passing (including existing suite).
- All new components have dedicated test files.
- No test depends on real LLM, real CodeGraph, or real OMLX.
- E2E dry-run tests verify both empty-repo and existing-repo paths.

## Local Artifacts (Ignored)

- `.ai-dev/runtime/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`
- `.codegraph/`
- `.codebase-memory/`

All are in `.gitignore`.

## Known Limitations (Phase 1 Boundary)

- Patch execution and post-edit reconcile are deferred to later phases.
- `/reconcile` and `/maintenance` are view-only projections.
- Agent protocol templates are placeholder markdown files; full agent orchestration is future work.
- CodeGraph retrieval requires the `codegraph` CLI if real graph queries are desired; fallback to `rg` always works.

## Acceptance Criteria Checklist

- [x] `context_window` can be configured.
- [x] Output budget is separate from context window.
- [x] Budget includes reserved output and safety margin.
- [x] Unknown OpenAI-compatible models do not default to 200K.
- [x] pressure/preserve/split/hard_stop states exist.
- [x] Hard stop prevents unsafe model calls.
- [x] Preservation can save state before stopping.
- [x] Tests do not require real LLM or CodeGraph.
- [x] Empty repo can initialize with a goal.
- [x] PlanGraph can be created without CodeGraph.
- [x] Large goals can be chunked into structured planning state.
- [x] Planning can preserve state near context limit.
- [x] Task DAG can be generated incrementally.
- [x] Scaffold handoff to CodeGraph is explicitly defined.
- [x] Resume can continue from saved state.
- [x] Workflow gates (test, review, worklog, rollback, next) are integrated.
- [x] E2E dry-run tests verify both paths.

## Conclusion

Tasks 051–070 deliver a bounded, configurable, and recoverable coding runtime. The N-context design makes cc-mini usable with 4K, 32K, or 200K models, local or remote, with or without CodeGraph. Phase 1 is complete.
