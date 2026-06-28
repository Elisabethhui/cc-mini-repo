# Configuration Reference

This document summarizes the runtime configuration for the context-bounded `cc-mini` branch.

## 1. Provider Selection

Supported provider values:

```text
anthropic
openai
```

For local OpenAI-compatible servers, use:

```text
provider = openai
```

Do not use `provider=local`.

## 2. Environment Variables

### Provider

```bash
export CC_MINI_PROVIDER=openai
```

or:

```bash
export CC_MINI_PROVIDER=anthropic
```

### Anthropic

```bash
export ANTHROPIC_API_KEY="..."
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
export CC_MINI_MODEL="claude-sonnet-4-6"
```

### OpenAI / OpenAI-Compatible

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
export CC_MINI_MODEL="gpt-4.1-mini"
```

For local runtimes:

```bash
export OPENAI_API_KEY="dummy"
export OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
export CC_MINI_MODEL="Qwen3.5-9B-MLX-4bit"
```

## 3. Context Runtime

### `CC_MINI_CONTEXT_WINDOW`

Total runtime context window.

Example:

```bash
export CC_MINI_CONTEXT_WINDOW=32768
```

### `CC_MINI_MAX_OUTPUT_TOKENS`

Reserved output budget for a model response.

Example:

```bash
export CC_MINI_MAX_OUTPUT_TOKENS=2048
```

### `CC_MINI_SAFETY_MARGIN_TOKENS`

Safety margin kept free to reduce overflow risk.

Example:

```bash
export CC_MINI_SAFETY_MARGIN_TOKENS=2048
```

### `CC_MINI_MAX_TOKENS`

Legacy-compatible output token setting.

Do not treat this as total context window.

Prefer:

```bash
CC_MINI_MAX_OUTPUT_TOKENS
```

## 4. Runtime Flags

### `CC_MINI_AUTO_COMPACT`

Controls automatic compaction behavior.

Examples:

```bash
export CC_MINI_AUTO_COMPACT=true
export CC_MINI_AUTO_COMPACT=false
```

### `CC_MINI_AUTO_APPROVE`

Controls automatic permission approval where supported.

Examples:

```bash
export CC_MINI_AUTO_APPROVE=true
export CC_MINI_AUTO_APPROVE=false
```

Use with care. For real coding work, explicit approval is safer.

## 5. TOML Configuration

Example local model config:

```toml
provider = "openai"

[openai]
base_url = "http://127.0.0.1:1234/v1"
api_key = "dummy"
model = "Qwen3.5-9B-MLX-4bit"

[context]
window = 32768
max_output_tokens = 2048
safety_margin_tokens = 2048
```

Example Anthropic config:

```toml
provider = "anthropic"

[anthropic]
api_key = "..."
base_url = "https://api.anthropic.com"
model = "claude-sonnet-4-6"

[context]
window = 200000
max_output_tokens = 4096
safety_margin_tokens = 4096
```

Example OpenAI config:

```toml
provider = "openai"

[openai]
api_key = "..."
base_url = "https://api.openai.com/v1"
model = "gpt-4.1-mini"

[context]
window = 128000
max_output_tokens = 4096
safety_margin_tokens = 4096
```

## 6. RuntimeProfile Fields

The runtime profile tracks:

```text
provider
model
base_url
context_window
max_output_tokens
safety_margin_tokens
runtime_kind
supports_streaming
supports_tool_calling
```

Runtime kind examples:

```text
cloud_openai
cloud_anthropic
local_openai_compatible
```

## 7. BudgetReport Fields

The budget report tracks:

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

Budget states:

```text
ok
warning
preserve
split
hard_stop
```

## 8. State Meaning

### ok

Continue normally.

### warning

Continue, but consider reducing context.

### preserve

Preserve structured state and compact/repack before continuing.

### split

Task is too large. Split into smaller tasks.

### hard_stop

Do not call the model. Human intervention or task reduction is required.

## 9. Local Artifact Paths

Do not commit:

```text
.ai-dev/runtime/
.ai-dev/context-packs/
.ai-dev/worklogs/
.ai-dev/tmp/
.codegraph/
.codebase-memory/
```

Commit durable design/docs/templates only when intended:

```text
.ai-dev/design/
.ai-dev/templates/
.ai-dev/skills/
docs/
README.md
```

## 10. Verification Commands

Local development:

```bash
pytest tests/ -v -k "not integration"
```

Compile core runtime files:

```bash
python -m py_compile \
  src/core/config.py \
  src/core/runtime_profile.py \
  src/core/context_budget.py \
  src/core/runtime_state.py \
  src/core/preservation.py \
  src/core/plan_graph.py \
  src/core/plan_preservation.py \
  src/core/code_retrieval.py \
  src/core/context_pack.py \
  src/core/batch_runner.py \
  src/core/agent_protocol.py \
  src/core/engine.py \
  src/core/commands.py
```

Before commit:

```bash
git status --short
git diff --check
```

