# cc-mini Phase 3 Continuity and Maintenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve long-session coherence by introducing a durable workspace semantic artifact layer with explicit `derived` and `manual` strata, and making drift recovery, reconcile, and maintenance advisory and manual-first instead of silently mutating source files.

**Architecture:** Build on the coding workflow from Phase 2 and make continuity a product feature. The key persistent unit is a workspace semantic artifact store that records high-level entity relations, task spine snapshots, Phase 2 convergence records, drift summaries, and maintenance candidates. Artifacts are split into `derived` records produced from workflow output and `manual` records added by users, with `derived` taking precedence for reconstruction while `manual` remains available for annotations and local corrections. Reconcile and maintenance read those artifacts and source hashes to generate suggestions, but they do not rewrite original files unless a later phase explicitly approves that behavior.

**Execution Split:** The task-level execution plan for this phase lives in [2026-04-21-cc-mini-phase3-execution-split.md](./2026-04-21-cc-mini-phase3-execution-split.md). Use that file for subagent or GSD task transcription; keep this file as the higher-level phase boundary reference.

**Tech Stack:** Python 3.11, pytest, argparse, rich

---

## Direction Check

Phase 3 is about keeping a long local coding session coherent over time. It should not add more startup complexity; it should add resilience after the workflow is already in motion.

The important design choice from the user is:

- manual-first maintenance
- workspace artifacts as the durable high-level semantic layer
- no direct mutation of original source files unless the user explicitly approves it later
- `derived` and `manual` artifact strata must be preserved separately, with explicit source and priority labels

## Boundary With Phase 2

- Phase 2 emits the patch transaction summary and convergence record.
- Phase 3 persists those outputs into workspace semantic artifacts and can also store manual annotations in a separate stratum.
- Phase 3 may suggest maintenance or recovery, but it does not perform source writes.
- If a user wants to change source files again, that should re-enter Phase 2, not happen implicitly here.

---

## Milestone 1: Workspace Semantic Artifact Layer

### Task M3-T1: Add a workspace semantic artifact store for entity relations and task spine snapshots

**Goal:** Create a durable workspace-level artifact store that records high-level semantics such as entity relations, task spine snapshots, Phase 2 convergence records, drift summaries, and optional manual annotations without modifying source files.

**Files:**
- Create: `src/core/wiki/semantic_artifacts.py`
- Create: `tests/test_semantic_artifacts.py`

**Allowed changes:**
- Define semantic artifact dataclasses and persistence helpers.
- Store artifacts under `.cc-mini/wiki/artifacts/`.
- Represent entity relations, task spine snapshots, drift notes, and maintenance candidates as workspace artifacts.
- Keep `derived` and `manual` records separate, with source labels and priority metadata.

**Forbidden changes:**
- Do not change source files as part of the artifact store itself.
- Do not add automatic maintenance or cleanup here.
- Do not change startup behavior.

**Explicit dependencies:** Phase 2 convergence output

**Verification:**
- Static check: `rg -n "semantic_artifacts|artifacts/|task spine|entity relation" src/core/wiki/semantic_artifacts.py tests/test_semantic_artifacts.py`
- Minimal run: `python -m pytest tests/test_semantic_artifacts.py -v`
- Related tests: `python -m pytest tests/test_wiki_phase2.py tests/test_main.py -v`

**Done criteria:**
- High-level semantic state can be stored and loaded independently of the original source files.
- The artifact layer is clearly separate from the code-edit layer.

**Step sketch:**

```python
def test_semantic_artifact_store_round_trip(tmp_path):
    store = SemanticArtifactStore(tmp_path)
    artifact = TaskSpineArtifact(
        task_id="task-1",
        global_goal="Keep the task thread",
        step_goal="Recover semantic state",
    )

    path = store.save_task_spine(artifact)
    restored = store.load_task_spine(path.stem)

    assert restored.task_id == "task-1"
    assert restored.step_goal == "Recover semantic state"
```

### Task M3-T2: Route reconcile and maintenance through artifact projections

**Goal:** Make drift detection and maintenance suggestion logic read from workspace artifacts and source hashes so they can explain what changed without mutating the original files.

**Files:**
- Modify: `src/core/wiki/reconcile.py`
- Modify: `src/core/wiki/maintenance.py`
- Modify: `tests/test_maintenance.py`

**Allowed changes:**
- Use semantic artifacts as the primary projection for drift and maintenance suggestions.
- Keep reconcile and maintenance advisory and manual-first.
- Continue to compare source hashes when useful, but never auto-edit source files.
- Allow threshold-based maintenance suggestions, but require explicit confirmation before any follow-up action.

**Forbidden changes:**
- Do not auto-cleanup or archive on startup.
- Do not rewrite source files implicitly during reconcile or maintenance scans.
- Do not hide manual confirmation behind a background action.

**Explicit dependencies:** `M3-T1`

**Verification:**
- Static check: `rg -n "scan_for_stale|run_maintenance|semantic artifact|drift" src/core/wiki/reconcile.py src/core/wiki/maintenance.py tests/test_maintenance.py`
- Minimal run: `python -m pytest tests/test_maintenance.py -v`
- Related tests: `python -m pytest tests/test_semantic_artifacts.py -v`

**Done criteria:**
- Drift is surfaced as a suggestion, not a silent side effect.
- Maintenance reports can be generated without altering original files.

---

## Milestone 2: Manual Recovery and Maintenance Surfaces

### Task M3-T3: Add explicit `/reconcile` and `/maintenance` command surfaces

**Goal:** Give the user explicit commands to inspect drift and maintenance candidates from the workspace semantic artifacts, while keeping the actions manual, reviewable, and split between derived and manual layers.

**Files:**
- Modify: `src/core/commands.py`
- Modify: `README.md`
- Modify: `tests/test_commands.py`

**Allowed changes:**
- Add or improve command/help text for reconcile and maintenance surfaces.
- Make the output summarize drift candidates, semantic artifact state, and suggested follow-up actions.
- Surface whether each item came from `derived` or `manual` strata.
- Keep the command behavior advisory; do not apply cleanup automatically.

**Forbidden changes:**
- Do not make maintenance automatic by default.
- Do not mutate original files from these commands.
- Do not confuse these surfaces with the coding workflow.

**Explicit dependencies:** `M3-T2`

**Verification:**
- Static check: `rg -n "reconcile|maintenance|semantic artifact|drift" src/core/commands.py README.md tests/test_commands.py`
- Minimal run: `python -m pytest tests/test_commands.py -v`
- Related tests: `python -m pytest tests/test_maintenance.py tests/test_semantic_artifacts.py -v`

**Done criteria:**
- Users can ask for recovery and maintenance suggestions intentionally.
- The docs explain that these are manual surfaces, not background behavior.

### Task M3-T4: Add long-session semantic recovery smoke coverage

**Goal:** Prove that repeated turns preserve the task spine, semantic artifact state, manual annotations, and drift suggestions without losing the main coding thread.

**Files:**
- Create: `tests/test_wiki_phase3.py`

**Allowed changes:**
- Add a smoke test that simulates a long-running task and repeated updates to the semantic artifact layer.
- Assert the system can still point back to the main task and report drift suggestions.
- Assert `derived` and `manual` records remain distinct across repeated turns.
- Keep the smoke test deterministic and light.

**Forbidden changes:**
- Do not add a daemon or watcher.
- Do not require an external service.
- Do not expand into a broad lifecycle suite.

**Explicit dependencies:** `M3-T1`, `M3-T2`, `M3-T3`

**Verification:**
- Static check: `rg -n "recovery|semantic artifact|drift|task spine" tests/test_wiki_phase3.py src/core/wiki/semantic_artifacts.py`
- Minimal run: `python -m pytest tests/test_wiki_phase3.py -v`
- Related tests: `python -m pytest tests/test_semantic_artifacts.py tests/test_maintenance.py -v`

**Done criteria:**
- A long session can be inspected and recovered without losing the main task line.
- Semantic artifacts remain the durable view of the higher-level workflow state.

---

## Execution Notes

- Keep each task small and isolated.
- If a task starts to pull in runtime-isolation or general-agent expansion, stop and split it.
- Preserve the already-validated Phase 1 startup path and the Phase 2 patch/converge model.
- Prefer tests first; only add helpers when the tests show a real boundary gap.
