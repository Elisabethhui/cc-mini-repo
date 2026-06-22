# CodeGraph Setup

## Purpose

This file documents how this repository uses CodeGraph for low-token code exploration.

CodeGraph is a local code intelligence index. It should help locate files, symbols, call relationships, impact radius, and affected tests before reading large source files.

## File Boundary

Never commit CodeGraph local indexes.

Ignored paths:

- `.codegraph/`
- `.codebase-memory/`

Do not paste raw CodeGraph dumps into committed files.

If a query result is useful for one task, summarize it into a local ignored context pack:

- `.ai-dev/context-packs/task-xxx.md`

## Install

Recommended local usage:

```bash
npx @colbymchenry/codegraph
```

If already installed:

```bash
codegraph version
```

## Initialize This Project

Run from the repository root:

```bash
codegraph init
codegraph status
```

`codegraph init` creates `.codegraph/` locally.

Confirm `.codegraph/` is ignored:

```bash
git check-ignore .codegraph/example.db
```

## Daily Use

Before exploring code:

```bash
codegraph status
```

If the project changed and you need current results:

```bash
codegraph sync
codegraph status
```

## Query Order

Prefer small queries first.

```bash
codegraph files
codegraph query "<keyword>"
codegraph callers "<symbol>"
codegraph callees "<symbol>"
codegraph impact "<symbol>"
git diff --name-only | codegraph affected --stdin --quiet
```

Use broad exploration only when smaller queries fail:

```bash
codegraph explore "<question>"
```

## Cold Start Flow

If the user request has no clear file or symbol:

1. Extract keywords from the task.
2. Use `rg` for exact error strings, command names, config keys, and route names.
3. Use `codegraph query` for likely symbols.
4. Pick 1-3 anchors.
5. Use callers/callees/impact on the best anchor.

Example:

```bash
rg -n "workflow status|status command|workflow"
codegraph query "workflow"
codegraph query "status"
```

## Map Sync Barrier

After implementation and before test selection, sync the map.

```bash
git diff --name-only
codegraph sync
codegraph status
```

Then select affected tests:

```bash
git diff --name-only | codegraph affected --stdin --quiet
```

Do not rely on CodeGraph affected-test output when freshness is stale, unavailable, or unknown.

## Freshness States

Classify CodeGraph freshness as:

- `fresh`: sync succeeded and status is healthy
- `probably-fresh`: watcher is active and changed symbols appear in queries
- `stale`: changed files are not reflected
- `unavailable`: CodeGraph is not installed or not initialized
- `unknown`: cannot determine freshness

Only use CodeGraph for affected test selection when freshness is `fresh` or `probably-fresh`.

## Fallback When CodeGraph Is Unavailable

Use exact search:

```bash
rg -n "<keyword>"
rg -n "<function_or_class_name>"
find . -maxdepth 3 -type f | sort
```

Fallback rules:

- prefer exact strings
- avoid reading large files
- read snippets around matches
- record that CodeGraph was unavailable
- do not pretend impact analysis is complete

## Common Queries For This Repository

CLI and commands:

```bash
codegraph query "main"
codegraph query "commands"
codegraph query "slash"
codegraph query "REPL"
```

Engine and tool loop:

```bash
codegraph query "Engine"
codegraph query "submit"
codegraph query "Tool"
codegraph query "execute"
```

Token and context:

```bash
codegraph query "TokenBudget"
codegraph query "token_budget"
codegraph query "compact"
codegraph query "dehydration"
```

Skills:

```bash
codegraph query "skills"
codegraph query "Skill"
codegraph query "skills_bundled"
```

Wiki-strict:

```bash
codegraph query "wiki"
codegraph query "taskpack"
codegraph query "reconcile"
codegraph query "post_edit_guard"
```

Sandbox and permissions:

```bash
codegraph query "Permission"
codegraph query "sandbox"
codegraph query "Bash"
```

Tests:

```bash
codegraph query "test_engine"
codegraph query "test_commands"
codegraph query "test_wiki"
```

## Using With Context Packs

A CodeGraph result should be compressed before use in a small-context model.

Do not paste full raw output unless it is tiny.

Summarize into:

- relevant files
- relevant symbols
- callers/callees
- impact radius
- affected tests
- source snippets still needed

Use:

- `.ai-dev/skills/code-intel/SKILL.md`
- `.ai-dev/skills/context-pack/SKILL.md`
- `.ai-dev/skills/context-tier-policy/SKILL.md`

## Using With Test Gate

After code changes:

```bash
codegraph sync
git diff --name-only | codegraph affected --stdin --quiet
```

If affected tests are found, run targeted tests first.

If no affected tests are found but changed files are important, fall back to nearby tests or a smoke test.

## Troubleshooting

If CodeGraph says the project is not initialized:

```bash
codegraph init
```

If results seem stale:

```bash
codegraph sync
codegraph status
```

If sync is blocked:

```bash
codegraph unlock
codegraph sync
```

If the tool is unavailable:

```bash
codegraph version
```

If still unavailable, use `rg` fallback and record this in the context pack or test gate result.

## Commit Rules

Before committing, check:

```bash
git status --short
```

Never commit:

- `.codegraph/`
- `.codebase-memory/`
- raw query dumps
- local context packs
- local work logs
- task scratch files