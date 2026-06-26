# Local Models (MLX / OMLX / OpenAI-Compatible)

cc-mini supports locally-hosted OpenAI-compatible endpoints.  This includes:

- **MLX** models served via `mlx_lm.server`, LM Studio, or similar
- **OMLX** and other Apple-Silicon-optimized stacks
- Any custom server that exposes `/v1/chat/completions`

> **Design choice:** Local models use the existing `openai` provider.  You only need to point `--base-url` (or `OPENAI_BASE_URL`) at your local server.

---

## Quick Start

### 1. Start a local OpenAI-compatible server

**Example with `mlx_lm.server`:**

```bash
pip install mlx-lm
mlx_lm.server --model mlx-community/Mistral-7B-Instruct-v0.2-MLX
```

This typically listens on `http://localhost:8080`.

**Example with LM Studio:**

1. Load a model in LM Studio.
2. Start the local server (usually `http://localhost:1234`).

### 2. Run cc-mini against it

```bash
cc-mini \
  --provider openai \
  --base-url http://localhost:8080/v1 \
  --model mlx-community/Mistral-7B-Instruct-v0.2-MLX \
  --max-tokens 32000
```

Or via environment variables:

```bash
export CC_MINI_PROVIDER=openai
export OPENAI_BASE_URL=http://localhost:8080/v1
export CC_MINI_MODEL=mlx-community/Mistral-7B-Instruct-v0.2-MLX
export CC_MINI_MAX_TOKENS=32000
cc-mini
```

Or in `.cc-mini.toml`:

```toml
provider = "openai"
model = "mlx-community/Mistral-7B-Instruct-v0.2-MLX"
max_tokens = 32000

[openai]
base_url = "http://localhost:8080/v1"
# api_key is optional for most local servers
```

---

## max_tokens vs. Context Window

| Concept | What it means | Default for local 32K models |
|---------|---------------|------------------------------|
| **Context window** | Total input + output tokens the model can process | 32,768 |
| **max_tokens** | How many tokens the model is *allowed to output* in a single response | 32,000 |

`--max-tokens` controls the **output budget**, not the full context window.  When you set `--max-tokens 32000`, you are telling the model it may generate up to 32K tokens in one go.  The remaining ~768 tokens are reserved for the system prompt and conversation history overhead.

**Recommendation for 32K local models:**

```bash
--max-tokens 32000
```

This is safe because cc-mini automatically detects local endpoints and applies the 32K default.  You only need to override it if you want a smaller output limit.

---

## Health Check

Inside the REPL, run:

```
> /model-health
```

This performs three lightweight checks against your endpoint:

1. `GET /health` — optional endpoint (many local servers expose this)
2. `GET /v1/models` — lists available models and verifies yours is present
3. `POST /v1/chat/completions` — sends a minimal 1-token request to confirm chat works

All checks have a 5-second timeout.  If a check fails, you get a warning or error message, but the REPL does not crash.  This is useful for diagnosing:

- Wrong `--base-url`
- Model not loaded in the server
- Server not started
- Network/firewall issues

---

## Local Model Profile

When cc-mini detects a local endpoint, it builds a `LocalModelProfile`:

| Field | Typical value |
|-------|---------------|
| `kind` | `mlx` or `openai-compatible` |
| `base_url` | Your local server URL |
| `context_window` | 32,768 |
| `recommended_max_output_tokens` | 32,000 |
| `supports_streaming` | `true` |
| `supports_tool_calling` | `auto` (detect at runtime) |

The profile is shown automatically by `/model-health` and is stored in `AppConfig.local_profile`.

---

## Known Limitations

- **Tool calling:** Not all local servers support function calling.  cc-mini sends tools anyway; if the server rejects them, you will see an error in the chat-completions health check.
- **Streaming:** Most local servers support streaming, but some older MLX builds do not.  If streaming fails, cc-mini falls back to non-streaming mode automatically.
- **Context compression:** The token-budget manager uses the same 32K thresholds for local models as for cloud models.  If your local model has a smaller context window (e.g., 8K), lower `--max-tokens` accordingly.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `/model-health` shows "Connection refused" | Server not running | Start your local server first |
| `/model-health` shows 404 on `/v1/models` | Wrong base_url path | Try `http://localhost:8080` (without `/v1`) |
| `/model-health` shows model not in list | Model name mismatch | Check the exact model ID in your server UI |
| Responses are truncated | `max_tokens` too low | Set `--max-tokens 32000` |
| Out-of-memory on Mac | Model too large for RAM | Use a smaller quant (e.g., Q4 instead of Q8) |

---

## Safety Notes

- No API keys are ever hardcoded in cc-mini source code.
- Local model endpoints do not send data to the cloud.
- Health checks use dummy prompts (e.g., `"hi"`) so they never leak real conversation content.
