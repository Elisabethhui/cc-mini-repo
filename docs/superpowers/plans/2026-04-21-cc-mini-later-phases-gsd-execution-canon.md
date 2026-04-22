# cc-mini Later Phases GSD Execution Canon

> **Purpose:** This document is the transcribe-ready execution canon for cc-mini phases after Phase 1. Use it to turn the approved phase plans into GSD tasks without re-litigating architecture during execution.

**Goal:** Provide one canonical execution order and task-splitting rule set for Phase 2 through Phase 5 so future implementation work stays small, phase-correct, and easy to assign to subagents.

**Architecture:** Keep the later phases separated by responsibility, not by convenience. Phase 2 owns the coding transaction layer, Phase 3 owns durable semantic continuity, Phase 4 owns runtime isolation, and Phase 5 owns broader agent expansion. Each phase should be executed from its own plan file, but the tasks below define the order and the boundary that GSD workers should preserve while transcribing them into runnable work.

**Tech Stack:** Python 3.11, pytest, argparse, rich, the existing cc-mini CLI/runtime

---

## Canonical Phase Split

- **Phase 2:** explicit patching, rollback, confirmation, convergence record
- **Phase 3:** workspace semantic artifacts, drift projections, manual-first reconcile / maintenance, plus separate `derived` and `manual` strata
- **Phase 4:** visible runtime separation between `standard` and `wiki_strict` with shared primitives only where harmless
- **Phase 5:** coding-adjacent expansion first, then broader general-agent capability

The task-level execution split for Phase 5 lives in [2026-04-21-cc-mini-phase5-execution-split.md](./2026-04-21-cc-mini-phase5-execution-split.md).

## Phase 3 Detail Map

- Use [2026-04-21-cc-mini-phase3-continuity-maintenance.md](./2026-04-21-cc-mini-phase3-continuity-maintenance.md) for the high-level phase boundary.
- Use [2026-04-21-cc-mini-phase3-execution-split.md](./2026-04-21-cc-mini-phase3-execution-split.md) for task-level execution.

## Phase 4 Detail Map

- Use [2026-04-21-cc-mini-phase4-runtime-isolation.md](./2026-04-21-cc-mini-phase4-runtime-isolation.md) for the high-level phase boundary.
- Use [2026-04-21-cc-mini-phase4-execution-split.md](./2026-04-21-cc-mini-phase4-execution-split.md) for task-level execution.

## Hard Rules For All Later-Phase Tasks

- One task changes one behavior.
- One task should usually touch 1-3 files.
- A task must not cross a phase boundary.
- Every task must state:
  - files
  - allowed changes
  - forbidden changes
  - explicit dependencies
  - verification
  - done criteria
- Verification must always include:
  - static check
  - minimal run
  - related tests when they exist
- If a task starts to pull in the next phase, split it.

## Recommended Execution Order

1. Phase 2 task M2-T1
2. Phase 2 task M2-T2
3. Phase 2 task M2-T3
4. Phase 2 task M2-T4
5. Phase 3 task M3-T1
6. Phase 3 task M3-T2
7. Phase 3 task M3-T3
8. Phase 3 task M3-T4
9. Phase 4 task M4-T1
10. Phase 4 task M4-T2
11. Phase 4 task M4-T3
12. Phase 4 task M4-T4
13. Phase 5 task M5-T1
14. Phase 5 task M5-T2
15. Phase 5 task M5-T3

## Phase 2 Execution Canon

### M2-T1: Patch session manifest and rollback snapshot helper

- **Files:** `src/core/wiki/patch_session.py`, `tests/test_patch_session.py`
- **Behavior change:** persist a patch session manifest plus rollback metadata
- **Do not:** wire CLI, auto-patch, maintenance, or source mutations
- **Depends on:** Phase 1 `TaskPack` and `EditSpec`
- **Verify:** `rg -n "PatchSession|RollbackSnapshot|patch session" src/core/wiki/patch_session.py tests/test_patch_session.py`
  - `python -m pytest tests/test_patch_session.py -v`
  - `python -m pytest tests/test_main.py tests/test_commands.py -v`

### M2-T2: Explicit `/patch` command for bounded multi-file edits

- **Files:** `src/core/commands.py`, `src/core/wiki/patch_session.py`, `tests/test_wiki_phase2.py`
- **Behavior change:** user-triggered patch entrypoint with rollback-first safety
- **Do not:** make patch automatic, expand into maintenance, or write outside the declared patch session
- **Depends on:** `M2-T1`
- **Verify:** `rg -n "patch|PatchSession|rollback|EditSpec" src/core/commands.py src/core/wiki/patch_session.py tests/test_wiki_phase2.py`
  - `python -m pytest tests/test_wiki_phase2.py -v`
  - `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

### M2-T3: Confirmation-based convergence record step

- **Files:** `src/core/wiki/post_edit_guard.py`, `src/core/wiki/convergence_record.py`, `tests/test_wiki_phase2.py`
- **Behavior change:** `post_edit` emits a confirmation-gated convergence record
- **Do not:** rewrite source files again, add maintenance/archive behavior, or create a durable semantic store
- **Depends on:** `M2-T2`
- **Verify:** `rg -n "CompletionState|convergence_record|post_edit|rollback" src/core/wiki/post_edit_guard.py src/core/wiki/convergence_record.py tests/test_wiki_phase2.py`
  - `python -m pytest tests/test_wiki_phase2.py -v`
  - `python -m pytest tests/test_commands.py tests/test_main.py -v`

### M2-T4: Coding-loop smoke coverage and docs alignment

- **Files:** `README.md`, `src/core/commands.py`, `tests/test_wiki_phase2.py`
- **Behavior change:** expose the full Phase 2 patch/confirm/rollback loop in docs and smoke tests
- **Do not:** expand into Phase 3 surfaces or reframe `standard`
- **Depends on:** `M2-T2`, `M2-T3`
- **Verify:** `rg -n "patch|post_edit|rollback|converge|semantic" README.md src/core/commands.py tests/test_wiki_phase2.py`
  - `python -m pytest tests/test_wiki_phase2.py -v`
  - `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

## Phase 3 Execution Canon

### M3-T1: Workspace semantic artifact store

- **Files:** `src/core/wiki/semantic_artifacts.py`, `tests/test_semantic_artifacts.py`
- **Behavior change:** durable workspace-level semantic artifacts with distinct `derived` and `manual` strata
- **Do not:** mutate source files, add watchers, or change startup behavior
- **Depends on:** Phase 2 convergence output
- **Verify:** `rg -n "semantic_artifacts|artifacts/|task spine|entity relation" src/core/wiki/semantic_artifacts.py tests/test_semantic_artifacts.py`
  - `python -m pytest tests/test_semantic_artifacts.py -v`
  - `python -m pytest tests/test_wiki_phase2.py tests/test_main.py -v`

### M3-T2: Drift and maintenance projections from artifacts

- **Files:** `src/core/wiki/reconcile.py`, `src/core/wiki/maintenance.py`, `tests/test_maintenance.py`
- **Behavior change:** turn drift and maintenance into artifact-backed suggestions with threshold-based prompts
- **Do not:** auto-edit source, auto-cleanup on startup, or hide manual confirmation
- **Depends on:** `M3-T1`
- **Verify:** `rg -n "scan_for_stale|run_maintenance|semantic artifact|drift" src/core/wiki/reconcile.py src/core/wiki/maintenance.py tests/test_maintenance.py`
  - `python -m pytest tests/test_maintenance.py -v`
  - `python -m pytest tests/test_semantic_artifacts.py -v`

### M3-T3: Explicit `/reconcile` and `/maintenance` surfaces

- **Files:** `src/core/commands.py`, `README.md`, `tests/test_commands.py`
- **Behavior change:** give the user manual-first recovery and maintenance entrypoints that expose artifact provenance
- **Do not:** mutate original files or merge this into coding workflow behavior
- **Depends on:** `M3-T2`
- **Verify:** `rg -n "reconcile|maintenance|semantic artifact|drift" src/core/commands.py README.md tests/test_commands.py`
  - `python -m pytest tests/test_commands.py -v`
  - `python -m pytest tests/test_maintenance.py tests/test_semantic_artifacts.py -v`

### M3-T4: Long-session semantic recovery smoke coverage

- **Files:** `tests/test_wiki_phase3.py`
- **Behavior change:** prove repeated turns preserve the task spine and drift suggestions
- **Do not:** add a daemon, external service, or broad lifecycle suite
- **Depends on:** `M3-T1`, `M3-T2`, `M3-T3`
- **Verify:** `rg -n "recovery|semantic artifact|drift|task spine" tests/test_wiki_phase3.py src/core/wiki/semantic_artifacts.py`
  - `python -m pytest tests/test_wiki_phase3.py -v`
  - `python -m pytest tests/test_semantic_artifacts.py tests/test_maintenance.py -v`

## Phase 4 Execution Canon

### M4-T1: Split mode-specific runtime setup paths

- **Files:** `src/core/main.py`, `src/core/config.py`, `src/core/permissions.py`
- **Behavior change:** make `standard` and `wiki_strict` runtime setup visibly different while still allowing harmless shared primitives
- **Do not:** break Phase 1/2 behavior or invent a new user-visible mode
- **Depends on:** Phase 2 and Phase 3 completion
- **Verify:** `rg -n "standard|wiki_strict|resolve_run_mode|PermissionChecker" src/core/main.py src/core/config.py src/core/permissions.py`
  - `python -m pytest tests/test_main.py tests/test_config.py -v`
  - `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

### M4-T2: Separate prompt and state assumptions by mode

- **Files:** `src/core/context.py`, `src/core/flow_state.py`, `tests/test_main.py`
- **Behavior change:** keep `standard` from inheriting `wiki_strict` assumptions and avoid introducing a second full runtime stack
- **Do not:** add new lifecycle behavior or make `standard` wiki-aware
- **Depends on:** `M4-T1`
- **Verify:** `rg -n "plan mode|wiki_strict|standard|flow_state|prompt" src/core/context.py src/core/flow_state.py tests/test_main.py`
  - `python -m pytest tests/test_main.py -k standard -v`
  - `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

### M4-T3: Cross-mode isolation regression coverage

- **Files:** `tests/test_mode_isolation.py`
- **Behavior change:** prove later-phase surfaces do not leak into `standard`
- **Do not:** broaden the suite into a giant integration test
- **Depends on:** `M4-T1`, `M4-T2`
- **Verify:** `rg -n "analysis-first|later-phase|standard|wiki_strict" tests/test_mode_isolation.py src/core/main.py`
  - `python -m pytest tests/test_mode_isolation.py -v`
  - `python -m pytest tests/test_main.py tests/test_commands.py -v`

### M4-T4: Documentation of the isolation boundary

- **Files:** `README.md`, `docs/superpowers/specs/2026-04-20-cc-mini-32k-wiki-strict-design.md`
- **Behavior change:** explain the final mode split in user-facing language
- **Do not:** reopen Phase 1 or change the product direction
- **Depends on:** `M4-T3`
- **Verify:** `rg -n "standard|wiki_strict|isolation|Phase 4" README.md docs/superpowers/specs/2026-04-20-cc-mini-32k-wiki-strict-design.md`
  - `python -m pytest tests/test_mode_isolation.py tests/test_main.py -v`
  - `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

## Phase 5 Execution Canon

### M5-T1: Broaden task intake beyond coding-only requests

- **Files:** `src/core/commands.py`, `src/core/coordinator.py`, `tests/test_commands.py`
- **Behavior change:** accept broader task descriptions and route them intentionally, preferring coding-adjacent tasks first
- **Do not:** break coding workflows or weaken `standard`
- **Depends on:** Phases 2-4 completion
- **Verify:** `rg -n "coordinator|task|coding|general" src/core/commands.py src/core/coordinator.py tests/test_commands.py`
  - `python -m pytest tests/test_commands.py -v`
  - `python -m pytest tests/test_mode_isolation.py tests/test_main.py -v`

### M5-T2: Extend orchestration to non-coding workflows

- **Files:** `src/core/worker_manager.py`, `src/core/tools/agent.py`, `tests/test_worker_manager.py`
- **Behavior change:** reuse the worker model for broader tasks without unbounded routing, while leaving room for planning/document tasks
- **Do not:** fan out every task, move all logic into orchestration, or weaken permissions
- **Depends on:** `M5-T1`
- **Verify:** `rg -n "WorkerManager|AgentTool|SendMessageTool|TaskStopTool" src/core/worker_manager.py src/core/tools/agent.py tests/test_worker_manager.py`
  - `python -m pytest tests/test_worker_manager.py -v`
  - `python -m pytest tests/test_commands.py tests/test_mode_isolation.py -v`

### M5-T3: General-agent evaluation and guardrail coverage

- **Files:** `tests/test_general_agent.py`, `README.md`
- **Behavior change:** make broader agent behavior observable and bounded, with the first wave staying near coding
- **Do not:** promise broad autonomy without guardrails or drop coding-specific tests
- **Depends on:** `M5-T1`, `M5-T2`
- **Verify:** `rg -n "general agent|routing|guardrail|coding" README.md tests/test_general_agent.py`
  - `python -m pytest tests/test_general_agent.py -v`
  - `python -m pytest tests/test_mode_isolation.py tests/test_permissions.py -v`

## Transcription Notes For GSD

- Use this canon to split work into tasks, then copy the task wording into the GSD plan.
- Keep file ownership disjoint when possible.
- Prefer one subagent per task when tasks are independent.
- If a task depends on a new helper, create the helper in the same task only when the helper is directly required for that behavior change.
- If the code path starts to mix phases, stop and split the task.
