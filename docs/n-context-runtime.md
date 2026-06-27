# N-Context Runtime

The N-Context Runtime is cc-mini's bounded-context execution engine. It makes every model call safe, recoverable, and configurable under a user-defined `context_window=N`.

## Core Principle

Instead of treating the model as having unlimited memory, the runtime enforces:

```text
fixed_overhead + current_state + packed_context + messages + tool_results + reserved_output + safety_margin <= context_window
```

Where `context_window=N` is **configurable** and not hard-coded to 32K or 200K.

## Key Invariants

1. `context_window` is configurable via `CC_MINI_CONTEXT_WINDOW` or TOML.
2. `CC_MINI_MAX_TOKENS` and `CC_MINI_MAX_OUTPUT_TOKENS` mean **output budget only**, not the full context window.
3. Input budget and output budget are tracked separately.
4. Hard stop is the last fallback, not the main mechanism.
5. Important state is externalized to `.ai-dev/runtime/`.
6. Large raw artifacts are saved by path and summarized.
7. Unit tests use fakes and mocks—no real LLM or CodeGraph required.

## Budget States

Before each model call the runtime produces a budget report with one of these states:

| State | Action |
|-------|--------|
| `ok` | Continue normally. |
| `warning` | Light cleanup: drop low-value history, truncate old tool outputs. |
| `preserve` | Freeze, extract structured state, write artifacts, repack, continue. |
| `split` | Task is too large; split into smaller executable batches. |
| `hard_stop` | Do not call the model. Save checkpoint and wait for human decision. |

## Preservation Pipeline

When the budget enters `preserve`, the pipeline:

1. **Freeze** current runtime state.
2. **Extract** goal, phase, decisions, open questions, risks, next action.
3. **Persist** to `.ai-dev/runtime/<run-id>/`.
4. **Materialize** artifacts (large content externalized to files).
5. **Repack** a lean context pack from the preserved summary.
6. **Continue or ask** depending on remaining budget.

## Two Retrieval Modes

| Mode | When | Primary Graph | Fallback |
|------|------|---------------|----------|
| **PlanGraph-first** | Empty repository, no code yet | PlanGraph (tasks, decisions, risks) | None needed |
| **CodeGraph-first** | Code exists | CodeGraph (symbols, files, callers) | `rg` (ripgrep) |

After scaffold exists, both graphs work together:
- **PlanGraph** explains *why* and *what*.
- **CodeGraph** explains *where* and *how*.
- **Runtime State** explains *what happened so far*.

## Configuration

### Environment Variables

| Variable | Meaning |
|----------|---------|
| `CC_MINI_CONTEXT_WINDOW` | Model context window size (e.g. `32768`, `200000`) |
| `CC_MINI_MAX_OUTPUT_TOKENS` | Output token budget per response |
| `CC_MINI_MAX_TOKENS` | Alias for `CC_MINI_MAX_OUTPUT_TOKENS` (output only!) |
| `CC_MINI_SAFETY_MARGIN_TOKENS` | Reserved safety margin |
| `CC_MINI_AUTO_COMPACT` | Auto-compact when approaching limits |

### TOML Example

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
```

## Local OMLX / MLX Models

Local models use the existing OpenAI-compatible provider path:

```bash
export CC_MINI_PROVIDER=openai
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=none
export CC_MINI_CONTEXT_WINDOW=32768
export CC_MINI_MAX_OUTPUT_TOKENS=2048
```

No special `provider=local` is required.

## Local Artifacts (Must Stay Ignored)

- `.ai-dev/runtime/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`
- `.codegraph/`
- `.codebase-memory/`

These directories are already in `.gitignore`.

## Commands

| Command | Purpose |
|---------|---------|
| `/workflow-pack <goal>` | Generate a bounded context pack |
| `/workflow-run --dry-run <goal>` | Preview the execution plan |
| `/workflow-run <goal>` | Run supervised execution |
| `/workflow-resume <run-id>` | Resume from saved runtime state |

See `docs/workflow-run.md` for detailed usage.
