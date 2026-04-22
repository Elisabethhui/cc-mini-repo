# cc-mini Phase 2 Coding Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the analysis-first `wiki_strict` path into a real coding workflow: explicit patching, rollback-aware multi-file edits, and confirmation-gated convergence records after human approval.

**Architecture:** Reuse the Phase 1 analysis chain and extend it into a constrained modify-and-converge loop. Keep `standard` stable. Treat `wiki_strict` as the coding-first product path and make every write or impact step explicit, traceable, reversible, and testable. Phase 2 is the transaction layer: it owns patch manifests, rollback snapshots, cross-file impact analysis, human confirmation, and the convergence record emitted after the patch is accepted. It does not own the long-lived semantic artifact store, and it never rewrites source files during convergence.

**Tech Stack:** Python 3.11, pytest, argparse, rich

---

## Direction Check

Phase 1 already gives the project a usable startup surface and a structured analysis chain. Phase 2 starts where Phase 1 stops: it is the first phase where code changes become a first-class product surface.

The main Phase 2 question is not "can the model edit files?" but "can the workflow prove what changed, what it affected, and how to undo it if the user rejects the result?"

## Boundary With Phase 3

- Phase 2 emits a patch transaction summary plus a convergence record.
- Phase 3 persists workspace semantic artifacts derived from those records.
- Phase 2 never becomes the durable semantic store.
- Phase 3 never performs code writes itself.

---

## Milestone 1: Explicit Patch and Rollback Boundary

### Task M2-T1: Add a patch session manifest and rollback snapshot helper

**Goal:** Create one explicit object that records a patch session, the files it touched, and the rollback snapshot needed to restore the workspace if the patch is rejected or fails.

**Files:**
- Create: `src/core/wiki/patch_session.py`
- Create: `tests/test_patch_session.py`

**Allowed changes:**
- Define patch session data structures for selected EditSpecs, original file hashes, patch timestamps, and rollback references.
- Add save/load helpers for patch sessions.
- Keep the helper focused on patch bookkeeping only.

**Forbidden changes:**
- Do not wire the CLI into patch execution yet.
- Do not add maintenance or watcher behavior.
- Do not mutate source files automatically as part of the helper itself.

**Explicit dependencies:** Phase 1 startup and Phase 1 `TaskPack`/`EditSpec` generation

**Verification:**
- Static check: `rg -n "PatchSession|RollbackSnapshot|patch session" src/core/wiki/patch_session.py tests/test_patch_session.py`
- Minimal run: `python -m pytest tests/test_patch_session.py -v`
- Related tests: `python -m pytest tests/test_main.py tests/test_commands.py -v`

**Done criteria:**
- A patch session can be saved and loaded deterministically.
- The session records enough information to describe a rollback.

**Step sketch:**

```python
def test_patch_session_round_trip(tmp_path):
    session = PatchSession(
        task_id="task-1",
        target_files=["src/app.py"],
        original_hashes={"src/app.py": "deadbeef"},
    )

    path = save_patch_session(tmp_path, session)
    restored = load_patch_session(path)

    assert restored.task_id == "task-1"
    assert restored.original_hashes["src/app.py"] == "deadbeef"
```

### Task M2-T2: Add an explicit `/patch` command for bounded multi-file edits

**Goal:** Make patching a user-triggered command that applies only the selected EditSpecs, writes a rollback snapshot first, and fails closed if the edit set is not safe.

**Files:**
- Modify: `src/core/commands.py`
- Modify: `src/core/wiki/patch_session.py`
- Create: `tests/test_wiki_phase2.py`

**Allowed changes:**
- Add a patch command that loads a primed TaskPack and applies selected EditSpecs explicitly.
- Support multi-file edits as long as each target is covered by the patch session and rollback snapshot.
- Enforce cross-file impact analysis before any write happens.

**Forbidden changes:**
- Do not make patch automatic on plan exit.
- Do not permit writes outside the declared patch session.
- Do not add maintenance cleanup or watcher behavior here.

**Explicit dependencies:** `M2-T1`

**Verification:**
- Static check: `rg -n "patch|PatchSession|rollback|EditSpec" src/core/commands.py src/core/wiki/patch_session.py tests/test_wiki_phase2.py`
- Minimal run: `python -m pytest tests/test_wiki_phase2.py -v`
- Related tests: `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

**Done criteria:**
- The user can invoke patch explicitly.
- Cross-file edits are bounded and rollback is recorded before the write.
- A failed patch leaves a usable rollback record.

**Step sketch:**

```python
def test_patch_command_requires_explicit_taskpack(tmp_path):
    from core.wiki.taskpack import TaskPack, EditSpec, TaskStatus

    taskpack = TaskPack(
        task_id="task-1",
        title="Patch demo",
        status=TaskStatus.PRIMED,
        target_files=["src/app.py", "src/util.py"],
        primary_symbols=["main", "helper"],
        edit_specs=[
            EditSpec(target_file="src/app.py", operation="update", description="Update app", old_string="old", new_string="new"),
            EditSpec(target_file="src/util.py", operation="update", description="Update util", old_string="old", new_string="new"),
        ],
    )

    assert taskpack.is_ready_for_patch()[0]
    assert len(taskpack.edit_specs) == 2
```

---

## Milestone 2: Confirmation-Based Convergence

### Task M2-T3: Turn post_edit finalization into a confirmation-based convergence record step

**Goal:** Make `post_edit` the explicit place where the user can confirm the patch outcome and produce a high-level convergence record, without rewriting source files again.

**Files:**
- Modify: `src/core/wiki/post_edit_guard.py`
- Create: `src/core/wiki/convergence_record.py`
- Modify: `tests/test_wiki_phase2.py`

**Allowed changes:**
- Use post-edit analysis to produce a convergence record describing the effect of the patch.
- On explicit finalization, store a patch transaction summary that can be consumed by later phases.
- Keep rollback metadata available if convergence fails.

**Forbidden changes:**
- Do not add automatic startup hooks.
- Do not add maintenance or archive behavior here.
- Do not perform a second source-code rewrite during convergence.
- Do not build the persistent workspace semantic artifact store yet.

**Explicit dependencies:** `M2-T2`

**Verification:**
- Static check: `rg -n "CompletionState|convergence_record|post_edit|rollback" src/core/wiki/post_edit_guard.py src/core/wiki/convergence_record.py tests/test_wiki_phase2.py`
- Minimal run: `python -m pytest tests/test_wiki_phase2.py -v`
- Related tests: `python -m pytest tests/test_commands.py tests/test_main.py -v`

**Done criteria:**
- `post_edit` can report, confirm, and emit a convergence record.
- The convergence record is enough for later phases to build persistent semantic artifacts.
- If the convergence step fails, rollback metadata is still available.

**Step sketch:**

```python
def test_post_edit_finalize_updates_semantic_artifacts(tmp_path):
    from core.wiki.post_edit_guard import ImpactSummary, CompletionState
    from core.wiki.convergence_record import ConvergenceRecordStore

    summary = ImpactSummary(task_id="task-1", completion_state=CompletionState.IMPACT_CLEAN)
    store = ConvergenceRecordStore(tmp_path)
    result = store.converge(summary, confirmed=True)

    assert result["confirmed"] is True
    assert result["record_written"] is True
    assert result["source_files_touched"] == 0
```

### Task M2-T4: Add coding-loop smoke coverage and docs alignment

**Goal:** Prove the full Phase 2 loop is understandable and reproducible: patch, confirm, record convergence, and rollback if needed.

**Files:**
- Modify: `README.md`
- Modify: `src/core/commands.py`
- Modify: `tests/test_wiki_phase2.py`

**Allowed changes:**
- Add a temp-repo smoke test that exercises patch -> post_edit -> confirm -> rollback.
- Update README and help text to describe the explicit coding loop.
- Keep Phase 1 wording intact while adding Phase 2 language.

**Forbidden changes:**
- Do not expand into maintenance or continuity surfaces.
- Do not reframe `standard`.
- Do not hide rollback from the user-facing story.

**Explicit dependencies:** `M2-T2`, `M2-T3`

**Verification:**
- Static check: `rg -n "patch|post_edit|rollback|converge|semantic" README.md src/core/commands.py tests/test_wiki_phase2.py`
- Minimal run: `python -m pytest tests/test_wiki_phase2.py -v`
- Related tests: `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

**Done criteria:**
- The full coding loop is visible in docs and tests.
- A user can understand how to enter, confirm, record convergence, and undo the workflow.

---

## Execution Notes

- Keep each task small and isolated.
- If a task starts to pull in maintenance or runtime-isolation work, stop and split it.
- Preserve the already-validated Phase 1 startup path.
- Prefer tests first; only add helpers when the tests show a real boundary gap.
