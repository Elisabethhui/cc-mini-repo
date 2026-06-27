# Local 32K Runtime Guide

This guide explains how to run cc-mini with a **32K context window** local model (e.g. OMLX, MLX, or any OpenAI-compatible local server).

## Important Distinction

- **`CC_MINI_CONTEXT_WINDOW`** = the model's **total** context window (e.g. `32768`)
- **`CC_MINI_MAX_OUTPUT_TOKENS`** = how many tokens the model may **output** in a single response (e.g. `2048`)

Do not confuse them. Setting `--max-tokens 32000` on a 32K model leaves almost no room for the prompt.

## Recommended Settings for 32K Models

```bash
export CC_MINI_PROVIDER=openai
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=none
export CC_MINI_MODEL=Qwen3.5-9B-MLX-4bit
export CC_MINI_CONTEXT_WINDOW=32768
export CC_MINI_MAX_OUTPUT_TOKENS=2048
export CC_MINI_SAFETY_MARGIN_TOKENS=1024
```

This leaves:
- **~29,696 tokens** for prompt + context pack + tool schemas
- **2,048 tokens** for the model's response
- **1,024 tokens** safety margin

## Bounded Workflow for Small Context

1. **Macro-plan** — Write the goal in the REPL or a plan file.
2. **Slice** — One small task at a time.
3. **Surface search** — Use `/workflow-test` or `Glob`/`Grep` to find anchors.
4. **Inspect** — Read at most 5 files; prefer snippets and signatures over full files.
5. **Implement** — Edit at most 3 files per task.
6. **Verify** — Run the smallest useful test set.
7. **Review** — Use `/review` or `/close` to record decisions.
8. **Log** — Write a work log to `.ai-dev/worklogs/` for future sessions.

Stop if the impact radius becomes broad. Larger models may widen context, but testing, review, rollback, and file boundaries remain mandatory.

## TOML Config Example

Create `.cc-mini.toml` in your project root:

```toml
provider = "openai"
model = "Qwen3.5-9B-MLX-4bit"
base_url = "http://localhost:8000/v1"

[context]
window = 32768
max_output_tokens = 2048
safety_margin_tokens = 1024
auto_compact = true
```

## Health Check

Inside the REPL, run:

```
> /model-health
```

This verifies endpoint reachability and shows the local model profile.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "Context budget exceeded" | `--max-tokens` set to full window | Set `CC_MINI_MAX_OUTPUT_TOKENS` to ~2K |
| Long pauses between turns | Model is slow; reduce context pack size | Lower `context.window` or use `/compact` |
| Tool results truncated | `single_tool_result_max_chars` too low | Increase in TOML or read files in chunks |

## See Also

- `docs/n-context-runtime.md` — General N-context runtime design
- `docs/workflow-run.md` — Workflow commands reference
- `docs/local-models.md` — Full local model setup guide
