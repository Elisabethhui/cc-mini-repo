# cc-mini Phase 3 Derived/Manual Artifact Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a durable workspace semantic artifact layer with explicit `derived` and `manual` strata so long-session continuity can be recovered, inspected, and maintained without mutating source files.

**Architecture:** Phase 3 consumes the Phase 2 patch/convergence output and turns it into a persistent workspace view. `derived` artifacts are generated from workflow output and used as the reconstruction baseline. `manual` artifacts are user-authored annotations that stay separate, carry their own provenance, and never overwrite the derived layer implicitly. Reconcile and maintenance read both strata, but any source-file change still belongs to Phase 2 or later.

**Tech Stack:** Python 3.11, pytest, argparse, rich

---

## Minimal Artifact Contract

### Phase 2 convergence input contract

Phase 3 only depends on a small, stable subset of Phase 2 output. A convergence record ingested by this phase must expose:

- `task_id`
- `confirmed`
- `summary`
- `references`

Optional fields may be preserved if present, but Phase 3 tasks must not depend on them.

### Artifact record shape

Each persisted artifact should carry:

- `artifact_id`
- `layer`: `derived` or `manual`
- `kind`: `convergence_record`, `task_spine`, `drift_note`, `maintenance_candidate`, `annotation`
- `task_id`
- `source`
- `priority`
- `created_at`
- `updated_at`
- `payload`
- `references`

### Storage layout

- `.cc-mini/wiki/artifacts/derived/`
- `.cc-mini/wiki/artifacts/manual/`
- `.cc-mini/wiki/artifacts/index.json`

### Priority rule

- `derived` is the baseline reconstruction source.
- `manual` is an overlay for annotations and corrections.
- If both exist for the same subject, projections must show both and label the source clearly.
- Manual content does not rewrite or replace source files automatically.

---

## Milestone 1: Artifact Store Core

### Task M3-E1: Define the layered semantic artifact store and persistence format

**Goal:** Create the smallest durable artifact store that can save and load `derived` and `manual` records independently.

**Files:**
- Create: `src/core/wiki/semantic_artifacts.py`
- Create: `tests/test_semantic_artifacts.py`

**Allowed changes:**
- Define artifact dataclasses, layer labels, and persistence helpers.
- Store artifacts under `.cc-mini/wiki/artifacts/`.
- Add an index file for listing and lookup.

**Forbidden changes:**
- Do not touch source files.
- Do not add reconcile, maintenance, or command routing yet.
- Do not blur `derived` and `manual` into one bucket.

**Explicit dependencies:** Phase 2 convergence record output shape

**Verification:**
- Static check: `rg -n "artifact_id|derived|manual|index.json|semantic_artifacts" src/core/wiki/semantic_artifacts.py tests/test_semantic_artifacts.py`
- Minimal run: `python -m pytest tests/test_semantic_artifacts.py -v`
- Related tests: `python -m pytest tests/test_wiki_phase2.py -v`

**Done criteria:**
- A derived artifact and a manual artifact can be written and loaded separately.
- The store can list records without merging the two layers.

**Step sketch:**

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

### Task M3-E2: Ingest Phase 2 convergence records into the derived layer

**Goal:** Turn Phase 2 convergence output into durable derived artifacts without changing source files.

**Files:**
- Modify: `src/core/wiki/semantic_artifacts.py`
- Modify: `tests/test_semantic_artifacts.py`

**Allowed changes:**
- Add a helper that converts a convergence record into derived artifacts.
- Record the task spine snapshot and convergence summary as derived data.
- Keep the derived write path deterministic.

**Forbidden changes:**
- Do not write manual annotations here.
- Do not modify source files or add commands.
- Do not promote derived records into editable source content.

**Explicit dependencies:** `M3-E1`

**Verification:**
- Static check: `rg -n "ingest|convergence|task spine|derived" src/core/wiki/semantic_artifacts.py tests/test_semantic_artifacts.py`
- Minimal run: `python -m pytest tests/test_semantic_artifacts.py -v`
- Related tests: `python -m pytest tests/test_wiki_phase2.py -v`

**Done criteria:**
- A convergence record can be imported into the derived layer.
- The resulting artifact set can be loaded back with the same task id and provenance.

**Step sketch:**

```python
def test_ingest_convergence_record_creates_derived_snapshot(tmp_path):
    store = SemanticArtifactStore(tmp_path)
    record = {
        "task_id": "task-1",
        "confirmed": True,
        "summary": {"files": ["src/app.py"]},
    }

    ids = store.ingest_convergence_record(record)

    assert any(item.kind == "convergence_record" for item in ids)
    assert any(item.layer == "derived" for item in store.list_layer("derived"))
```

### Task M3-E3: Add manual annotations as a separate layer with explicit provenance

**Goal:** Let users attach manual notes or corrections without overwriting derived artifacts or source files.

**Files:**
- Modify: `src/core/wiki/semantic_artifacts.py`
- Modify: `tests/test_semantic_artifacts.py`

**Allowed changes:**
- Add manual annotation helpers that always write to the manual layer.
- Preserve `source="user"` and a low-priority overlay model.
- Add lookup helpers that return both derived and manual records for the same subject.

**Forbidden changes:**
- Do not change the derived layer format.
- Do not infer that a manual note rewrites source files.
- Do not auto-promote a manual note into a derived record.

**Explicit dependencies:** `M3-E1`

**Verification:**
- Static check: `rg -n "manual|annotation|priority|provenance" src/core/wiki/semantic_artifacts.py tests/test_semantic_artifacts.py`
- Minimal run: `python -m pytest tests/test_semantic_artifacts.py -v`
- Related tests: `python -m pytest tests/test_wiki_phase2.py -v`

**Done criteria:**
- Manual annotations persist separately from derived artifacts.
- A subject can have both derived and manual records, and callers can see both.

**Step sketch:**

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

## Milestone 2: Reconcile and Maintenance Projections

### Task M3-E4: Route reconcile and maintenance through artifact projections

**Goal:** Make reconcile and maintenance read `derived` plus `manual` artifacts and emit suggestions without mutating source files or triggering any execution path.

**Files:**
- Modify: `src/core/wiki/reconcile.py`
- Modify: `src/core/wiki/maintenance.py`
- Modify: `tests/test_maintenance.py`

**Allowed changes:**
- Use semantic artifacts as the primary projection for drift and maintenance suggestions.
- Surface threshold-based suggestions when stale or drifted data is detected.
- Keep source hash checks as read-only signals.
- Keep the task read-only: projection and suggestion only.

**Forbidden changes:**
- Do not auto-edit source files.
- Do not auto-run maintenance from startup.
- Do not collapse the manual layer into the derived layer.
- Do not call any maintenance action that mutates files, archives content, or updates indexes.
- Do not add a `dry_run=False` execution path here.

**Explicit dependencies:** `M3-E1`, `M3-E2`, `M3-E3`

**Verification:**
- Static check: `rg -n "semantic artifact|derived|manual|drift|maintenance" src/core/wiki/reconcile.py src/core/wiki/maintenance.py tests/test_maintenance.py`
- Minimal run: `python -m pytest tests/test_maintenance.py -v`
- Related tests: `python -m pytest tests/test_semantic_artifacts.py -v`

**Done criteria:**
- Drift and maintenance reports can explain whether their input came from derived or manual artifacts.
- No source file is modified by reconcile or maintenance projections.

**Step sketch:**

```python
def test_reconcile_uses_artifact_projection_without_writes(tmp_path):
    engine = ReconcileEngine(tmp_path)
    result = engine.reconcile(dry_run=True)

    assert result["dry_run"] is True
    assert "items" in result
```

### Task M3-E5: Add manual-first recovery surfaces and documentation

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

**Explicit dependencies:** `M3-E4`

**Verification:**
- Static check: `rg -n "reconcile|maintenance|derived|manual|artifact" src/core/commands.py README.md tests/test_commands.py`
- Minimal run: `python -m pytest tests/test_commands.py -v`
- Related tests: `python -m pytest tests/test_maintenance.py tests/test_semantic_artifacts.py -v`

**Done criteria:**
- Users can intentionally ask for recovery/maintenance suggestions.
- The docs make the two artifact strata obvious.

## Milestone 3: Long-Session Regression Coverage

### Task M3-E6: Add long-session recovery smoke coverage for derived/manual continuity

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

**Explicit dependencies:** `M3-E1`, `M3-E2`, `M3-E3`, `M3-E4`, `M3-E5`

**Verification:**
- Static check: `rg -n "recovery|semantic artifact|drift|task spine|derived|manual" tests/test_wiki_phase3.py src/core/wiki/semantic_artifacts.py`
- Minimal run: `python -m pytest tests/test_wiki_phase3.py -v`
- Related tests: `python -m pytest tests/test_semantic_artifacts.py tests/test_maintenance.py -v`

**Done criteria:**
- A long session can be inspected and recovered without losing the main task line.
- Derived and manual records remain distinct across repeated turns.

---

## Execution Notes

- Keep each task small and isolated.
- If a task starts to pull in runtime-isolation or general-agent expansion, stop and split it.
- Preserve the already-validated Phase 1 startup path and the Phase 2 patch/converge model.
- Manual annotations are overlays, not source edits.
- Prefer tests first; only add helpers when the tests show a real boundary gap.
