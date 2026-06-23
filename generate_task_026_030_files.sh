#!/usr/bin/env bash
set -eu

mkdir -p .ai-dev/design
mkdir -p .ai-dev/templates

cat > .ai-dev/templates/TASK_026_WORKFLOW_STATUS_REVIEW.md <<'EOF'
# Current Task: task-026

## Goal

Run the final map-sync, test-gate, fresh-review, and work-log pass for the `workflow status` feature after task-024 and task-025 are implemented.

This task does not add new feature behavior. It verifies, reviews, and closes out the first product implementation.

## Why

The workflow status feature is the first real product change in the context-bounded workflow system. It must prove that the process works end to end:

- implementation
- map sync
- targeted tests
- fresh review
- rollback path
- work log

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 1
- max_iterations: 1

## Depends On

- task-024 workflow status core module
- task-025 workflow status command wiring

## Allowed Read

- `src/core/workflow_status.py`
- `src/core/commands.py`
- `src/core/main.py` if changed
- `tests/test_workflow_status.py`
- `tests/test_commands.py`
- `tests/test_main.py` if changed
- relevant git diff

## Allowed Edit

Only local ignored artifacts unless a tiny documentation/workflow note is explicitly needed:

- `.ai-dev/worklogs/`
- `.ai-dev/tmp/`

Do not edit product code in this review task unless review finds a small blocking issue and the user explicitly approves a revise step.

## Do Not Do

- Do not add new workflow commands.
- Do not refactor command routing.
- Do not expand scope into workflow init.
- Do not change CodeGraph provider behavior.
- Do not commit local task artifacts.
- Do not ignore failed tests.

## Required Commands

```bash
git status --short
git diff --stat
git diff --name-only
```

If CodeGraph is available:

```bash
codegraph sync
codegraph status
git diff --name-only | codegraph affected --stdin --quiet
```

Run targeted tests:

```bash
pytest tests/test_workflow_status.py -v
pytest tests/test_commands.py -v
```

If `src/core/main.py` changed:

```bash
pytest tests/test_main.py -v
PYTHONPATH=src python -m core.main --help
```

## Fresh Review Packet

Include:

- original task goal
- changed files
- diff stat
- targeted tests run
- test result
- CodeGraph freshness state
- known risks
- rollback path

## Acceptance Criteria

- map-sync decision is recorded
- targeted tests are run or failure is classified
- fresh review recommendation is explicit
- no local workflow artifacts are staged
- rollback path is concrete
- commit decision is clear

## Review Decision

Use one:

- commit
- revise
- rollback
- reslice
- hold

## Rollback

Before commit:

```bash
git restore src/core/workflow_status.py tests/test_workflow_status.py
git restore src/core/commands.py tests/test_commands.py
```

If touched:

```bash
git restore src/core/main.py tests/test_main.py
```
EOF

cat > .ai-dev/design/WORKFLOW_INIT_PLAN.md <<'EOF'
# Workflow Init Command Plan

## Purpose

Plan the second product command in the context-bounded workflow feature:

`cc-mini workflow init`

This document is design-only. Do not implement from this file without creating a current task card first.

## Goal

Add a safe initializer that creates missing workflow scaffold files for a repository.

The command should help users adopt the context-bounded workflow without manually copying many files.

## Why After Status

`workflow status` is read-only and tells users what is missing.

`workflow init` is the next logical command because it can fill those missing workflow pieces.

## Non-Goals

Do not implement yet:

- task generation
- context pack generation
- CodeGraph queries
- test execution
- review automation
- commit automation
- state router
- full skill installation marketplace

## Safety Rules

`workflow init` must be conservative.

It should:

- create missing files only
- never overwrite existing files without confirmation
- print a clear summary
- update `.gitignore` only with explicit user approval
- not run model calls
- not initialize CodeGraph automatically unless user asks
- not commit changes

## Proposed User Experience

```bash
cc-mini workflow init
```

Expected behavior:

1. Detect repository root.
2. Check existing workflow files.
3. Show missing files.
4. Ask before writing.
5. Create missing scaffold files.
6. Print next step.

Possible output:

```text
Context-Bounded Workflow Init

Missing:
  .ai-dev/WORKFLOW.md
  .ai-dev/templates/CURRENT_TASK.md
  .ai-dev/skills/task-slicer/SKILL.md

Will create missing files only.
No product code will be changed.

Next:
  Run `cc-mini workflow status`
```

## Required Files

Initializer may create:

- `AGENTS.md`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/PROJECT_MAP.md`
- `.ai-dev/CODEGRAPH.md`
- `.ai-dev/TESTING.md`
- `.ai-dev/templates/`
- `.ai-dev/skills/`

But first version should be smaller.

Recommended v1 creates only:

- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/templates/CURRENT_TASK.md`
- `.ai-dev/templates/CONTEXT_PACK.md`
- `.ai-dev/templates/TEST_GATE.md`
- `.ai-dev/templates/REVIEW_ROLLBACK.md`
- `.ai-dev/templates/WORK_LOG.md`

Keep skill generation for later unless already bundled cleanly.

## Implementation Areas

Likely files:

- `src/core/workflow_status.py` or new `src/core/workflow_init.py`
- `src/core/commands.py`
- `tests/test_workflow_init.py`
- `tests/test_commands.py`

## Acceptance Criteria

- creates missing workflow files
- does not overwrite existing files by default
- works outside git but warns
- updates no product code
- prints created/skipped files
- has tests using temporary directories
- does not require CodeGraph

## Test Plan

Targeted tests:

```bash
pytest tests/test_workflow_init.py -v
pytest tests/test_commands.py -v
```

Test cases:

- empty temp repo creates expected files
- existing files are not overwritten
- partial scaffold creates only missing files
- missing git repo does not crash
- command output is stable enough

## Risks

- init becomes too broad
- overwrites user files
- creates too many files
- duplicates repository-specific workflow files
- conflicts with manually maintained AGENTS.md

## First Executable Task

Create a task card:

`task-027 implement workflow init scaffold writer`

Keep it limited to file creation helpers and tests first.
EOF

cat > .ai-dev/design/WORKFLOW_DOCTOR_PLAN.md <<'EOF'
# Workflow Doctor Command Plan

## Purpose

Plan a read-only diagnostic command:

`cc-mini workflow doctor`

Doctor should perform deeper checks than `workflow status`.

## Goal

Help users identify workflow setup issues, ignored-file leaks, stale CodeGraph state, malformed workflow files, and possible secret exposure.

## Relationship To Status

`workflow status` is quick and friendly.

`workflow doctor` is deeper and more diagnostic.

Use status before normal work.
Use doctor when something feels wrong or before a major commit.

## Non-Goals

Do not implement yet:

- automatic fixes
- automatic secret removal
- automatic commits
- full markdown parsing engine
- full static analysis
- CodeGraph database inspection

## Checks

Doctor should check:

- required workflow files
- ignored local artifact paths
- tracked cache files
- staged local artifacts
- CodeGraph availability
- CodeGraph initialization
- CodeGraph freshness if possible
- malformed Markdown code fences in `.ai-dev/skills`
- potential secrets in staged diff
- pycache or generated files tracked by git

## Suggested Command

```bash
cc-mini workflow doctor
```

Output shape:

```text
Context-Bounded Workflow Doctor

File boundary:
  OK ignored local task artifacts
  WARN .pytest_cache tracked by git

Markdown:
  OK skill code fences

CodeGraph:
  WARN not installed

Secrets:
  OK no obvious staged secrets

Decision:
  pass-with-warnings
```

## Severity Levels

- `ok`
- `warn`
- `fail`
- `blocked`

Use `blocked` for:

- obvious staged secrets
- local artifact directories staged
- workflow files malformed enough to break use

## Implementation Areas

Likely files:

- `src/core/workflow_status.py`
- maybe new `src/core/workflow_doctor.py`
- `src/core/commands.py`
- `tests/test_workflow_doctor.py`

## Acceptance Criteria

- read-only
- does not mutate files
- works without CodeGraph
- detects ignored path problems
- detects staged local artifacts
- detects simple unclosed code fences in workflow files
- flags obvious secret patterns in staged diff
- has targeted tests

## Test Plan

```bash
pytest tests/test_workflow_doctor.py -v
pytest tests/test_commands.py -v
```

Test cases:

- clean scaffold passes
- missing ignored path warns/fails
- staged local artifact blocks
- unclosed code fence fails
- fake secret in staged diff blocks
- CodeGraph missing warns but does not fail

## Risks

- false positives in secret detection
- too much output for small models
- command becomes slow
- doctor starts fixing things unexpectedly

## First Executable Task

Create task:

`task-028 implement workflow doctor read-only checks`

Start with file boundary and markdown fence checks only.
EOF

cat > .ai-dev/design/CODEINTEL_PROVIDER_IMPLEMENTATION_PLAN.md <<'EOF'
# CodeIntel Provider Implementation Plan

## Purpose

Plan the first implementation of a CodeIntel provider abstraction.

This turns CodeGraph usage from a written workflow into a reusable product capability.

## Goal

Add a small internal provider layer that can answer code intelligence questions without requiring the model to read large files.

## First Provider Scope

Implement only these first:

- detect CodeGraph availability
- detect `.codegraph/` initialization
- run `codegraph status`
- run `codegraph query <keyword>`
- fallback to `rg` when CodeGraph is unavailable

Do not implement full impact/call graph in the first pass.

## Non-Goals

Do not implement yet:

- full MCP client
- Codebase-Memory-MCP integration
- daemon management
- semantic search abstraction
- automatic context-pack generation
- automatic test selection

## Proposed Module

Recommended new file:

```text
src/core/codeintel.py
```

Possible types:

```python
@dataclass
class CodeIntelResult:
    provider: str
    query: str
    ok: bool
    items: list[str]
    warnings: list[str]
    truncated: bool = False

class CodeIntelProvider:
    def available(self) -> bool:
        ...

    def status(self) -> CodeIntelResult:
        ...

    def query(self, keyword: str) -> CodeIntelResult:
        ...
```

Keep it simple and consistent with existing project style.

## Provider Order

1. CodeGraph
2. rg fallback

If CodeGraph fails:

- record warning
- return fallback results
- do not crash

## Security And Safety

- use subprocess safely
- do not run shell=True unless existing project style requires it
- apply timeout
- trim output
- do not expose huge raw output
- never read `.codegraph/` database directly

## Output Limits

Default output limits:

- max items: 20
- max lines: 200
- max chars: small enough for a 32k context workflow

If output is truncated, set:

```text
truncated: true
```

## Implementation Areas

Likely files:

- `src/core/codeintel.py`
- `tests/test_codeintel.py`

Optional later:

- `src/core/commands.py`

## Acceptance Criteria

- can detect CodeGraph missing
- can detect CodeGraph present
- can query via CodeGraph when available
- can fallback to `rg`
- returns compact structured result
- handles timeout/failure gracefully
- has tests with mocked subprocess

## Test Plan

```bash
pytest tests/test_codeintel.py -v
```

Test cases:

- CodeGraph missing
- CodeGraph status success
- CodeGraph query success
- CodeGraph timeout
- CodeGraph error
- rg fallback success
- output truncation

## Map Sync

When this implementation changes product code:

```bash
codegraph sync
codegraph status
```

## First Executable Task

Create task:

`task-029 implement CodeIntel provider detection and query`

Keep command wiring for a later task.
EOF

cat > .ai-dev/design/CONTEXT_PACK_GENERATOR_PLAN.md <<'EOF'
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
EOF

echo "Generated task 026-030 files."
echo "Next:"
echo "  git add .ai-dev/templates/TASK_026_WORKFLOW_STATUS_REVIEW.md"
echo "  git add .ai-dev/design/WORKFLOW_INIT_PLAN.md"
echo "  git add .ai-dev/design/WORKFLOW_DOCTOR_PLAN.md"
echo "  git add .ai-dev/design/CODEINTEL_PROVIDER_IMPLEMENTATION_PLAN.md"
echo "  git add .ai-dev/design/CONTEXT_PACK_GENERATOR_PLAN.md"
echo "  git commit -m \"Add workflow review init doctor codeintel and context pack plans\""
