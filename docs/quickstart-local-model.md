# Quickstart: Local Model Runtime

This guide explains how to install and run `cc-mini` with a local OpenAI-compatible model server, such as an OMLX / MLX / Qwen runtime.

The current branch is designed for **N-context local coding**. That means the context window is configurable and should not be assumed to be 32K, even though 32K is the main low-cost target.

## 1. Install

Clone the repository and install it in development mode:

```bash
git clone https://github.com/Elisabethhui/cc-mini-repo.git
cd cc-mini-repo
git checkout feature/context-bounded-dev-bootstrap

python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

Run the non-integration test suite:

```bash
pytest tests/ -v -k "not integration"
```

## 2. Start A Local Model Server

Start your local OpenAI-compatible server first.

Example endpoint shape:

```text
http://127.0.0.1:1234/v1
```

The server should expose OpenAI-compatible chat/completions behavior. The API key can usually be a placeholder value if your local server does not enforce authentication.

## 3. Configure cc-mini For OMLX / Qwen

Use `provider=openai` for local OpenAI-compatible runtimes.

Do not add or use `provider=local`.

```bash
export CC_MINI_PROVIDER=openai
export OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
export OPENAI_API_KEY="dummy"
export CC_MINI_MODEL="Qwen3.5-9B-MLX-4bit"
```

Set the runtime context budget:

```bash
export CC_MINI_CONTEXT_WINDOW=32768
export CC_MINI_MAX_OUTPUT_TOKENS=2048
export CC_MINI_SAFETY_MARGIN_TOKENS=2048
```

Important:

- `CC_MINI_CONTEXT_WINDOW` is the total context window.
- `CC_MINI_MAX_OUTPUT_TOKENS` is reserved output budget.
- `CC_MINI_MAX_TOKENS` is legacy-compatible and should be treated as output tokens, not total context.

## 4. Optional Local Config File

You can also use a local TOML config if your current CLI invocation supports a config path.

Example:

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

Keep local configs out of git if they contain private endpoints or keys.

## 5. Start cc-mini

If the package exposes a console script:

```bash
cc-mini
```

Fallback:

```bash
PYTHONPATH=src python -m core.main
```

## 6. Check Runtime Health

Inside the REPL, run:

```text
/model-health
```

This verifies whether the configured model endpoint is reachable and whether the minimal model request works.

Then run:

```text
/workflow-status
/workflow-doctor
```

These commands verify the local context-bounded workflow setup.

## 7. Recommended First Workflow

For an existing codebase:

```text
/workflow-init
/workflow-doctor
/model-health
/codeintel-status
/workflow-pack "small task goal"
/workflow-run --dry-run "small task goal"
```

Only run supervised execution after the dry run output looks correct:

```text
/workflow-run "small task goal"
```

For an empty repository:

```text
/workflow-init
/plan-init "project goal"
/plan-status
/workflow-pack "first implementation task"
/workflow-run --dry-run "first implementation task"
```

## 8. CodeGraph Optional Setup

The workflow is CodeGraph-first when CodeGraph is available, but it should degrade gracefully to `rg` and internal heuristics when CodeGraph is missing.

If you have CodeGraph installed, sync after code changes:

```bash
codegraph sync || true
codegraph status || true
```

Do not commit CodeGraph local data:

```text
.codegraph/
.codebase-memory/
```

## 9. What Not To Commit

These are runtime or local artifacts and should not be committed:

```text
.ai-dev/runtime/
.ai-dev/context-packs/
.ai-dev/worklogs/
.ai-dev/tmp/
.codegraph/
.codebase-memory/
.pytest_cache/
__pycache__/
*.pyc
```

Before committing:

```bash
git status --short
git diff --check
```

## 10. Common Problems

### The model name is unexpectedly Qwen in tests

Your shell environment may be leaking runtime variables into tests.

Check:

```bash
env | grep -E 'CC_MINI|OPENAI|ANTHROPIC'
```

Unset local runtime variables before running full unit tests if needed.

### The model server is reachable but tool calls fail

Some local OpenAI-compatible servers do not fully support tool calling.

Use smaller tasks, run `/workflow-pack` first, and prefer dry runs before supervised execution.

### Context still overflows

Lower output budget and increase safety margin:

```bash
export CC_MINI_MAX_OUTPUT_TOKENS=1024
export CC_MINI_SAFETY_MARGIN_TOKENS=3072
```

Then use:

```text
/workflow-pack "task goal"
/workflow-run --dry-run "task goal"
```

