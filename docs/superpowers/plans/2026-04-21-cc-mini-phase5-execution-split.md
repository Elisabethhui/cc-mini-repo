# cc-mini Phase 5 Execution Split

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand cc-mini into a bounded general-agent surface by adding explicit task intake, task-kind-aware worker orchestration, and guardrail tests/docs, while keeping the coding-first path the default and preserving the stable `standard` mode.

**Architecture:** Phase 5 should stay close to the existing coordinator and worker machinery instead of introducing a new routing subsystem. The first wave adds a dedicated task-intake path that classifies requests as coding-adjacent or broader general tasks, then threads a small `task_kind` hint through worker launches so orchestration can stay explicit and bounded. Tests and docs should prove that the new surface widens task handling without turning cc-mini into an unbounded router.

**Tech Stack:** Python 3.11, pytest, argparse, rich

---

## Milestone 1: Task Intake Surface

### Task M5-E1: Add a dedicated task-intake command and task-intent helper

**Goal:** Let users submit broader tasks through an explicit command surface that still prefers coding-adjacent routing when the task can be framed that way.

**Files:**
- Modify: `src/core/commands.py`
- Modify: `src/core/coordinator.py`
- Modify: `tests/test_commands.py`

**Allowed changes:**
- Add a lightweight task-intent helper that classifies incoming text as coding-adjacent or general.
- Add a `/task` slash command that queues a follow-up model query for broader task intake.
- Expand coordinator prompt language so task intake is explicitly coding-adjacent-first instead of coding-only.
- Add tests that lock in the new command/help behavior.

**Forbidden changes:**
- Do not change the behavior of `/plan`, `/prime`, `/scan`, or `/digest`.
- Do not introduce a new routing engine or task planner.
- Do not weaken `standard` mode or the existing permission model.

**Explicit dependencies:** Phases 1-4 completion

**Verification:**
- Static check: `rg -n "task-intake|coding-adjacent|/task|general task" src/core/commands.py src/core/coordinator.py tests/test_commands.py`
- Minimal run: `python -m pytest tests/test_commands.py -v`
- Related tests: `python -m pytest tests/test_main.py tests/test_mode_isolation.py -v`

**Done criteria:**
- `cc-mini /task ...` accepts a broader request and clearly signals how it will be treated.
- The coordinator prompt tells the model to prefer coding-adjacent decomposition when possible.
- Existing coding commands still behave exactly as before.

### Task M5-E2: Make worker orchestration task-kind aware

**Goal:** Carry a small task-kind hint through worker launches so research-oriented and broader general tasks stay bounded without changing the worker protocol into a router.

**Files:**
- Modify: `src/core/worker_manager.py`
- Modify: `src/core/tools/agent.py`
- Modify: `tests/test_worker_manager.py`

**Allowed changes:**
- Add an optional `task_kind` field to worker launches.
- Preserve the current worker execution model while recording the kind for status and notifications.
- Adjust the worker prompt or summary text to reflect coding/research/general intent when provided.
- Expand the `Agent` tool schema to expose the new task-kind hint.

**Forbidden changes:**
- Do not fan out every task into workers.
- Do not add a new agent type or a new routing subsystem.
- Do not weaken worker permissions or allow task kinds to bypass existing checks.

**Explicit dependencies:** `M5-E1`

**Verification:**
- Static check: `rg -n "task_kind|WorkerManager|AgentTool|SendMessageTool|TaskStopTool" src/core/worker_manager.py src/core/tools/agent.py tests/test_worker_manager.py`
- Minimal run: `python -m pytest tests/test_worker_manager.py -v`
- Related tests: `python -m pytest tests/test_commands.py tests/test_main.py -v`

**Done criteria:**
- Worker launches can be labeled as coding, research, or general without changing the launch protocol shape.
- Worker notifications preserve the new metadata clearly enough for the coordinator to reason about them.

## Milestone 2: General-Agent Guardrails

### Task M5-E3: Add general-agent tests and document the first expansion wave

**Goal:** Make the wider task-intake surface observable and bounded so the first general-agent wave stays near coding and does not regress the stable workflow.

**Files:**
- Create: `tests/test_general_agent.py`
- Modify: `README.md`

**Allowed changes:**
- Add representative tests for `/task` intake and task-kind-aware worker launches.
- Document the first-wave scope as coding-adjacent first, broader general tasks second.
- Describe guardrails plainly so the broader agent surface does not sound autonomous.

**Forbidden changes:**
- Do not remove coding-specific tests or documentation.
- Do not promise broad autonomy or unbounded task routing.
- Do not change Phase 1-4 behavior while writing the new docs/tests.

**Explicit dependencies:** `M5-E1`, `M5-E2`

**Verification:**
- Static check: `rg -n "general agent|coding-adjacent|/task|task_kind" README.md tests/test_general_agent.py`
- Minimal run: `python -m pytest tests/test_general_agent.py -v`
- Related tests: `python -m pytest tests/test_commands.py tests/test_worker_manager.py -v`

**Done criteria:**
- README explains the bounded general-agent expansion clearly.
- The new tests pin the first-wave behavior so later work cannot quietly broaden scope without review.

## Transcription Notes For GSD

- Keep the task boundaries small and execute them in order.
- Prefer one worker per task when the files do not overlap.
- If a task starts to grow into a new routing system, stop and split it.
- Keep the coding workflow as the default user experience.
