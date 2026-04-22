# cc-mini Phase 3 Execution Split Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Phase 3 semantic continuity layer as a strict `derived/manual` artifact system, then expose read-only reconcile and maintenance projections that never mutate source files.

**Architecture:** Phase 3 is the workspace-semantic layer above Phase 2. `derived` artifacts are created from Phase 2 convergence output and act as the reconstruction baseline. `manual` artifacts are user-authored overlays that stay separate and never replace derived data implicitly. Any command surface in this phase is view-only or suggestion-only. If a task would mutate source files, archive content, or update indexes as a side effect, it belongs to a later phase or must be split out.

**Tech Stack:** Python 3.11, pytest, argparse, rich

---

## Execution Order

1. Task M3-1: Artifact store core
2. Task M3-2: Derived ingest from Phase 2 convergence
3. Task M3-3: Manual annotation layer
4. Task M3-4: Read-only reconcile and maintenance projections
5. Task M3-5: View-only command surfaces and docs
6. Task M3-6: Long-session regression coverage

---

## Task M3-1: Artifact Store Core

**Goal:** Create the smallest persistent artifact store that can save and load `derived` and `manual` records independently.

**Files:**
- Create: `src/core/wiki/semantic_artifacts.py`
- Create: `tests/test_semantic_artifacts.py`

**Allowed changes:**
- Define `ArtifactRecord` and `SemanticArtifactStore`.
- Persist artifacts under `.cc-mini/wiki/artifacts/derived/` and `.cc-mini/wiki/artifacts/manual/`.
- Maintain an index file for lookup without merging layers.

**Forbidden changes:**
- Do not touch source files.
- Do not add reconcile, maintenance, or command routing.
- Do not blur `derived` and `manual` into a single bucket.

**Explicit dependencies:** Phase 2 convergence record output shape

**Verification:**
- Static check: `rg -n "ArtifactRecord|SemanticArtifactStore|derived|manual|index.json" src/core/wiki/semantic_artifacts.py tests/test_semantic_artifacts.py`
- Minimal run: `python -m pytest tests/test_semantic_artifacts.py -v`
- Related tests: `python -m pytest tests/test_wiki_phase2.py -v`

**Done criteria:**
- A derived artifact and a manual artifact can be written and loaded separately.
- The store can list records by layer without merging them.

**Step 1: Write the failing test**

```python
def test_store_separates_layers(tmp_path):
    store = SemanticArtifactStore(tmp_path)

    derived = ArtifactRecord(
        artifact_id="conv-1",
        layer="derived",
        kind="convergence_record",
        task_id="task-1",
        source="phase2",
        priority=10,
        payload={"summary": "patch accepted"},
    )
    manual = ArtifactRecord(
        artifact_id="note-1",
        layer="manual",
        kind="annotation",
        task_id="task-1",
        source="user",
        priority=1,
        payload={"note": "double-check naming"},
    )

    store.save(derived)
    store.save(manual)

    assert store.load("derived", "conv-1").artifact_id == "conv-1"
    assert store.load("manual", "note-1").artifact_id == "note-1"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_semantic_artifacts.py::test_store_separates_layers -v`

Expected: FAIL with `SemanticArtifactStore` not defined or missing layer-specific persistence.

**Step 3: Write minimal implementation**

Implement only the artifact record, store, save/load, and layer-specific file layout needed for the test.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_semantic_artifacts.py::test_store_separates_layers -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/core/wiki/semantic_artifacts.py tests/test_semantic_artifacts.py
git commit -m "feat: add layered semantic artifact store"
```

---

## Task M3-2: Derived Ingest from Phase 2 Convergence

**Goal:** Convert Phase 2 convergence output into derived semantic artifacts without changing source files.

**Files:**
- Modify: `src/core/wiki/semantic_artifacts.py`
- Modify: `tests/test_semantic_artifacts.py`

**Allowed changes:**
- Add an ingest helper that accepts the Phase 2 convergence input contract.
- Record task spine and convergence summary as derived artifacts.
- Keep derived writes deterministic and repeatable.

**Forbidden changes:**
- Do not write manual annotations here.
- Do not modify source files or add commands.
- Do not depend on Phase 2 internals beyond the minimal input contract.

**Explicit dependencies:** `M3-1`

**Verification:**
- Static check: `rg -n "ingest_convergence_record|task spine|convergence|derived" src/core/wiki/semantic_artifacts.py tests/test_semantic_artifacts.py`
- Minimal run: `python -m pytest tests/test_semantic_artifacts.py -v`
- Related tests: `python -m pytest tests/test_wiki_phase2.py -v`

**Done criteria:**
- A convergence record can be ingested into the derived layer.
- The result can be reloaded with the same task id and provenance.

**Step 1: Write the failing test**

```python
def test_ingest_convergence_record_creates_derived_snapshot(tmp_path):
    store = SemanticArtifactStore(tmp_path)
    record = {
        "task_id": "task-1",
        "confirmed": True,
        "summary": {"files": ["src/app.py"]},
        "references": ["src/app.py"],
    }

    ids = store.ingest_convergence_record(record)

    assert any(item.kind == "convergence_record" for item in ids)
    assert any(item.layer == "derived" for item in store.list_layer("derived"))
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_semantic_artifacts.py::test_ingest_convergence_record_creates_derived_snapshot -v`

Expected: FAIL with missing ingest helper or missing derived artifact output.

**Step 3: Write minimal implementation**

Add the ingest helper and the derived artifact construction needed for the test.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_semantic_artifacts.py::test_ingest_convergence_record_creates_derived_snapshot -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/core/wiki/semantic_artifacts.py tests/test_semantic_artifacts.py
git commit -m "feat: ingest convergence records into derived artifacts"
```

---

## Task M3-3: Manual Annotation Layer

**Goal:** Let users attach manual notes or corrections without overwriting derived artifacts or source files.

**Files:**
- Modify: `src/core/wiki/semantic_artifacts.py`
- Modify: `tests/test_semantic_artifacts.py`

**Allowed changes:**
- Add manual annotation helpers that always write to the manual layer.
- Preserve `source="user"` and a low-priority overlay model.
- Add lookup helpers that return both derived and manual records for the same task.

**Forbidden changes:**
- Do not change the derived layer format.
- Do not infer that a manual note rewrites source files.
- Do not auto-promote a manual note into a derived record.

**Explicit dependencies:** `M3-1`

**Verification:**
- Static check: `rg -n "add_manual_annotation|manual|annotation|priority|provenance" src/core/wiki/semantic_artifacts.py tests/test_semantic_artifacts.py`
- Minimal run: `python -m pytest tests/test_semantic_artifacts.py -v`
- Related tests: `python -m pytest tests/test_wiki_phase2.py -v`

**Done criteria:**
- Manual annotations persist separately from derived artifacts.
- A task can have both derived and manual records, and callers can see both.

**Step 1: Write the failing test**

```python
def test_manual_annotation_does_not_replace_derived(tmp_path):
    store = SemanticArtifactStore(tmp_path)
    store.save(
        ArtifactRecord(
            artifact_id="conv-1",
            layer="derived",
            kind="task_spine",
            task_id="task-1",
            source="phase2",
            priority=10,
            payload={"step_goal": "recover"},
        )
    )
    store.add_manual_annotation(
        task_id="task-1",
        note="prefer shorter step labels",
    )

    records = store.list_for_task("task-1")
    assert {r.layer for r in records} == {"derived", "manual"}
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_semantic_artifacts.py::test_manual_annotation_does_not_replace_derived -v`

Expected: FAIL with missing manual annotation support or missing layered lookup.

**Step 3: Write minimal implementation**

Add the manual layer write path and a lookup helper that returns both layers.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_semantic_artifacts.py::test_manual_annotation_does_not_replace_derived -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/core/wiki/semantic_artifacts.py tests/test_semantic_artifacts.py
git commit -m "feat: add manual semantic annotations"
```

---

## Task M3-4: Read-Only Reconcile and Maintenance Projections

**Goal:** Make reconcile and maintenance read `derived` plus `manual` artifacts and emit suggestions without mutating source files.

**Files:**
- Modify: `src/core/wiki/reconcile.py`
- Modify: `src/core/wiki/maintenance.py`
- Modify: `tests/test_maintenance.py`

**Allowed changes:**
- Use semantic artifacts as the primary projection for drift and maintenance suggestions.
- Surface threshold-based suggestions when stale or drifted data is detected.
- Keep source hash checks as read-only signals.

**Forbidden changes:**
- Do not auto-edit source files.
- Do not auto-run maintenance from startup.
- Do not collapse the manual layer into the derived layer.
- Do not add any file-mutating action path, even behind a flag.

**Explicit dependencies:** `M3-1`, `M3-2`, `M3-3`

**Verification:**
- Static check: `rg -n "semantic artifact|derived|manual|drift|maintenance" src/core/wiki/reconcile.py src/core/wiki/maintenance.py tests/test_maintenance.py`
- Minimal run: `python -m pytest tests/test_maintenance.py -v`
- Related tests: `python -m pytest tests/test_semantic_artifacts.py -v`

**Done criteria:**
- Drift and maintenance reports can explain whether their input came from derived or manual artifacts.
- No source file is modified by reconcile or maintenance projections.

**Step 1: Write the failing test**

```python
def test_reconcile_uses_artifact_projection_without_writes(tmp_path):
    engine = ReconcileEngine(tmp_path)
    result = engine.reconcile(dry_run=True)

    assert result["dry_run"] is True
    assert "items" in result
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_maintenance.py::test_reconcile_uses_artifact_projection_without_writes -v`

Expected: FAIL with missing artifact projection behavior or incompatible reconcile wiring.

**Step 3: Write minimal implementation**

Add the read-only projection path and keep all write paths out of this task.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_maintenance.py::test_reconcile_uses_artifact_projection_without_writes -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/core/wiki/reconcile.py src/core/wiki/maintenance.py tests/test_maintenance.py
git commit -m "feat: make reconcile and maintenance projection-only"
```

---

## Task M3-5: View-Only Command Surfaces and Docs

**Goal:** Expose `/reconcile` and `/maintenance` as reviewable surfaces that show artifact provenance and require explicit follow-up, without offering any execution path.

**Files:**
- Modify: `src/core/commands.py`
- Modify: `README.md`
- Modify: `tests/test_commands.py`

**Allowed changes:**
- Add or improve command/help text for reconcile and maintenance surfaces.
- Display whether items came from `derived` or `manual` strata.
- Keep the commands view-only and advisory.

**Forbidden changes:**
- Do not mutate original files from these commands.
- Do not automatically continue into repair actions.
- Do not expose an execution command, confirm-and-run flow, or background mutation hook from these surfaces.
- Do not hide the provenance labels.

**Explicit dependencies:** `M3-4`

**Verification:**
- Static check: `rg -n "reconcile|maintenance|derived|manual|artifact" src/core/commands.py README.md tests/test_commands.py`
- Minimal run: `python -m pytest tests/test_commands.py -v`
- Related tests: `python -m pytest tests/test_maintenance.py tests/test_semantic_artifacts.py -v`

**Done criteria:**
- Users can intentionally ask for recovery/maintenance suggestions.
- The docs make the two artifact strata obvious.

**Step 1: Write the failing test**

```python
def test_help_mentions_artifact_strata():
    output = render_help_text()
    assert "derived" in output
    assert "manual" in output
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_commands.py::test_help_mentions_artifact_strata -v`

Expected: FAIL with missing provenance wording in help output.

**Step 3: Write minimal implementation**

Update command help and README wording only; do not add any action path.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_commands.py::test_help_mentions_artifact_strata -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/core/commands.py README.md tests/test_commands.py
git commit -m "feat: document view-only phase 3 surfaces"
```

---

## Task M3-6: Long-Session Recovery Smoke Coverage

**Goal:** Prove repeated turns preserve the task spine, the derived/manual split, and the main task thread.

**Files:**
- Create: `tests/test_wiki_phase3.py`

**Allowed changes:**
- Add a smoke test that simulates repeated updates to the semantic artifact layer.
- Assert the system can still point back to the main task and report drift suggestions.
- Keep the smoke test deterministic and light.

**Forbidden changes:**
- Do not add a daemon or watcher.
- Do not require an external service.
- Do not expand into a broad lifecycle suite.

**Explicit dependencies:** `M3-1`, `M3-2`, `M3-3`, `M3-4`, `M3-5`

**Verification:**
- Static check: `rg -n "recovery|semantic artifact|drift|task spine|derived|manual" tests/test_wiki_phase3.py src/core/wiki/semantic_artifacts.py`
- Minimal run: `python -m pytest tests/test_wiki_phase3.py -v`
- Related tests: `python -m pytest tests/test_semantic_artifacts.py tests/test_maintenance.py -v`

**Done criteria:**
- A long session can be inspected and recovered without losing the main task line.
- Derived and manual records remain distinct across repeated turns.

**Step 1: Write the failing test**

```python
def test_long_session_preserves_derived_and_manual_layers(tmp_path):
    store = SemanticArtifactStore(tmp_path)
    store.save(
        ArtifactRecord(
            artifact_id="conv-1",
            layer="derived",
            kind="task_spine",
            task_id="task-1",
            source="phase2",
            priority=10,
            payload={"step_goal": "recover"},
        )
    )
    store.add_manual_annotation(task_id="task-1", note="retain this path")

    records = store.list_for_task("task-1")
    assert {r.layer for r in records} == {"derived", "manual"}
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_wiki_phase3.py::test_long_session_preserves_derived_and_manual_layers -v`

Expected: FAIL with missing phase 3 store or lookup support.

**Step 3: Write minimal implementation**

Add the smoke test support only after Tasks M3-1 through M3-5 are in place.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_wiki_phase3.py::test_long_session_preserves_derived_and_manual_layers -v`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_wiki_phase3.py
git commit -m "test: cover derived and manual phase 3 continuity"
```

---

## Execution Notes

- Keep `derived` and `manual` strictly separate at the persistence layer.
- Treat reconcile and maintenance as read-only projection surfaces in this phase.
- Do not allow any task to introduce source mutation, archive operations, or background cleanup.
- If a later need for execution appears, split it into a later phase instead of widening Phase 3.

