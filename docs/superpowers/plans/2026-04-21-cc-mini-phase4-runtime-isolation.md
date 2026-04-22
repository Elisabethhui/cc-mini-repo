# cc-mini Phase 4 Runtime Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen the separation between `standard` and `wiki_strict` so the stable general interaction mode stays untouched while the coding workflow gets its own guarded runtime assumptions and visibly distinct runtime setup.

**Architecture:** This is the phase where logical separation becomes deliberate runtime separation. Keep the user-facing `standard` story boring and stable. Make `wiki_strict` own clearly separated runtime branches for tool selection, prompt policy, state gating, and workspace assumptions, while still allowing shared primitives where they remain harmless and explicit. The goal is visible runtime separation, not a full double-runtime rewrite.

**Execution Split:** The task-level execution plan for this phase lives in [2026-04-21-cc-mini-phase4-execution-split.md](./2026-04-21-cc-mini-phase4-execution-split.md). Use that file for subagent or GSD task transcription; keep this file as the higher-level phase boundary reference.

**Tech Stack:** Python 3.11, pytest, argparse, rich

---

## Direction Check

Phase 4 should feel like a consolidation pass, not a feature explosion. The point is to reduce accidental coupling that will otherwise slow down future coding and agent work, while keeping shared low-level primitives only where they do not blur mode-specific behavior.

---

## Milestone 1: Mode-Specific Runtime Boundaries

### Task M4-T1: Split mode-specific runtime setup paths

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

### Task M4-T2: Separate prompt and state assumptions by mode

**Goal:** Ensure the prompt policy and persistent state assumptions for `standard` do not quietly inherit `wiki_strict` assumptions, while keeping the shared runtime pieces explicit.

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

**Explicit dependencies:** `M4-T1`

**Verification:**
- Static check: `rg -n "plan mode|wiki_strict|standard|flow_state|prompt" src/core/context.py src/core/flow_state.py tests/test_main.py`
- Minimal run: `python -m pytest tests/test_main.py -k standard -v`
- Related tests: `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

**Done criteria:**
- The two modes have distinct assumptions that are visible in code and tests.
- `standard` remains a clean general interaction surface.

---

## Milestone 2: Isolation Regression and Migration Notes

### Task M4-T3: Add cross-mode isolation regression coverage

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

**Explicit dependencies:** `M4-T1`, `M4-T2`

**Verification:**
- Static check: `rg -n "analysis-first|later-phase|standard|wiki_strict" tests/test_mode_isolation.py src/core/main.py`
- Minimal run: `python -m pytest tests/test_mode_isolation.py -v`
- Related tests: `python -m pytest tests/test_main.py tests/test_commands.py -v`

**Done criteria:**
- Mode leakage becomes a test failure instead of a user surprise.
- The stable mode stays stable.

### Task M4-T4: Update docs to describe the isolation boundary

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

**Explicit dependencies:** `M4-T3`

**Verification:**
- Static check: `rg -n "standard|wiki_strict|isolation|Phase 4" README.md docs/superpowers/specs/2026-04-20-cc-mini-32k-wiki-strict-design.md`
- Minimal run: `python -m pytest tests/test_mode_isolation.py tests/test_main.py -v`
- Related tests: `python -m pytest tests/test_commands.py tests/test_permissions.py -v`

**Done criteria:**
- The docs explain the runtime boundary without ambiguity.
- The stable mode story remains easy to understand.
