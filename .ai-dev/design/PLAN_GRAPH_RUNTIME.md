# PlanGraph Runtime Design

## 1. Purpose

PlanGraph supports bounded planning when a repository is empty or when CodeGraph is unavailable.

Before code exists, there is no CodeGraph. Therefore the system needs a planning-time graph.

## 2. Core Problem

A user may start from:

- an empty repository
- a broad product idea
- a large design requirement
- a migration plan
- a partially written README

A single huge planning prompt can exceed `context_window=N`.

Planning itself must be bounded, incremental, and recoverable.

## 3. Design Goal

PlanGraph Runtime must support:

```text
goal intake
project charter
requirements extraction
architecture slicing
decision recording
task DAG creation
plan preservation
handoff to CodeGraph after scaffold exists
```

## 4. Non-Goals

PlanGraph does not replace CodeGraph after code exists.

PlanGraph does not require a full architecture in one call.

PlanGraph does not generate production code by itself.

PlanGraph does not require real LLM calls in unit tests.

## 5. Core Principle

Do not use:

```text
large goal -> one huge plan -> full architecture -> full task list
```

Use:

```text
large goal -> project charter -> PlanGraph -> architecture slices -> task DAG -> execution packs
```

## 6. PlanGraph Data Model

Recommended logical schema:

```json
{
  "run_id": "run-...",
  "project_name": "",
  "phase": "intake",
  "goal": "",
  "non_goals": [],
  "constraints": [],
  "assumptions": [],
  "modules": [],
  "interfaces": [],
  "risks": [],
  "open_questions": [],
  "decisions": [],
  "acceptance_tests": [],
  "task_dag": [],
  "artifacts": [],
  "next_action": ""
}
```

## 7. Planning Phases

### Phase 0: Intake

Extract the smallest useful understanding of the user's goal.

Output:

```text
project-charter.md
initial plan-graph.json
```

### Phase 1: Charter

Create:

```text
primary goal
success criteria
non-goals
constraints
known unknowns
first milestone
```

### Phase 2: SpecGraph

Convert the charter into structured requirements:

```text
capabilities
interfaces
configuration needs
runtime assumptions
testing expectations
safety constraints
```

### Phase 3: Architecture Slices

Expand one slice at a time, for example:

```text
runtime profile
context budget
preservation pipeline
PlanGraph
CodeGraph retrieval
context pack
batch runner
workflow commands
```

### Phase 4: Task DAG

Generate layered work:

```text
milestone
feature
implementation task
test gate
documentation gate
```

Each task should include:

```text
id
goal
depends_on
allowed_files
forbidden_files
test_strategy
context_budget_hint
acceptance_criteria
```

### Phase 5: Scaffold

Generate minimal code only after stable PlanGraph decisions.

### Phase 6: CodeGraph Handoff

After code exists:

```text
PlanGraph explains why and what.
CodeGraph explains where and how.
Runtime State explains what happened so far.
```

## 8. Plan Preservation

When planning approaches `N`, preserve:

```text
confirmed goals
confirmed non-goals
decisions
open questions
modules
interfaces
risks
next action
```

Write to:

```text
.ai-dev/runtime/<run-id>/plan-graph.json
.ai-dev/runtime/<run-id>/planning/step-xxx.md
.ai-dev/runtime/<run-id>/planning/decisions.md
.ai-dev/runtime/<run-id>/planning/open-questions.md
```

## 9. Large Requirement Handling

Large requirements must become:

```text
raw artifact path
chunk summaries
structured requirement summary
open questions
```

Do not copy full raw requirement text into prompt.

## 10. PlanGraph vs Runtime State

PlanGraph stores desired design and decisions.

Runtime State stores actual execution progress.

Both are required.

## 11. PlanGraph vs CodeGraph

PlanGraph is used before code exists and continues to explain intent after code exists.

CodeGraph is used after code exists to locate files, symbols, callers, tests, and impact radius.

Recommended transition:

```text
empty repo:
  PlanGraph only

early scaffold:
  PlanGraph + partial CodeGraph

active development:
  PlanGraph + CodeGraph + Runtime State

maintenance:
  CodeGraph primary, PlanGraph for goals and task dependencies
```

## 12. Commands

Initial conservative commands:

```text
/plan-init <goal>
/plan-status
/plan-export
```

### /plan-init

Creates a runtime run and initial PlanGraph.

It must not write product code.

### /plan-status

Shows current planning phase, decisions, open questions, and next action.

### /plan-export

Exports a compact planning summary for external tools or another agent.

## 13. Planning Agent Constraints

The Planner Agent must:

- produce structured output
- avoid long prose unless needed
- record decisions explicitly
- separate assumptions from facts
- identify open questions
- avoid writing product code
- avoid reading full repositories
- respect the current budget report

## 14. Acceptance Criteria

PlanGraph Runtime is acceptable when:

- an empty repo can be initialized with a goal
- PlanGraph can be created without CodeGraph
- large goals can be chunked into structured planning state
- planning can preserve state near context limit
- task DAG can be generated incrementally
- scaffold handoff to CodeGraph is explicitly defined
- tests do not call real LLMs
