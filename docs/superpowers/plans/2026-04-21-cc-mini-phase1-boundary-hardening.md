# cc-mini Phase 1 Boundary Hardening Follow-up Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining non-blocking gaps after Phase 1 startup is already in place: lock plan-mode write isolation, keep legacy lifecycle surfaces clearly labeled as later-phase, and keep docs/help aligned with the actual phase boundary.

**Architecture:** Treat this as a small stabilization pass over the existing runtime. Keep the startup path, workspace bootstrap, and wiki_strict analysis chain unchanged. Use tests to pin the remaining boundary behavior first, and only add tiny helpers or wording changes if the tests show a real gap.

**Tech Stack:** Python 3.11, pytest, argparse, rich

---

## Direction Check

Phase 1 base behavior already exists and has been validated:

- `init` and `doctor` work
- `run --mode standard|wiki_strict` works
- wiki_strict starts lazily and only does explicit analysis work
- scan / prime / plan structured outputs are already covered

This follow-up plan does **not** reopen the Phase 1 base scope. It only covers the residual hardening items that do not block the overall milestone.

---

## Milestone 1: Plan-Mode Boundary Hardening

### Task M1-T1: Add regression tests for plan-mode write isolation

**Goal:** Prove that plan mode only permits writes to the plan file itself and blocks write / shell actions elsewhere.

**Files:**
- Create: `tests/test_permissions.py`

**Allowed changes:**
- Add a focused regression test for `PermissionChecker` in plan mode.
- Use a tiny fake `Tool` or an existing test double to cover `Edit`, `Write`, and `Bash`.
- Assert that plan file writes are allowed and non-plan writes are denied.

**Forbidden changes:**
- Do not change the runtime permission logic yet.
- Do not touch `src/core/main.py`.
- Do not add patch, post_edit, or maintenance features.

**Explicit dependencies:** none

**Verification:**
- Static check: `rg -n "_PLAN_MODE_ALLOWED_TOOLS|_PLAN_MODE_WRITE_TOOLS|plan mode" src/core/permissions.py tests/test_permissions.py`
- Minimal run: `python -m pytest tests/test_permissions.py -v`
- Related tests: `python -m pytest tests/test_main.py tests/test_config.py -v`

**Done criteria:**
- A non-plan-path `Edit` or `Write` attempt is denied in plan mode.
- A write to the active plan file remains allowed.
- The regression test makes the plan-mode boundary obvious to future maintainers.

**Step sketch:**

```python
def test_plan_mode_allows_only_the_plan_file(monkeypatch, tmp_path):
    from core.permissions import PermissionChecker
    from core.plan import PlanModeManager
    from types import SimpleNamespace

    # Bind a plan manager with a known plan file path, then probe write tools.
    plan_path = tmp_path / "plans" / "calm-forest.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("# draft\n", encoding="utf-8")

    manager = PlanModeManager()
    manager._plan_file = plan_path
    manager._active = True

    checker = PermissionChecker(auto_approve=False)
    checker.set_plan_manager(manager)
    write_tool = SimpleNamespace(name="Write")
    bash_tool = SimpleNamespace(name="Bash")

    assert checker.check(write_tool, {"file_path": str(tmp_path / "other.md")}) == "deny"
    assert checker.check(write_tool, {"file_path": plan_path}) == "allow"
    assert checker.check(bash_tool, {"command": "touch other.md"}) == "deny"
```

### Task M1-T2: Centralize the plan-file write decision if the test exposes duplication

**Goal:** Keep the plan-mode file-path check in one small, testable place so the permission rules do not drift.

**Files:**
- Modify: `src/core/permissions.py`
- Modify: `tests/test_permissions.py`

**Allowed changes:**
- Add a tiny helper for the plan-file path comparison if needed.
- Reuse that helper from `PermissionChecker.check`.
- Keep the rest of the permission flow untouched.

**Forbidden changes:**
- Do not change the non-plan-mode permission flow.
- Do not broaden plan mode to allow extra tools.
- Do not modify the CLI startup path.

**Explicit dependencies:** `M1-T1`

**Verification:**
- Static check: `rg -n "plan_path|file_path|PermissionChecker" src/core/permissions.py tests/test_permissions.py`
- Minimal run: `python -m pytest tests/test_permissions.py -v`
- Related tests: `python -m pytest tests/test_main.py -k plan -v`

**Done criteria:**
- Plan-mode write gating is centralized enough to test directly.
- The helper or refactor does not change the observed permission outcome.

**Step sketch:**

```python
def test_plan_write_allowed_helper_matches_plan_path():
    assert _plan_write_allowed("/tmp/.claude/plans/calm-forest.md", "/tmp/.claude/plans/calm-forest.md")
    assert not _plan_write_allowed("/tmp/.claude/plans/calm-forest.md", "/tmp/.claude/plans/other.md")
```

---

## Milestone 2: Later-Phase Surface Alignment

### Task M2-T3: Make legacy lifecycle commands self-identify as later-phase

**Goal:** Make `init_build` and `post_edit` unmistakably read as later-phase or legacy surfaces, so they do not compete with the Phase 1 minimal product story.

**Files:**
- Modify: `src/core/commands.py`
- Modify: `tests/test_main.py`

**Allowed changes:**
- Tighten the command descriptions and direct output wording.
- Keep the underlying legacy behavior intact unless a tiny message change is enough.
- Make it obvious that these surfaces are not part of Phase 1 startup.

**Forbidden changes:**
- Do not add any new lifecycle implementation.
- Do not move patch/post_edit/maintenance into Phase 1.
- Do not change wiki_strict analysis behavior.

**Explicit dependencies:** none

**Verification:**
- Static check: `rg -n "init_build|post_edit|later-phase|legacy full wiki bootstrap" src/core/commands.py tests/test_main.py`
- Minimal run: `python -m pytest tests/test_main.py -k "help or post_edit or init_build" -v`
- Related tests: `python -m pytest tests/test_main.py tests/test_wiki_phase1.py -v`

**Done criteria:**
- The help text and direct command output both say these are later-phase surfaces.
- A reader cannot confuse them with the Phase 1 minimal startup path.

**Step sketch:**

```python
def test_init_build_announces_later_phase(tmp_path, monkeypatch):
    from core.commands import CommandContext, handle_command
    from core.config import AppConfig
    from core.engine import Engine
    from core.permissions import PermissionChecker
    from core.session import SessionStore
    from rich.console import Console
    from io import StringIO
    from unittest.mock import MagicMock

    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(spec=Engine),
        session_store=MagicMock(spec=SessionStore),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(spec=AppConfig),
        permissions=MagicMock(spec=PermissionChecker),
    )

    handle_command("init_build", "", ctx)

    output = console.file.getvalue()
    assert "later-phase" in output.lower()
```

### Task M2-T4: Add help/docs consistency coverage for the phase boundary

**Goal:** Keep README and slash-command help aligned so Phase 1 language stays stable as the code evolves.

**Files:**
- Modify: `README.md`
- Modify: `tests/test_main.py` or create `tests/test_commands.py`

**Allowed changes:**
- Add a small test that checks the command help output for the phase boundary labels.
- Update README wording only when the test reveals drift.
- Keep the wording consistent with the approved design doc.

**Forbidden changes:**
- Do not change runtime behavior.
- Do not expand the documented scope beyond Phase 1.
- Do not introduce new commands while editing docs.

**Explicit dependencies:** `M2-T3`

**Verification:**
- Static check: `rg -n "Phase 1|analysis-first|later-phase|patch|post-edit|maintenance" README.md src/core/commands.py tests/test_main.py`
- Minimal run: `python -m pytest tests/test_main.py -k help -v`
- Related tests: `python -m pytest tests/test_main.py tests/test_permissions.py -v`

**Done criteria:**
- README and command help tell the same Phase 1 story.
- Later-phase lifecycle surfaces remain clearly deferred.

**Step sketch:**

```python
def test_help_mentions_later_phase_surfaces():
    from core.commands import CommandContext, handle_command
    from core.config import AppConfig
    from core.engine import Engine
    from core.permissions import PermissionChecker
    from core.session import SessionStore
    from rich.console import Console
    from io import StringIO
    from unittest.mock import MagicMock

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(spec=Engine),
        session_store=MagicMock(spec=SessionStore),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(spec=AppConfig),
        permissions=MagicMock(spec=PermissionChecker),
    )

    handle_command("help", "", ctx)
    output = console.file.getvalue()
    assert "Legacy full wiki bootstrap (later phase)" in output
    assert "Later-phase post-edit guard" in output
```

---

## Execution Notes

- Keep each task small and isolated.
- If a task starts to pull in patch / maintenance work, stop and split it.
- Preserve the already-validated Phase 1 startup path.
- Prefer tests first; only add helpers when the tests show a real boundary gap.
