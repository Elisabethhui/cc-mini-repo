# cc-mini Phase 6 Delivery Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn a completed coding task into a manually confirmed, reviewable, commit-ready, and audit-friendly closeout unit, then expose a read-only milestone review surface that can consume that closeout record.

**Architecture:** Reuse the existing coding workflow and add a thin closure layer above it. The closure layer writes a compact closeout record in both JSON and Markdown, asks for explicit commit confirmation instead of auto-committing, and exposes a read-only milestone review command that reads the record without mutating source files or git state. Phase 6 is the delivery/closure bridge between implementation work and milestone review; it must not become a new router, planner, or background automation system.

**Tech Stack:** Python 3.11, pytest, argparse, rich, existing slash-command system, existing bundled `/test` `/review` `/commit` skills

---

## File Structure Lock

Before defining tasks, the phase should touch only a small set of focused files:

- `src/core/wiki/closeout.py` owns closeout record data, persistence, and Markdown/JSON rendering.
- `src/core/commands.py` owns the `/close` and `/milestone-review` command surfaces.
- `README.md` documents the closure loop and the read-only audit surface.
- `docs/superpowers/plans/2026-04-21-cc-mini-roadmap.md` gets the Phase 6 roadmap entry so the long-term phase map matches the new closure loop.
- `tests/test_closeout.py` covers the closeout record store and rendering.
- `tests/test_wiki_phase6.py` covers confirmation gating, failure-stop behavior, and read-only milestone review behavior.
- `tests/test_commands.py` covers the command table and help-text surface.

Keep the phase narrow: closeout data, closeout commands, and read-only milestone review only.

---

## Milestone 1: Closeout Record Layer

### Task M6-T1: Add a closeout record model and persistence layer

**Task ID:** M6-T1

**Task Name:** Closeout record model and persistence layer

**Goal:** Create one durable closeout record object that can save and load the evidence needed for later milestone review in both JSON and Markdown form.

**Files:**
- Create: `src/core/wiki/closeout.py`
- Create: `tests/test_closeout.py`

**Allowed changes:**
- Define a `CloseoutRecord` dataclass with fields for task id, phase name, verification status, review status, commit status, commit hash, ready-for-audit flag, residual risks, and timestamps.
- Define a `CloseoutStore` that writes to `.cc-mini/wiki/reports/closeout/`.
- Provide save/load helpers for the latest closeout record.
- Render the same record into both machine-readable JSON and human-readable Markdown.

**Forbidden changes:**
- Do not wire the CLI into closure yet.
- Do not auto-commit or auto-archive anything.
- Do not mutate source files or git state as part of the record store.

**Explicit dependencies:** Phase 2 convergence records, Phase 3 derived/manual artifact conventions

**Verification:**
- Static check: `rg -n "CloseoutRecord|CloseoutStore|closeout" src/core/wiki/closeout.py tests/test_closeout.py`
- Minimal run: `./.venv/bin/python -m pytest tests/test_closeout.py -v`
- Related tests: `./.venv/bin/python -m pytest tests/test_semantic_artifacts.py tests/test_wiki_phase3.py -v`

**Done criteria:**
- A closeout record can round-trip through disk without losing fields.
- The store writes both JSON and Markdown outputs for the same closeout.
- The record is clearly separate from source-code editing behavior.

**Step sketch:**

```python
def test_closeout_record_round_trip(tmp_path):
    from core.wiki.closeout import CloseoutRecord, CloseoutStore

    store = CloseoutStore(tmp_path)
    record = CloseoutRecord(
        task_id="task-1",
        phase_name="Phase 6",
        verification_status="passed",
        review_status="approved",
        commit_status="pending",
        commit_hash=None,
        ready_for_audit=False,
        residual_risks=["commit confirmation still pending"],
    )

    path = store.save(record)
    restored = store.load(path.stem)

    assert restored.task_id == "task-1"
    assert restored.verification_status == "passed"
    assert "commit confirmation" in store.render_markdown(restored)
```

---

## Milestone 2: Closure Commands

### Task M6-T2: Add a `/close` command that requires explicit commit confirmation

**Task ID:** M6-T2

**Task Name:** `/close` command with explicit commit confirmation

**Goal:** Make `/close` the user-facing orchestration point that collects verification and review results, writes a draft closeout record, and stops before any git mutation until the user explicitly confirms with a follow-up command.

**Files:**
- Modify: `src/core/commands.py`
- Modify: `tests/test_wiki_phase6.py`

**Allowed changes:**
- Add `/close` handling with a confirmation path such as `/close confirm` and `/close cancel`.
- Reuse the existing `/test`, `/review`, and `/commit` skills rather than inventing a new planner or commit engine.
- Write a draft closeout record before confirmation and finalize it only after explicit confirmation.
- Stop the flow if verification fails or if the review result is risky and the user does not continue.

**Forbidden changes:**
- Do not auto-commit.
- Do not auto-archive.
- Do not hide confirmation behind a background job or silent side effect.
- Do not mutate source files during the closeout draft step.

**Explicit dependencies:** `M6-T1`

**Verification:**
- Static check: `rg -n "/close|closeout|confirm|cancel|/test|/review|/commit" src/core/commands.py tests/test_wiki_phase6.py`
- Minimal run: `./.venv/bin/python -m pytest tests/test_wiki_phase6.py -v`
- Related tests: `./.venv/bin/python -m pytest tests/test_commands.py tests/test_skills.py -v`

**Done criteria:**
- `/close` creates a draft closeout record and clearly asks for confirmation.
- `/close confirm` finalizes the record and reaches the existing commit path only after the user confirms.
- `/close cancel` exits cleanly without git mutation.
- Failed verification stops the closure flow before commit.

**Step sketch:**

```python
def test_close_requires_confirm_before_commit():
    from io import StringIO
    from unittest.mock import MagicMock
    from rich.console import Console
    from core.commands import CommandContext, handle_command

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=None,
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("close", "", ctx)
    output = console.file.getvalue()

    assert "Confirm with /close confirm" in output
    assert "ready for audit" not in output.lower()
    assert ctx.pending_query is not None

    handle_command("close", "confirm", ctx)
    output = console.file.getvalue()

    assert "closeout finalized" in output.lower()
    assert "commit" in output.lower()
```

### Task M6-T3: Add a read-only `/milestone-review` command

**Task ID:** M6-T3

**Task Name:** Read-only milestone review command

**Goal:** Expose a `/milestone-review` command that reads the closeout record, reports readiness and residual risk, and never mutates source files or git state.

**Files:**
- Modify: `src/core/commands.py`
- Modify: `src/core/wiki/closeout.py`
- Modify: `tests/test_wiki_phase6.py`

**Allowed changes:**
- Add a milestone-review command surface that loads the latest closeout record.
- Summarize ready/not-ready status, verification status, review status, commit hash when present, and residual risks.
- If no closeout record exists, say so plainly and point the user back to `/close`.
- Keep the command read-only.

**Forbidden changes:**
- Do not start verification or commit actions from `/milestone-review`.
- Do not modify source files or git state.
- Do not invent a new background audit process.

**Explicit dependencies:** `M6-T1`, `M6-T2`

**Verification:**
- Static check: `rg -n "milestone-review|closeout|ready for audit|read-only" src/core/commands.py src/core/wiki/closeout.py tests/test_wiki_phase6.py`
- Minimal run: `./.venv/bin/python -m pytest tests/test_wiki_phase6.py -v`
- Related tests: `./.venv/bin/python -m pytest tests/test_commands.py tests/test_semantic_artifacts.py -v`

**Done criteria:**
- `/milestone-review` reads only from closeout storage.
- The output clearly distinguishes ready-for-audit from not-ready states.
- Missing records are handled as a user-facing read-only result, not as an error that mutates state.

**Step sketch:**

```python
def test_milestone_review_is_read_only():
    from io import StringIO
    from unittest.mock import MagicMock
    from rich.console import Console
    from core.commands import CommandContext, handle_command

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=None,
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("milestone-review", "", ctx)
    output = console.file.getvalue()

    assert "No closeout record found" in output
    assert ctx.pending_query is None
```

---

## Milestone 3: User-Facing Surface and Guardrails

### Task M6-T4: Update roadmap, README, and command help to include Phase 6

**Task ID:** M6-T4

**Task Name:** Roadmap and docs alignment for delivery closure

**Goal:** Make the new closure loop visible in the long-term roadmap, the README, and the command help output so users can discover `/close` and `/milestone-review` without guessing.

**Files:**
- Modify: `docs/superpowers/plans/2026-04-21-cc-mini-roadmap.md`
- Modify: `README.md`
- Modify: `tests/test_commands.py`

**Allowed changes:**
- Add a Phase 6 entry to the roadmap.
- Document the `/close` and `/milestone-review` surfaces in the README.
- Update the help-table regression test so the new commands are visible to users.
- Keep the wording explicit that commit is manual and milestone review is read-only.

**Forbidden changes:**
- Do not rewrite the earlier phase descriptions.
- Do not expand the roadmap into a new router or planner.
- Do not blur implementation commits and closure commits.

**Explicit dependencies:** `M6-T1`, `M6-T2`, `M6-T3`

**Verification:**
- Static check: `rg -n "Phase 6|/close|/milestone-review|closeout|read-only" README.md docs/superpowers/plans/2026-04-21-cc-mini-roadmap.md tests/test_commands.py`
- Minimal run: `./.venv/bin/python -m pytest tests/test_commands.py -v`
- Related tests: `./.venv/bin/python -m pytest tests/test_wiki_phase6.py tests/test_closeout.py -v`

**Done criteria:**
- The roadmap reflects Phase 6 as the delivery-closure bridge.
- The README explains the closure flow without implying auto-commit or auto-archive.
- The help surface shows the new commands and preserves the read-only/manual-confirmation boundary.

**Step sketch:**

```python
def test_help_lists_delivery_closure_commands():
    from io import StringIO
    from unittest.mock import MagicMock
    from rich.console import Console
    from core.commands import CommandContext, handle_command

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=None,
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("help", "", ctx)
    output = console.file.getvalue()

    assert "/close" in output
    assert "/milestone-review" in output
    assert "manual confirmation" in output.lower()
    assert "read-only" in output.lower()
```

---

## Execution Notes

- Keep the closeout layer thin and explicit; it should record and present evidence, not invent new workflow behavior.
- If `/close` starts pulling in new general-agent routing, split it back down immediately.
- Preserve the separation between implementation commits from Phase 2 and closure commits in Phase 6.
- The most important test is the user-confirmation path: verify, review, confirm, commit, summarize, then review read-only.

## Self-Review

**1. Spec coverage:** The plan covers the design spec’s required pieces:
- manual commit confirmation in `/close`
- JSON + Markdown closeout artifacts
- read-only `/milestone-review`
- failure-stop behavior when verification or review fails
- milestone-level audit consumption of the closeout record

**2. Placeholder scan:** No `TBD`, `TODO`, or vague filler steps are used. Every task lists explicit files, dependencies, verification commands, and done criteria.

**3. Type consistency:** The plan uses the same names throughout:
- `CloseoutRecord`
- `CloseoutStore`
- `/close`
- `/milestone-review`
- `ready_for_audit`
- `commit_status`

No later task introduces a conflicting name for the same concept.
