# Context-Bounded Workflow Roadmap

This document explains why the `feature/context-bounded-dev-bootstrap` branch exists and what the 000-070 task path changed.

## 1. Why This Branch Exists

The original problem is that a small local model, such as a 32K Qwen / MLX / OMLX runtime, cannot reliably handle a large software development task if the model has to read the whole repository, reason about the whole architecture, modify code, test, review, and recover all inside one chat context.

The goal of this branch is to make complex coding work possible under a bounded context window:

```text
large goal
  -> structured planning
  -> code intelligence
  -> compact context pack
  -> bounded implementation
  -> test gate
  -> review gate
  -> work log
  -> rollback/resume
```

This is not only for 32K. The runtime treats the context window as `N`.

32K is the strict baseline.

## 2. Overall Product Goal

The target system is:

```text
N-Context Graph-First Coding Runtime
```

It should support:

- local OpenAI-compatible models
- configurable context windows
- CodeGraph-first retrieval for existing repositories
- PlanGraph-first planning for empty repositories
- context pack generation
- runtime state persistence
- budget-aware execution
- supervised multi-step workflow execution
- resumable runs
- test/review/worklog/rollback gates

## 3. Design Principles

### Context is a budget, not a pile of text

The model should not read the whole repository by default.

It should receive a compact context pack selected for the current task.

### CodeGraph locates, source snippets verify

CodeGraph or code-intelligence tools should identify relevant symbols, files, tests, and impact area.

Source reads should be small and targeted.

### PlanGraph exists before code exists

For empty repositories, CodeGraph has nothing to index. PlanGraph captures product goals, modules, constraints, task DAG, risks, decisions, and next action.

### Runtime state replaces chat memory

Long workflows must not rely on the current chat session.

State is written to `.ai-dev/runtime/` and can be resumed.

### Gates prevent silent failure

Every serious change should pass through:

- budget check
- test recommendation
- review packet
- work log
- rollback guidance

## 4. Task Path Summary

### Tasks 000-020: Workflow Foundation

These tasks created the context-bounded development scaffold:

- `.ai-dev/` structure
- workflow skills
- templates
- initial design documents
- file boundary rules
- local artifact separation

Purpose:

```text
separate product code from AI workflow files and local runtime artifacts
```

### Tasks 021-026: First Real Workflow Loop

These tasks validated the workflow with the first product command:

- `/workflow-status`
- closeout flow
- stable runner
- task execution discipline

Purpose:

```text
prove that one small feature can be implemented, tested, reviewed, and committed cleanly
```

### Tasks 027-030: Route Alignment

These tasks aligned the plan:

- workflow init plan
- workflow doctor plan
- CodeIntel provider plan
- context pack generator plan
- task route and command surface alignment

Purpose:

```text
avoid competing task routes and lock a single implementation path
```

### Tasks 031-036: Workflow Setup + Code Intelligence

Implemented:

- `/workflow-init`
- `/workflow-doctor`
- CodeIntel provider
- `/codeintel-status`
- `/codeintel-query`

Purpose:

```text
make the project self-checking and make code lookup compact
```

### Tasks 037-042: Workflow Gates

Implemented:

- test selector
- `/workflow-test`
- review packet builder
- work log generator
- rollback helper
- workflow next-state recommender

Purpose:

```text
make coding work verifiable, reviewable, recordable, and recoverable
```

### Tasks 043-050: First Convergence

Produced:

- wiki_strict boundary review
- prompt minimization review
- workflow docs
- migration guide
- config defaults review
- end-to-end dry run
- final review
- merge plan

Purpose:

```text
stabilize the first context-bounded workflow layer
```

### Task 051: N-Context Runtime Design

Added the major design documents:

- `N_CONTEXT_RUNTIME.md`
- `PLAN_GRAPH_RUNTIME.md`
- `BOUNDED_AGENT_RUNTIME.md`

Purpose:

```text
move from workflow scaffolding to a full N-context runtime architecture
```

### Task 052: Runtime Profile Core

Implemented runtime profile detection:

- provider
- model
- base_url
- context_window
- max_output_tokens
- safety_margin_tokens
- runtime kind
- streaming/tool-calling support

Purpose:

```text
make runtime behavior model-aware and local-model-aware
```

### Task 053: Context Budget Core

Implemented:

- `ContextBudgetCalculator`
- `BudgetReport`
- states: `ok`, `warning`, `preserve`, `split`, `hard_stop`

Purpose:

```text
separate input budget, output budget, safety margin, and projected total
```

### Task 054: Config and Env Integration

Added configuration support for:

- `CC_MINI_CONTEXT_WINDOW`
- `CC_MINI_MAX_OUTPUT_TOKENS`
- `CC_MINI_SAFETY_MARGIN_TOKENS`
- `CC_MINI_AUTO_COMPACT`
- `CC_MINI_AUTO_APPROVE`
- `[context]` TOML section

Purpose:

```text
let users configure N-context behavior without code changes
```

### Task 055: Engine Budget v2

Upgraded engine preflight:

- computes projected total before LLM calls
- includes reserved output and safety margin
- warning/preserve/split/hard_stop behavior
- blocks unsafe calls at hard stop

Purpose:

```text
prevent context overflow before it happens
```

### Task 056: Runtime State Store

Implemented `.ai-dev/runtime/` state:

- run id
- phase
- current step
- goal
- decisions
- open questions
- artifacts
- budget reports
- next action

Purpose:

```text
make long workflows recoverable outside chat history
```

### Task 057: Preservation Pipeline

Implemented:

- structured state preservation
- large tool output materialization
- split/hard_stop recommendations

Purpose:

```text
when context pressure rises, preserve useful state instead of losing work
```

### Tasks 058-060: PlanGraph

Implemented:

- PlanGraph core
- planning commands
- planning preservation/chunking

Purpose:

```text
support empty repositories and large goals before code exists
```

### Tasks 061-063: Retrieval and Context Pack

Implemented:

- CodeGraph-first retrieval adapter
- ContextPackBuilder
- `/workflow-pack`

Purpose:

```text
turn a task into a bounded, prioritized context packet
```

### Tasks 064-068: Bounded Runtime Execution

Implemented:

- batch runner
- agent protocol
- `/workflow-run --dry-run`
- supervised execution
- `/workflow-resume`

Purpose:

```text
execute multi-step coding workflows under budget and permission control
```

### Tasks 069-070: Final Integration and Docs

Implemented:

- workflow gates integration
- final dry runs
- docs
- end-to-end tests

Purpose:

```text
verify empty-repo and existing-repo workflows
```

## 5. What This Branch Can Do Now

The branch can now support:

- local model configuration
- model health checks
- N-context budget calculation
- workflow initialization and diagnostics
- planning for empty repositories
- CodeGraph-first retrieval for existing repositories
- context pack generation
- workflow dry runs
- supervised workflow execution
- resume from runtime state
- test/review/worklog/rollback gates

## 6. What It Does Not Guarantee Yet

This branch does not guarantee:

- every local model supports tool calling
- every CodeGraph installation behaves identically
- supervised execution will always complete a large feature without human intervention
- no manual review is needed

The system is designed to make bounded coding safer and more observable, not fully autonomous.

## 7. Recommended Next Product Work

After this branch:

- polish user-facing command help
- add examples for OMLX/Qwen
- add screenshots or terminal transcripts
- test with a real medium-size repository
- add provider-specific model profiles
- improve CodeGraph installation guidance
- add CI coverage for Python 3.11 and 3.14 if both are supported

