# Workflow Configuration Defaults Review

Outcome of Task 047.  Reviews the safety and conservatism of default configuration values, with emphasis on workflow commands, permissions, and testing boundaries.

---

## Current Default Behaviour

### CLI Arguments (`src/core/main.py`)

| Flag | Default | Notes |
|------|---------|-------|
| `--auto-approve` | `False` | Explicit opt-in; help text labels it **"dangerous"** |
| `--mode` | `standard` | `wiki_strict` is opt-in |
| `--provider` | `anthropic` | Falls back to env / config file |
| `--max-tokens` | `32000` (anthropic) / provider fallback | High but bounded |
| `--effort` | `None` | Only used for OpenAI reasoning models |
| `--coordinator` | `False` | Background workers are opt-in |
| `--no-auto-dream` | `False` | Auto-dream is **enabled by default** |
| `--dream-interval` | `24.0` hours | Only relevant when auto-dream is on |
| `--dream-min-sessions` | `5` | Only relevant when auto-dream is on |

### AppConfig (`src/core/config.py`)

| Field | Default | Risk Level |
|-------|---------|------------|
| `provider` | `anthropic` | Low |
| `api_key` | `None` (loaded from env) | Low — never hardcoded |
| `base_url` | `None` | Low |
| `model` | Provider default | Low |
| `max_tokens` | Provider-specific fallback | Low |
| `effort` | `None` | Low |
| `buddy_model` | Provider default | Low |
| `memory_dir` | `~/.mini-claude/memory` | Low |
| `dream_interval_hours` | `24.0` | Low |
| `dream_min_sessions` | `5` | Low |
| `auto_dream` | `True` | **Medium** — background consolidation enabled by default |
| `config_paths` | `()` | Low |

### Sandbox (`src/core/sandbox/config.py`)

| Field | Default | Risk Level |
|-------|---------|------------|
| `enabled` | `False` | Low — sandbox is opt-in |
| `auto_allow_bash` | `False` | Low — even when enabled, bash still prompts |
| `allow_unsandboxed` | `False` | Low — fallback to unsandboxed is opt-in |
| `unshare_net` | `True` | Low — network isolation on by default if sandbox enabled |
| `filesystem.allow_write` | `["."]` | Medium — if sandbox enabled, write scope is cwd |

### Permissions (`src/core/permissions.py`)

| Behaviour | Default | Risk Level |
|-----------|---------|------------|
| Read-only tools | Auto-allowed | Low |
| Write tools (Edit, Write) | Prompt user | Low |
| Bash | Prompt user | Low |
| Plan mode | Restricted to read-only + plan file only | Low |
| `auto_approve` | `False` | Low — must be passed explicitly |

### Token Budget (`src/core/token_budget.py`)

| Threshold | Default | Purpose |
|-----------|---------|---------|
| `soft_limit` | 16 000 | Trigger dehydration |
| `compact_limit` | 20 000 | Trigger summary compaction |
| `checkpoint_limit` | 24 000 | Trigger snapshot truncation |
| `hard_stop_limit` | 26 000 | Absolute ceiling |
| `max_context` | 32 768 | Model context size |

These are conservative 32 K-oriented defaults with an 8 K output buffer.

---

## Safety Points

1. **Sandbox is disabled by default.**  A user must explicitly enable it via config or command.
2. **Auto-approve is off by default and labeled dangerous.**  The CLI help text explicitly warns about `--auto-approve`.
3. **Write and bash tools require user confirmation by default.**  The permission checker prompts with `y/n/always`.
4. **Plan mode restricts tool access.**  Only read-only tools and plan-file edits are allowed when plan mode is active.
5. **Workflow commands are read-only.**  `/workflow-status`, `/workflow-doctor`, `/workflow-test` do not mutate source files, run tests automatically, or commit changes.  `/workflow-init` creates scaffold files only and supports `--dry-run`.
6. **No automatic git commit.**  `/close` drafts a record; commit only happens after manual `/close confirm`.
7. **API keys are loaded from environment only.**  No hardcoded keys in source.
8. **Token budget has hard stop at 26 K.**  Prevents context overflow on 32 K models.
9. **Local model / MLX detection exists but is not a first-class CLI provider.**  The CLI only offers `anthropic` and `openai` as `--provider` choices.

---

## Risk Points

1. **Auto-dream is enabled by default.**  `auto_dream=True` means background memory consolidation can trigger automatically after 24 hours or 5 new sessions.  While this only writes to `~/.mini-claude/memory/`, it is background file I/O that the user may not expect.  Mitigation: `--no-auto-dream` is available.
2. **High default max_tokens (32 K).**  On Anthropic the default is 32 000 output tokens.  This is safe for API usage but could lead to unexpectedly long responses and higher costs if the user does not set a lower limit.  Mitigation: `--max-tokens` allows override.
3. **Sandbox `filesystem.allow_write` defaults to `["."]` when enabled.**  If a user turns on sandboxing without narrowing the write list, the sandbox still permits writes to the current working directory.  This is expected behaviour (the sandbox is for process isolation, not filesystem denial), but it is worth documenting.
4. **`--auto-approve` bypasses all confirmation gates.**  Once enabled, the permission checker returns `"allow"` for every tool.  This is by design but represents the single largest increase in blast radius.
5. **Local model provider is partially implemented.**  `config.py` has logic for `provider == "local"` and MLX model detection (lines 110–111), but `"local"` is not in the CLI `--provider` choices.  If a user sets it via env var or config file, the behaviour is untested and may bypass provider validation.
6. **Default config file paths are searched automatically.**  `~/.config/cc-mini/config.toml` and `.cc-mini.toml` in cwd are loaded without explicit `--config`.  A malicious `.cc-mini.toml` in a cloned repo could override provider or auto-approve settings.  Mitigation: env vars and CLI args override file values.

---

## Local Model Testing — How to Opt In

Local model support is **not a first-class CLI provider** in the current release.  The CLI `--provider` only accepts `anthropic` and `openai`.

To test local models, you must opt in via environment variable or config file:

```bash
# Not available via CLI flag
export CC_MINI_PROVIDER=local
export CC_MINI_MODEL=your-local-model
cc-mini
```

Or in `.cc-mini.toml`:

```toml
provider = "local"
model = "your-local-model"
```

**Note:** The `local` provider path is partially implemented in `config.py` (lines 110–111 force `max_tokens=32000` for local/MLX models), but full integration testing is not part of the standard test suite.  Local model tests should be run manually or in an isolated environment.

---

## What Should Not Enter Ordinary Tests

| Area | Why | Current Status |
|------|-----|----------------|
| Live API calls | Cost, latency, non-determinism | Mocked in tests |
| API key loading | Secrets must not appear in test output | Env-only; no tests for key values |
| Sandbox integration (bubblewrap/bwrap) | Requires OS-level dependencies; marked as `integration` | Excluded with `-k "not integration"` |
| Auto-dream timing | Time-dependent; flaky | No timing-dependent assertions found |
| Git state-dependent assertions | Repo state varies between runs | Tests use `tmp_path` and `monkeypatch` |
| Real filesystem writes outside tmp | Must not pollute workspace | Tests use `tmp_path` fixtures |
| Model provider resolution for `local` | Not a supported CLI provider | Should not be in standard pytest suite |

---

## Recommendations

1. **Keep sandbox disabled by default.**  Do not change `SandboxConfig.enabled` default.
2. **Keep `--auto-approve` opt-in and dangerous.**  The help text warning is sufficient.
3. **Consider disabling auto-dream by default** or adding a first-run prompt.  Background file writes to `~/.mini-claude/memory/` may surprise new users.
4. **Document the `.cc-mini.toml` precedence** in `README.md` or `docs/configuration.md`.  Users should know that a file in cwd can override global settings.
5. **Add a test** that verifies `local` provider is rejected by CLI argument parsing (if that is the intended boundary).
6. **Do not add OMLX / local model configuration** to the default config schema until local provider is a fully supported CLI choice.
7. **Keep workflow commands read-only.**  Any future command that mutates files or git state must require explicit confirmation.
8. **Do not change default max_tokens** without explicit user direction; 32 K is the product target.
