# cc-mini Phase 4 Execution Split Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen runtime isolation between `standard` and `wiki_strict` so the stable general interaction mode stays clean while the coding workflow gets clearly separated runtime assumptions.

**Architecture:** Phase 4 is a consolidation pass over the runtime boundary. It does not add new product surfaces. It makes mode-specific setup visible, keeps shared primitives only where they do not affect user-visible behavior, and adds regression coverage so `standard` cannot silently inherit `wiki_strict` assumptions. The phase should end with the docs explaining the final boundary in plain language.

**Execution Split:** The phase-level boundary reference is [2026-04-21-cc-mini-phase4-runtime-isolation.md](./2026-04-21-cc-mini-phase4-runtime-isolation.md). Use this file for task-level execution and transcription into GSD.

**Tech Stack:** Python 3.11, pytest, argparse, rich

---

## Execution Order

1. Task M4-1: Split mode-specific runtime setup paths
2. Task M4-2: Separate prompt and state assumptions by mode
3. Task M4-3: Add cross-mode isolation regression coverage
4. Task M4-4: Update docs to describe the isolation boundary

---

## Task M4-1: Split Mode-Specific Runtime Setup Paths

**Goal:** Make it obvious in code that `standard` and `wiki_strict` do not share the same behavior surface even if they continue to share some low-level primitives.

**Files:**
- Modify: `src/core/main.py`
- Modify: `src/core/config.py`
- Modify: `src/core/permissions.py`

**Allowed changes:**
- Factor mode-specific setup into clearer branches or helpers.
- Keep `standard` behavior stable.
- Keep the CLI contract unchanged.
- Keep shared primitives only where they do not affect user-visible mode behavior.

**Forbidden changes:**
- Do not break Phase 1 or Phase 2 command behavior.
- Do not introduce a new user-visible mode unless it is part of the phase goal.
- Do not collapse all behavior into one generic runtime.

**Explicit dependencies:** Phase 2 and Phase 3 completion

**Verification:**
- Static check: `rg -n "standard|wiki_strict|resolve_run_mode|PermissionChecker" src/core/main.py src/core/config.py src/core/permissions.py`
- Minimal run: `python -m pytest tests/test_main.py tests/test_config.py -v`
- Related tests: `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

**Done criteria:**
- The code clearly distinguishes mode setup paths.
- `standard` still behaves like the stable general-purpose entrypoint.

**Step 1: Write the failing test**

```python
from core.config import RunMode, resolve_run_mode


def test_mode_setup_separates_standard_and_wiki_strict(monkeypatch):
    monkeypatch.setenv("CC_MINI_MODE", "standard")

    assert resolve_run_mode("standard").value == RunMode.STANDARD.value
    assert resolve_run_mode("wiki_strict").value == RunMode.WIKI_STRICT.value
    assert resolve_run_mode(None, "wiki_strict").value == RunMode.WIKI_STRICT.value
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_main.py tests/test_config.py -v`

Expected: FAIL with an assertion gap around mode-specific setup.

**Step 3: Write minimal implementation**

Add the smallest setup branches/helpers needed to make mode-specific runtime setup visible.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_main.py tests/test_config.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/core/main.py src/core/config.py src/core/permissions.py
git commit -m "feat: split mode-specific runtime setup"
```

---

## Task M4-2: Separate Prompt and State Assumptions by Mode

**Goal:** Ensure the prompt policy and persistent state assumptions for `standard` do not quietly inherit `wiki_strict` assumptions.

**Files:**
- Modify: `src/core/context.py`
- Modify: `src/core/flow_state.py`
- Modify: `tests/test_main.py`

**Allowed changes:**
- Add mode-aware prompt sections or state gates where necessary.
- Keep the user experience unchanged for the stable path.
- Make the assumptions explicit enough to test.
- Avoid introducing a second full runtime stack unless a later phase proves it is needed.

**Forbidden changes:**
- Do not add new lifecycle behavior.
- Do not change the analysis chain into a different product.
- Do not make `standard` depend on wiki metadata.

**Explicit dependencies:** `M4-1`

**Verification:**
- Static check: `rg -n "plan mode|wiki_strict|standard|flow_state|prompt" src/core/context.py src/core/flow_state.py tests/test_main.py`
- Minimal run: `python -m pytest tests/test_main.py -k standard -v`
- Related tests: `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

**Done criteria:**
- The two modes have distinct assumptions that are visible in code and tests.
- `standard` remains a clean general interaction surface.

**Step 1: Write the failing test**

```python
from core.context import build_system_prompt
from core.flow_state import get_flow_state_prompt


def test_standard_does_not_inherit_wiki_strict_assumptions(tmp_path):
    standard_prompt = build_system_prompt(cwd=str(tmp_path))
    wiki_prompt = get_flow_state_prompt()

    assert "WIKI_STRICT Flow-State Mode" not in standard_prompt
    assert "WIKI_STRICT Flow-State Mode" in wiki_prompt
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_main.py -k standard -v`

Expected: FAIL with prompt/state assumption mismatch.

**Step 3: Write minimal implementation**

Add the smallest mode-aware prompt/state split needed for the test.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_main.py -k standard -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/core/context.py src/core/flow_state.py tests/test_main.py
git commit -m "feat: separate prompt and state assumptions by mode"
```

---

## Task M4-3: Add Cross-Mode Isolation Regression Coverage

**Goal:** Prove that changes in `wiki_strict` do not spill into `standard`, and that later-phase surfaces remain out of the stable path.

**Files:**
- Create: `tests/test_mode_isolation.py`

**Allowed changes:**
- Add regression tests for banner text, command availability, and permission isolation.
- Keep the checks small and explicit.
- Focus on the user-observable separation.

**Forbidden changes:**
- Do not add new runtime features.
- Do not test the entire product in one giant suite.
- Do not weaken the stable path to make tests easier.

**Explicit dependencies:** `M4-1`, `M4-2`

**Verification:**
- Static check: `rg -n "analysis-first|later-phase|standard|wiki_strict" tests/test_mode_isolation.py src/core/main.py`
- Minimal run: `python -m pytest tests/test_mode_isolation.py -v`
- Related tests: `python -m pytest tests/test_main.py tests/test_commands.py -v`

**Done criteria:**
- Mode leakage becomes a test failure instead of a user surprise.
- The stable mode stays stable.

**Step 1: Write the failing test**

```python
import sys
from unittest.mock import patch

from core.main import main


def test_mode_leakage_is_detected(tmp_path, capsys):
    with patch.object(sys, "argv", ["cc-mini", "run", "--mode", "standard"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.ensure_memory_dir"), \
         patch("core.main.SessionStore") as mocked_session_store, \
         patch("core.main._bordered_prompt", side_effect=EOFError):
        mocked_session_store.return_value.session_id = "session-1"
        mocked_session_store.return_value.mode = "standard"
        main()

    output = capsys.readouterr().out
    assert "analysis-first" not in output
    assert "wiki_strict will scan only when you explicitly invoke /scan, /prime, or /plan." not in output
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_mode_isolation.py -v`

Expected: FAIL until the isolation assertions exist.

**Step 3: Write minimal implementation**

Add only the regression assertions needed to pin the boundary.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_mode_isolation.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_mode_isolation.py
git commit -m "test: add cross-mode isolation regression coverage"
```

---

## Task M4-4: Update Docs to Describe the Isolation Boundary

**Goal:** Document the mode split clearly so users understand what `standard` is for and what `wiki_strict` is for, including where the runtime remains shared and where it intentionally diverges.

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-04-20-cc-mini-32k-wiki-strict-design.md`

**Allowed changes:**
- Clarify the final user-facing mode story.
- Keep the Phase 1 language intact.
- Describe the isolation boundary in plain language.

**Forbidden changes:**
- Do not re-open the Phase 1 design.
- Do not redefine the product away from coding-first.
- Do not add unapproved new behavior.

**Explicit dependencies:** `M4-3`

**Verification:**
- Static check: `rg -n "standard|wiki_strict|isolation|Phase 4" README.md docs/superpowers/specs/2026-04-20-cc-mini-32k-wiki-strict-design.md`
- Minimal run: `python -m pytest tests/test_mode_isolation.py tests/test_main.py -v`
- Related tests: `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

**Done criteria:**
- The docs explain the runtime boundary without ambiguity.
- The stable mode story remains easy to understand.

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_docs_reference_the_isolation_boundary():
    readme = Path("README.md").read_text(encoding="utf-8")
    spec = Path("docs/superpowers/specs/2026-04-20-cc-mini-32k-wiki-strict-design.md").read_text(encoding="utf-8")

    assert "/reconcile" in readme
    assert "/maintenance" in readme
    assert "standard" in readme and "wiki_strict" in readme
    assert "runtime separation" in spec or "isolation boundary" in spec
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_mode_isolation.py tests/test_main.py -v`

Expected: FAIL until docs/text are aligned.

**Step 3: Write minimal implementation**

Update README and design wording only.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_mode_isolation.py tests/test_main.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add README.md docs/superpowers/specs/2026-04-20-cc-mini-32k-wiki-strict-design.md
git commit -m "docs: describe runtime isolation boundary"
```

---

## Execution Notes

- Keep shared primitives only where they do not blur user-visible mode behavior.
- If a task starts to pull in runtime isolation beyond the mode boundary, split it.
- Preserve the already-validated Phase 1 startup path and the Phase 2/3 workspace workflow.
- Prefer tests first; only add helpers when the tests show a real boundary gap.
