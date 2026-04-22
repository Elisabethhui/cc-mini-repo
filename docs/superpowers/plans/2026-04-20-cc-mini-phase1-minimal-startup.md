# cc-mini Phase 1 Minimal Startup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the Phase 1 minimal startup path for cc-mini: initialize a workspace, verify readiness, run standard/wiki_strict in an analysis-first shape, and produce structured wiki_strict outputs without pulling patch/post_edit/maintenance into the Phase 1 hard gate.

**Architecture:** Split the work into three layers: a small bootstrap helper for workspace init/doctor, an explicit CLI routing layer for `init` / `doctor` / `run`, and a lazy wiki_strict startup path that only enables the minimal analysis chain on demand. Keep `standard` behavior stable, keep wiki_strict logic separated at the behavior level first, and defer the later lifecycle surfaces to future phases.

**Tech Stack:** Python 3.11, argparse, prompt_toolkit, rich, pytest

---

## Direction Check

No blocking issue in the approved direction. The main implementation gap is that `init`, `doctor`, and `run --mode ...` are not yet first-class entrypoints, and wiki_strict startup still performs too much work too early. This plan fixes that by making Phase 1 analysis-first and deferring patch/post_edit/maintenance.

---

## Milestone 1: Workspace Bootstrap Surface

### Task M1-T1: Add a phase1 workspace bootstrap helper

**Goal:** Create one source of truth for phase1 workspace scaffolding and readiness checks so `init` and `doctor` can share the same rules.

**Files:**
- Create: `src/core/bootstrap.py`
- Create: `tests/test_bootstrap.py`

**Allowed changes:**
- Add a small bootstrap result type and workspace helper functions.
- Create the minimal `.cc-mini/` / `.cc-mini/wiki/` scaffold needed by phase1.
- Expose a readiness summary that tells the CLI whether the workspace is initialized, missing, or stale.
- Keep the helper idempotent so repeated init calls do not corrupt state.

**Forbidden changes:**
- Do not touch `src/core/main.py` yet.
- Do not change wiki scan/prime/plan behavior yet.
- Do not add patch, post_edit, maintenance, or watcher behavior.
- Do not change README or command help text yet.

**Explicit dependencies:** none

**Verification:**
- Static check: `rg -n "bootstrap_workspace|doctor_workspace|BootstrapResult" src/core/bootstrap.py tests/test_bootstrap.py`
- Minimal run: `python -c "from pathlib import Path; from core.bootstrap import bootstrap_workspace; r = bootstrap_workspace(Path('.')); print(r.ready)"`
- Related tests: `pytest tests/test_bootstrap.py -v`

**Done criteria:**
- A temp repo can be initialized through the helper.
- The helper returns a deterministic readiness result.
- Re-running the helper is safe and does not duplicate the scaffold.

### Task M1-T2: Add `cc-mini init`

**Goal:** Make workspace initialization a first-class CLI action that uses the new bootstrap helper and prints a clear next-step hint.

**Files:**
- Modify: `src/core/main.py`
- Modify: `tests/test_main.py`

**Allowed changes:**
- Add an `init` entrypoint or subcommand.
- Call the bootstrap helper from Task M1-T1.
- Print the created scaffold, whether the workspace was newly initialized or already present, and the next suggested command.
- Preserve the current non-init REPL path.

**Forbidden changes:**
- Do not add `doctor` yet.
- Do not change wiki_strict startup semantics yet.
- Do not add patch/post_edit/maintenance behavior.
- Do not remove the current legacy interactive path.

**Explicit dependencies:** `M1-T1`

**Verification:**
- Static check: `rg -n "\\binit\\b|bootstrap_workspace" src/core/main.py tests/test_main.py`
- Minimal run: `python -c "from core.main import main; import sys; sys.argv = ['cc-mini', 'init']; main()"`
- Related tests: `pytest tests/test_main.py -k init -v`

**Done criteria:**
- `cc-mini init` creates or validates the workspace scaffold.
- The command is idempotent.
- The output tells the user what happened and what to do next.

### Task M1-T3: Add `cc-mini doctor`

**Goal:** Give users a fast readiness check that explains whether the current workspace can run the phase1 minimal startup flow.

**Files:**
- Modify: `src/core/main.py`
- Modify: `tests/test_main.py`

**Allowed changes:**
- Add a `doctor` entrypoint or subcommand.
- Reuse the bootstrap helper from Task M1-T1.
- Report config, workspace, and phase1 readiness in a short actionable summary.
- Keep the output focused on missing prerequisites and recovery hints.

**Forbidden changes:**
- Do not add any scanning or task planning behavior.
- Do not change runtime mode selection yet.
- Do not introduce maintenance, patch, or post_edit behavior.
- Do not alter the README yet.

**Explicit dependencies:** `M1-T1`

**Verification:**
- Static check: `rg -n "\\bdoctor\\b|bootstrap_workspace" src/core/main.py tests/test_main.py`
- Minimal run: `python -c "from core.main import main; import sys; sys.argv = ['cc-mini', 'doctor']; main()"`
- Related tests: `pytest tests/test_main.py -k doctor -v`

**Done criteria:**
- `cc-mini doctor` gives a useful readiness summary on a fresh workspace and an initialized workspace.
- The command never mutates the workspace.

---

## Milestone 2: Explicit Runtime Entry and Lazy wiki_strict Startup

### Task M2-T4: Add `cc-mini run` and make mode selection explicit

**Goal:** Make `run --mode standard|wiki_strict` the explicit runtime entrypoint and ensure CLI mode selection wins over the current implicit behavior.

**Files:**
- Modify: `src/core/config.py`
- Modify: `src/core/main.py`
- Modify: `tests/test_config.py`

**Allowed changes:**
- Add a small mode-resolution helper that accepts CLI intent plus env fallback.
- Route `cc-mini run --mode ...` to the correct runtime.
- Preserve the existing legacy `cc-mini` no-subcommand path for compatibility.
- Keep `standard` as the default if nothing else is specified.

**Forbidden changes:**
- Do not change wiki_strict startup side effects yet.
- Do not add patch/post_edit/maintenance behavior.
- Do not replace the existing engine implementation.
- Do not change README wording yet.

**Explicit dependencies:** `M1-T1`, `M1-T2`, `M1-T3`

**Verification:**
- Static check: `rg -n "resolve_run_mode|RunMode|subcommand|\\brun\\b" src/core/config.py src/core/main.py tests/test_config.py`
- Minimal run: `python -c "from core.main import main; import sys; sys.argv = ['cc-mini', 'run', '--mode', 'standard']; main()"`
- Related tests: `pytest tests/test_config.py -k mode -v`

**Done criteria:**
- `cc-mini run --mode standard` and `cc-mini run --mode wiki_strict` dispatch to different mode paths.
- CLI mode choice is no longer silently ignored.

### Task M2-T5: Make wiki_strict startup lazy and analysis-only

**Goal:** Remove the startup overwork from wiki_strict so the mode starts fast and waits for explicit scan/prime/plan commands.

**Files:**
- Modify: `src/core/main.py`
- Modify: `tests/test_main.py`

**Allowed changes:**
- Remove automatic full workspace ingest on wiki_strict startup.
- Remove automatic watcher startup from the phase1 startup path.
- Keep wiki_strict tool registration and command availability intact.
- Keep `scan` / `prime` / `plan` working as explicit user actions.

**Forbidden changes:**
- Do not add a separate engine instance in phase1.
- Do not add patch, post_edit, or maintenance startup hooks.
- Do not make wiki_strict mutate the workspace before the user asks for analysis.
- Do not broaden the mode into a full lifecycle product yet.

**Explicit dependencies:** `M2-T4`

**Verification:**
- Static check: `rg -n "start_wiki_watcher|ingest_all\\(|wiki_strict" src/core/main.py tests/test_main.py`
- Minimal run: `python -c "from core.main import main; import sys; sys.argv = ['cc-mini', 'run', '--mode', 'wiki_strict']; main()"`
- Related tests: `pytest tests/test_main.py -k wiki_strict -v`

**Done criteria:**
- wiki_strict boot is lightweight.
- The mode no longer auto-scans or watches the whole workspace on startup.
- Analysis work happens only when the user invokes the explicit commands.

### Task M2-T6: Add a phase1 wiki analysis-chain smoke test

**Goal:** Prove that a fresh repo can go through the phase1 minimal analysis chain and produce structured outputs for scan, TaskPack, and planning.

**Files:**
- Create: `tests/test_wiki_phase1.py`
- Modify: `src/core/commands.py` only if a small testability helper is required

**Allowed changes:**
- Add a temp-repo smoke test that exercises `scan -> prime -> plan`.
- Assert the structured outputs that Phase 1 promises: Goal Stack, TaskPack, and EditSpec.
- Add only tiny testability helpers if direct command invocation is currently awkward.

**Forbidden changes:**
- Do not implement patch, post_edit, or maintenance.
- Do not add unrelated wiki refactors.
- Do not turn this into a broad end-to-end suite.

**Explicit dependencies:** `M1-T1`, `M2-T5`

**Verification:**
- Static check: `rg -n "Goal Stack|TaskPack|EditSpec|scan|prime|plan" tests/test_wiki_phase1.py src/core/commands.py`
- Minimal run: `python -m pytest tests/test_wiki_phase1.py -v`
- Related tests: the existing CLI and config tests should still pass

**Done criteria:**
- The phase1 analysis chain is reproducible in a clean temp repo.
- The test proves the product can produce structured outputs without requiring later-phase lifecycle features.

---

## Milestone 3: User-Facing Alignment

### Task M3-T7: Sync README and command help to phase1 wording

**Goal:** Make the public docs and slash-command help say exactly what phase1 supports, and clearly defer the later lifecycle surfaces.

**Files:**
- Modify: `README.md`
- Modify: `src/core/commands.py`

**Allowed changes:**
- Update quick start text to reflect the minimal startup path.
- Update phase1 language so `patch`, `post_edit`, and `maintenance` are clearly later-phase surfaces.
- Update slash-command descriptions to match the analysis-first phase1 scope.
- Keep the wording consistent with the approved design doc and the plan above.

**Forbidden changes:**
- Do not change runtime behavior.
- Do not introduce new features by accident while editing docs.
- Do not re-expand phase1 into a full lifecycle promise.

**Explicit dependencies:** `M2-T4`, `M2-T5`, `M2-T6`

**Verification:**
- Static check: `rg -n "init|doctor|run --mode|patch|post-edit|maintenance|wiki_strict" README.md src/core/commands.py`
- Minimal run: `python -c "from pathlib import Path; text = Path('README.md').read_text(); assert 'Phase 1' in text and 'patch, post-edit, and maintenance' in text"`
- Related tests: `pytest tests/test_wiki_phase1.py -v && pytest tests/test_main.py -v`

**Done criteria:**
- README and command help describe the same phase1 story.
- Later-stage lifecycle features are visible as deferred, not as first-phase commitments.

---

## Execution Notes

- Keep each task atomic and commit after each successful task.
- If a task starts to drag in patch/post_edit/maintenance, stop and split it.
- Prefer preserving the current runtime behavior outside the explicit phase1 scope.
- Reuse the bootstrap helper rather than duplicating workspace checks in multiple places.

