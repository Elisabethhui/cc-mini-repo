# Context Pack Generator Plan

## Purpose

Plan a future product feature that generates local context packs from task and code intelligence results.

Target future command:

`cc-mini workflow pack`

## Goal

Generate a small, local, ignored context pack for one task.

The context pack should help a small-context model implement the task without exploring the entire repository.

## Non-Goals

Do not implement yet:

- automatic code editing
- automatic task slicing
- full wiki generation
- long architecture summaries
- committing generated context packs
- replacing CodeGraph

## Inputs

Possible inputs:

- task file from `.ai-dev/tasks/`
- user goal
- CodeIntel results
- surface-search anchors
- testing registry
- project map

## Output

Local ignored file:

```text
.ai-dev/context-packs/task-xxx.md
```

Never committed by default.

## Content Tiers

Use context-tier-policy.

### Core

- files likely to edit
- target symbols
- short snippets

### Support

- direct callers/callees
- interfaces
- nearby tests
- signatures and summaries

### Peripheral

- broad impact
- risks
- paths and symbol names only

## Proposed Command

```bash
cc-mini workflow pack .ai-dev/tasks/task-xxx.md
```

Possible output:

```text
Context Pack Generated

Task:
  task-xxx

Output:
  .ai-dev/context-packs/task-xxx.md

Budget:
  32k

Core:
  2 files

Support:
  4 files

Peripheral:
  7 symbols summarized
```

## Implementation Areas

Likely future files:

- `src/core/context_pack.py`
- `src/core/codeintel.py`
- `src/core/commands.py`
- `tests/test_context_pack_generator.py`

## Acceptance Criteria

- reads task file
- includes task goal
- includes code intelligence summary
- applies tier policy
- writes local ignored context pack
- refuses to include secrets
- limits output size
- warns when task is too broad
- has tests

## Test Plan

```bash
pytest tests/test_context_pack_generator.py -v
```

Test cases:

- generates pack from small task
- warns on broad task
- respects output limits
- excludes ignored local artifacts
- redacts or blocks obvious secrets
- handles CodeIntel unavailable

## Risks

- generator becomes a wiki generator
- output gets too large
- raw CodeGraph dumps leak into context
- context packs accidentally staged
- model over-trusts incomplete context

## First Executable Task

Create task:

`task-030 design minimal context pack generator data model`

Implementation should wait until CodeIntel provider exists.
