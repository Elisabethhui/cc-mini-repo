# N-Context Runtime Design

## Status
This is the baseline design for cc-mini's bounded-context runtime after Task 051.
The runtime must support configurable `context_window=N`, not a hard-coded 32K value.

## Goal
Build a coding runtime that can continue useful work under a bounded context limit by using:
- runtime profile
- context budget calculator
- preservation pipeline
- external runtime state
- context packs
- CodeGraph-first retrieval when code exists
- PlanGraph when code does not exist
- bounded multi-step execution

## Core Formula
Every model call must satisfy:

```text
fixed_overhead
+ current_state
+ packed_context
+ messages
+ tool_results
+ reserved_output
+ safety_margin
<= context_window
```

Where `context_window=N` is configurable.

## Non-Goals
- Do not require the model to read a full codebase.
- Do not require a whole task to finish in one call.
- Do not require CodeGraph in an empty repository.
- Do not let agents spawn unlimited agents.
- Do not automatically commit, push, reset, delete, or run destructive shell commands.
- Do not require ordinary tests to use real OMLX, real CodeGraph, or real LLM.

## Runtime Invariants
1. `context_window` is configurable.
2. Input budget and output budget are separate.
3. `CC_MINI_MAX_TOKENS` means output budget only.
4. Hard stop is the last fallback, not the main mechanism.
5. Important state must be externalized.
6. Large raw artifacts must be saved by path and summarized.
7. Runtime artifacts must stay ignored.
8. Unit tests must use fakes/mocks.

## Budget Report
Before each model call, produce:

```text
context_window
system_prompt_tokens
tool_schema_tokens
message_tokens
packed_context_tokens
tool_result_tokens
reserved_output_tokens
safety_margin_tokens
projected_total_tokens
available_input_tokens
state
warnings
```

States:

```text
ok
warning
preserve
split
hard_stop
```

## State Semantics

### ok
Continue normally.

### warning
Do light cleanup: drop low-value history, truncate old tool outputs, prefer summaries.

### preserve
Stop appending raw context. Extract structured state, write runtime artifacts, repack, and continue safely.

### split
Current input/task is too large for one bounded step. Split into smaller executable batches.

### hard_stop
Do not call the model. Save checkpoint/state and require human decision or narrower scope.

## Preservation Pipeline
When entering `preserve`, run:

```text
1. Freeze
2. Extract
3. Persist
4. Materialize artifacts
5. Repack
6. Continue or ask
```

Extract:

```text
current goal
phase
decisions
open questions
files seen
symbols seen
test evidence
risks
next action
```

Persist under:

```text
.ai-dev/runtime/<run-id>/state.json
.ai-dev/runtime/<run-id>/steps/step-xxx.md
.ai-dev/runtime/<run-id>/budget-reports.jsonl
.ai-dev/runtime/<run-id>/artifacts/
```

## Configuration
Recommended env vars:

```text
CC_MINI_CONTEXT_WINDOW
CC_MINI_MAX_OUTPUT_TOKENS
CC_MINI_SAFETY_MARGIN_TOKENS
CC_MINI_AUTO_COMPACT
CC_MINI_AUTO_APPROVE
CC_MINI_AUTO_BATCH
CC_MINI_MAX_BATCH_STEPS
```

Recommended TOML:

```toml
[context]
window = 32768
max_output_tokens = 2048
safety_margin_tokens = 2048

[context.thresholds]
warning_ratio = 0.65
preserve_ratio = 0.75
split_ratio = 0.85
hard_stop_ratio = 0.92

[tools]
single_tool_result_max_chars = 6000
turn_tool_result_max_chars = 12000

[batch]
enabled = true
max_steps = 5
```

## Local OMLX / MLX Model Runtime
Use existing OpenAI-compatible provider path:

```text
provider=openai
base_url=http://localhost:8000/v1
model=Qwen3.5-9B-MLX-4bit
context_window=32768
max_output_tokens=2048
```

Do not add `provider=local` in the first implementation.

## Tool Output Governance
Use both:

```text
single_tool_result_max_chars
turn_tool_result_max_chars
```

Large output should become artifact handle plus structured summary.

## Runtime Local Artifacts
Must remain ignored:

```text
.ai-dev/runtime/
.ai-dev/context-packs/
.ai-dev/worklogs/
.ai-dev/checkpoints/
.ai-dev/tmp/
.codegraph/
.codebase-memory/
```

## Acceptance Criteria
- `context_window` can be configured.
- output budget is separate from context window.
- budget includes reserved output and safety margin.
- unknown OpenAI-compatible models do not default to 200K.
- pressure/preserve/split states exist.
- hard stop prevents unsafe model calls.
- preservation can save state before stopping.
- tests do not require real LLM or CodeGraph.
