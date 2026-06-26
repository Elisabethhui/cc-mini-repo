# Bounded Agent Runtime Design

## Status
This document defines the bounded multi-agent execution model for cc-mini.
The purpose is not to create many autonomous agents. The purpose is to make each step smaller, cheaper, safer, and recoverable under `context_window=N`.

## Core Principle
Bad design:

```text
many agents
each reads the whole repo
each repeats reasoning
each produces long unstructured output
```

Good design:

```text
one coordinator
small workers
strict budgets
structured inputs
structured outputs
shared runtime state
CodeGraph-first retrieval
context packs per step
```

## Architecture

```text
User Goal
  ↓
Coordinator
  ↓
Context Governor
  ↓
PlanGraph or CodeGraph Retrieval
  ↓
Context Pack
  ↓
Worker Agent
  ↓
Runtime State
  ↓
Test / Review / Next Gate
```

## Agent Roles

### Coordinator
Understands current phase, chooses next step, respects max_steps, requests packs, merges worker results, writes runtime state, decides continue/preserve/split/block.
The Coordinator should not read large files directly.

### Planner Agent
Updates PlanGraph, produces task slices, records assumptions, records decisions, identifies open questions. It does not modify product code.

### Retriever Agent
Queries CodeGraph, falls back to rg, identifies relevant files/symbols/tests, and returns compact evidence. It does not implement code.

### Context Packer
Mostly deterministic service. Ranks context items, fits content into N, keeps P0/P1 items, summarizes/externalizes low priority items, produces budget report.

### Implementer Agent
Applies bounded changes, respects allowed_files, avoids unrelated refactors, avoids speculative abstractions, and produces concise change summary.
It must not explore the whole repo again.

### Tester Agent
Chooses minimal tests, analyzes failures, recommends fix direction.

### Reviewer Agent
Reviews compact diff, checks scope/tests/risks, returns approve/revise/rollback/split.

## Runtime Blackboard
Agents communicate through:

```text
.ai-dev/runtime/<run-id>/
```

Suggested structure:

```text
state.json
plan-graph.json
budget-reports.jsonl
steps/
artifacts/
context-packs/
reviews/
```

This is local runtime state and must not be committed.

## Agent Protocol
Each agent call defines:

```text
role
goal
input schema
output schema
budget
allowed actions
forbidden actions
stop condition
```

Example:

```json
{
  "agent": "Implementer",
  "goal": "Add RuntimeProfile core",
  "budget_tokens": 12000,
  "allowed_files": ["src/core/runtime_profile.py", "tests/test_runtime_profile.py"],
  "forbidden_actions": ["commit", "push", "delete unrelated files"],
  "expected_output": {
    "status": "done | revise | blocked",
    "changed_files": [],
    "test_commands": [],
    "risks": [],
    "next_action": ""
  }
}
```

## Context Pack Requirement
Every worker receives a context pack, not full conversation history.

A pack contains task goal, current phase, relevant PlanGraph facts, CodeGraph summary, allowed files, forbidden files, key snippets, test recommendations, budget report, stop condition.

It must not contain full repo, large logs, large diffs, unbounded chat history, or unbounded search output.

## CodeGraph Usage
When code exists, code understanding is CodeGraph-first:

```text
CodeGraph locates.
Source snippets verify.
Context Pack executes.
```

If CodeGraph is unavailable, fallback to rg and manual snippets.

## Empty Repository Mode
When no code exists:

```text
goal intake
project charter
SpecGraph
architecture slices
task DAG
scaffold
CodeGraph init
```

After scaffold exists, use PlanGraph + CodeGraph.

## Step Lifecycle

```text
1. Load runtime state
2. Calculate context budget
3. Retrieve or plan
4. Build context pack
5. Call one worker agent
6. Save StepResult
7. Run gate
8. Decide next state
```

## Batch Runner States

```text
intake
plan
retrieve
pack
implement
test
review
preserve
split
done
blocked
```

## Safety Boundaries
The runtime must not automatically:

```text
git commit
git push
git reset --hard
delete files broadly
run destructive shell commands
modify credentials
change CI/CD secrets
```

These require explicit user confirmation.

## Workflow Gates
Integrate existing workflow capabilities:

```text
test selector
review packet
work log
rollback helper
workflow next
```

A task is done only when implementation is complete, test evidence exists or is explicitly skipped, review decision allows completion, runtime state is saved, and next action is clear.

## Failure Handling
Classify failures:

```text
budget_failure
retrieval_failure
implementation_failure
test_failure
review_failure
permission_blocked
unknown_failure
```

Each failure records reason, artifact path, safe next action, and whether resume is possible.

## Acceptance Criteria
- agents have narrow roles.
- each step has a budget.
- each step writes runtime state.
- CodeGraph is used first when code exists.
- PlanGraph is used when code does not exist.
- context packs replace raw history.
- preserve/split can happen before hard stop.
- resume can continue from saved state.
- tests use fake LLMs and fake retrieval.
- no agent can spawn unlimited agents.
