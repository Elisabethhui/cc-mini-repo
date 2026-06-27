# Workflow Commands

cc-mini includes a set of read-only workflow helpers that keep coding tasks small, bounded, and recoverable.  These commands are available in both `standard` and `wiki_strict` modes.

> **Important:** Workflow commands are **read-only diagnostics and recommendations**.  They do not modify source files, run tests automatically, or commit changes.

---

## Available Commands

| Command | What it does |
|---------|-------------|
| `/workflow-status` | Show workflow readiness: required files, ignored paths, git state, CodeGraph availability |
| `/workflow-init` | Create missing workflow scaffold files (`AGENTS.md`, `.ai-dev/` tree) |
| `/workflow-init --dry-run` | Preview what `/workflow-init` would create without writing files |
| `/workflow-doctor` | Run read-only diagnostics: required files, local artifacts in git, markdown code fences, CodeGraph availability |
| `/workflow-test` | Recommend tests based on changed files (uses CodeIntel when available, falls back to heuristics) |
| `/model-health` | Check model endpoint health and show local model profile (read-only, 5s timeout) |

### Planned (not yet implemented)

| Command | What it will do |
|---------|----------------|
| `/codeintel-status` | Show CodeIntel provider status and fallback state |
| `/codeintel-query <keyword>` | Query code relationships via CodeGraph or `rg` fallback |

---

## Quick Start

After cloning a repo, run the workflow readiness check:

```
> /workflow-status

Workflow status: NEEDS ATTENTION

Required Files:
- [OK] AGENTS.md (file present)
- [MISSING] .ai-dev/README.md (file missing)
...
```

If files are missing, scaffold them:

```
> /workflow-init

Created: AGENTS.md
Created: .ai-dev/README.md
Created: .ai-dev/WORKFLOW.md
...
```

Run diagnostics before starting work:

```
> /workflow-doctor

Context-Bounded Workflow Doctor

Required Files:
- [OK] AGENTS.md (file present)
...
Decision: ok
```

After making changes, ask for test recommendations:

```
> /workflow-test

Test Selection Result
Changed files: src/core/commands.py
Recommendations:
- pytest tests/test_commands.py -v
```

---

## N-Context Runtime Configuration

The runtime supports configurable `context_window=N` via environment variables or TOML:

| Environment Variable | TOML Key | Description |
|---------------------|----------|-------------|
| `CC_MINI_CONTEXT_WINDOW` | `context.window` | Model context window size |
| `CC_MINI_MAX_OUTPUT_TOKENS` | `context.max_output_tokens` | Output token budget (alias: `CC_MINI_MAX_TOKENS`) |
| `CC_MINI_SAFETY_MARGIN_TOKENS` | `context.safety_margin_tokens` | Reserved safety margin |
| `CC_MINI_AUTO_COMPACT` | `context.auto_compact` | Auto-compact when approaching limits |
| `CC_MINI_AUTO_APPROVE` | — | Auto-approve all tool permissions |

> **Note:** `CC_MINI_MAX_TOKENS` is preserved for backward compatibility and always means **output tokens**, not the full context window.

Example `.cc-mini.toml`:

```toml
[context]
window = 32768
max_output_tokens = 2048
safety_margin_tokens = 2048
auto_compact = true
```

---

## 32K Small-Context Workflow

For 32 K context models, the recommended bounded workflow is:

1. **Macro-plan** — Write the goal in the REPL or a plan file.
2. **Slice** — One small task at a time.
3. **Surface search** — Use `/workflow-test` or `Glob`/`Grep` to find anchors.
4. **Inspect** — Read at most 5 files; prefer snippets and signatures over full files.
5. **Implement** — Edit at most 3 files per task.
6. **Verify** — Run the smallest useful test set (e.g., `pytest tests/test_foo.py -v`).
7. **Review** — Use `/review` or `/close` to record decisions.
8. **Log** — Write a work log to `.ai-dev/worklogs/` for future sessions.

Stop if the impact radius becomes broad.  Larger models may widen context, but testing, review, rollback, and file boundaries remain mandatory.

---

## Local Artifacts

The following directories are workflow local state and **must not be committed**:

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`
- `.codegraph/`
- `.codebase-memory/`

They are already listed in `.gitignore`.  `/workflow-doctor` will warn you if any of them appear in `git status`.

---

## CodeGraph and Fallback

CodeGraph is optional.  When it is installed and initialized, workflow commands use it for compact code queries.  When it is unavailable, they fall back to `rg` (ripgrep) or simple file reading.

```bash
# Optional: initialize CodeGraph for faster code exploration
codegraph init
codegraph status
```

If CodeGraph is not present, `cc-mini` continues to work with `rg` and manual file reads.

---

## Future Aliases

External CLI commands such as `cc-mini workflow status` may be added later as aliases for the REPL slash commands, but they are not the current v1 target.  The primary interface is the interactive REPL.
