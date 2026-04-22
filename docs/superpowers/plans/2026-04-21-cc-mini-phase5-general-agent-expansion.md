# cc-mini Phase 5 General Agent Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand cc-mini from a strong local coding workflow into a broader general agent while preserving the coding-first path, the stable `standard` mode, and the ability to start with coding-adjacent task expansion before broader non-coding tasks.

**Architecture:** This phase should reuse the mature workflow primitives built earlier and extend them into broader task intake, orchestration, and evaluation. It is intentionally later than the coding and continuity phases because general-agent flexibility is only safe once the specialized workflow is already reliable. The first extension target should stay close to coding: planning, requirement shaping, task decomposition, and other coding-adjacent work, while keeping the design open enough to add a smaller non-coding task surface later.

**Tech Stack:** Python 3.11, pytest, argparse, rich

---

**Execution Split:** The task-level execution plan for this phase lives in [2026-04-21-cc-mini-phase5-execution-split.md](./2026-04-21-cc-mini-phase5-execution-split.md). Use that file for subagent or GSD task transcription; keep this file as the higher-level phase boundary reference.

---

## Direction Check

This phase is not about making cc-mini "do everything" overnight. It is about safely widening the kind of tasks it can handle once the coding workflow, continuity, and mode separation are already trustworthy, with coding-adjacent support taking priority over broader non-coding expansion.

---

## Milestone 1: General Task Intake

### Task M5-T1: Broaden the command surface from coding-only to task-oriented intake

**Goal:** Let cc-mini accept more general task descriptions without assuming they are always code-change requests, while still favoring coding-adjacent tasks first.

**Files:**
- Modify: `src/core/commands.py`
- Modify: `src/core/coordinator.py`
- Modify: `tests/test_commands.py`

**Allowed changes:**
- Add task-routing logic for non-coding requests.
- Keep the coding workflow intact.
- Make task intent explicit enough to route to the right handling path.
- Prefer coding-adjacent routes when the task can reasonably be expressed that way.

**Forbidden changes:**
- Do not break coding workflows to accommodate general tasks.
- Do not weaken `standard`.
- Do not hide the task type from the user.

**Explicit dependencies:** Phases 2-4 completion

**Verification:**
- Static check: `rg -n "coordinator|task|coding|general" src/core/commands.py src/core/coordinator.py tests/test_commands.py`
- Minimal run: `python -m pytest tests/test_commands.py -v`
- Related tests: `python -m pytest tests/test_mode_isolation.py tests/test_main.py -v`

**Done criteria:**
- The agent can distinguish coding tasks from general tasks.
- The coding workflow remains the default when appropriate.

### Task M5-T2: Extend multi-agent orchestration to non-coding workflows

**Goal:** Reuse the existing agent/worker model for broader tasks without turning it into an unbounded router, and keep the first wave focused on tasks near the coding workflow.

**Files:**
- Modify: `src/core/worker_manager.py`
- Modify: `src/core/tools/agent.py`
- Modify: `tests/test_worker_manager.py`

**Allowed changes:**
- Add general-purpose orchestration hooks where useful.
- Keep worker boundaries clear.
- Preserve the current coding-centric behaviors.
- Make it possible to support smaller planning and document-oriented extensions without redesigning the router.

**Forbidden changes:**
- Do not make every task fan out to workers.
- Do not move all logic into orchestration.
- Do not weaken the permission model.

**Explicit dependencies:** `M5-T1`

**Verification:**
- Static check: `rg -n "WorkerManager|AgentTool|SendMessageTool|TaskStopTool" src/core/worker_manager.py src/core/tools/agent.py tests/test_worker_manager.py`
- Minimal run: `python -m pytest tests/test_worker_manager.py -v`
- Related tests: `python -m pytest tests/test_commands.py tests/test_mode_isolation.py -v`

**Done criteria:**
- Multi-step general tasks can be coordinated without breaking the coding workflow.
- Worker behavior is still explainable and bounded.

---

## Milestone 2: General Agent Evaluation and Guardrails

### Task M5-T3: Add general-agent evaluation and guardrail coverage

**Goal:** Make broader agent behavior testable so future expansion does not quietly regress the coding path or the stable mode, including the coding-adjacent first-wave behavior.

**Files:**
- Create: `tests/test_general_agent.py`
- Modify: `README.md`

**Allowed changes:**
- Add representative tests for general task routing and fallback behavior.
- Document how users should expect the broader agent to behave.
- Keep evaluation lightweight and practical.
- Mention that the first supported expansion wave stays near coding, with broader non-coding tasks as a later follow-on.

**Forbidden changes:**
- Do not promise broad autonomy without guardrails.
- Do not remove the coding-specific tests.
- Do not turn this into an open-ended benchmark project.

**Explicit dependencies:** `M5-T1`, `M5-T2`

**Verification:**
- Static check: `rg -n "general agent|routing|guardrail|coding" README.md tests/test_general_agent.py`
- Minimal run: `python -m pytest tests/test_general_agent.py -v`
- Related tests: `python -m pytest tests/test_mode_isolation.py tests/test_permissions.py -v`

**Done criteria:**
- General-agent behavior is observable and bounded.
- The docs explain the intended scope instead of overselling it.
