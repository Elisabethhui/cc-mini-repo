# Workflow Command Design

## Purpose

Design the future `cc-mini workflow` command family before implementation.

This is a product design document, not an implementation task.

## Product Goal

Add a small-context-friendly workflow surface to cc-mini.

The workflow commands should help users:

- inspect workflow readiness
- initialize workflow files
- locate relevant code
- build context packs
- select tests
- review changes
- record work logs

## Design Principles

1. Start read-only.
2. Prefer explicit user control.
3. Never auto-commit.
4. Never commit local task artifacts.
5. Keep output short enough for small-context models.
6. Provide next-step guidance instead of doing everything automatically.
7. Use CodeGraph when available, fallback to `rg` when unavailable.

## Proposed Command Family

### `cc-mini workflow status`

Read-only.

Checks:

- branch and git status
- `.ai-dev/` structure
- required workflow files
- ignored local artifact paths
- CodeGraph availability
- CodeGraph index presence
- obvious staged local artifacts
- obvious generated/cache files

Output:

- current workflow readiness
- warnings
- recommended next command

### `cc-mini workflow init`

Creates missing workflow scaffold files.

Should not overwrite existing files unless user confirms.

Creates or verifies:

- `AGENTS.md`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/templates/`
- `.ai-dev/skills/`
- `.gitignore` entries

### `cc-mini workflow doctor`

Read-only.

Deeper validation than `status`.

Checks:

- malformed markdown fences
- missing templates
- unignored local artifacts
- potential secrets
- CodeGraph stale/unavailable state
- pycache or generated files tracked by git

### `cc-mini workflow task new`

Creates a local ignored task file from template.

Example:

`cc-mini workflow task new "add workflow status command"`

Writes:

- `.ai-dev/tasks/task-xxx.md`

Does not commit.

### `cc-mini workflow surface`

Runs cold-start anchor discovery.

Inputs:

- user goal
- optional task file

Outputs:

- keywords
- candidate anchors
- next CodeGraph queries

### `cc-mini workflow code-intel`

Runs CodeGraph or fallback search.

Subcommands:

- `query`
- `callers`
- `callees`
- `impact`
- `affected`

### `cc-mini workflow pack`

Generates a local ignored context pack.

Inputs:

- task file
- surface search result
- code-intel result

Writes:

- `.ai-dev/context-packs/task-xxx.md`

### `cc-mini workflow sync`

Runs map sync barrier.

Checks:

- changed files
- CodeGraph status
- CodeGraph sync
- freshness

### `cc-mini workflow test`

Selects smallest useful verification.

Uses:

- changed files
- CodeGraph affected tests
- `.ai-dev/TESTING.md`

### `cc-mini workflow review`

Prepares fresh review packet.

Inputs:

- task
- context pack summary
- test result
- diff stat
- focused diff

### `cc-mini workflow log`

Writes local work log.

Writes:

- `.ai-dev/worklogs/task-xxx.md`

## First Implementation Target

Implement first:

`cc-mini workflow status`

Why:

- read-only
- low risk
- validates file boundary rules
- useful before every task
- does not require CodeGraph subprocess integration yet

## Non-Goals For First Version

Do not implement yet:

- automatic implementation
- automatic commit
- multi-agent execution
- full PRD generation
- full CodeGraph embedding
- background daemon management
- remote API calls

## Output Style

Commands should output:

- short status
- warnings
- next recommended action
- machine-readable option later, but not required first

## Risks

- command family becomes too large
- workflow files become a second product
- hidden mutation in commands that should be read-only
- local task artifacts accidentally staged
- CodeGraph unavailable causing poor UX

## Open Questions

- Should workflow commands be slash commands, CLI commands, or both?
- Should `.ai-dev` be configurable?
- Should CodeGraph be optional by default?
- Should workflow init create `AGENTS.md` automatically?
- Should status fail with nonzero exit code in CI?