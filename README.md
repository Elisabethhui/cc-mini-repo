<div align="center">

# cc-mini

**Ultra-light Harness scaffolding for AI agents**

**Agentic** &nbsp;·&nbsp; **Built to Extend** &nbsp;·&nbsp; **From Claude Code**
<br>

The entire core is `~1000 lines of Python`

</div>

---

### **NEW: Buddy — AI Companion with Custom Sprites**

> Your coding companion lives in the terminal. Type `/buddy` to hatch it. Supports custom ASCII species — bring your own Pikachu!

![Custom Pikachu buddy companion](assets/buddy-pikachu.jpg)

[Full Buddy docs &rarr;](docs/buddy.md)

---

## Features

### Core

- **Interactive REPL** with streaming output, command history, slash command autocomplete
- **Agentic tool loop** — Claude calls tools autonomously until the task is complete
- **6 built-in tools**: `Read`, `Edit`, `Write`, `Glob`, `Grep`, `Bash`
- **Permission system** — reads auto-approved, writes/bash ask for confirmation
- **Session persistence** — auto-save conversations, `/resume` to continue later
- **Context compression** — auto-compact when approaching token limits
- **Anthropic + OpenAI compatible** — works with any compatible API endpoint

### Advanced (from unreleased Claude Code features)

| Feature | Description | Docs |
|---------|-------------|------|
| **Coordinator Mode** | Background workers for parallel research and implementation | [docs &rarr;](docs/coordinator.md) |
| **Buddy** | Tamagotchi AI pet with personality, stats, mood, and speech bubbles | [docs &rarr;](docs/buddy.md) |
| **KAIROS Memory** | Cross-session memory with auto-consolidation | [docs &rarr;](docs/memory.md) |
| **Skills** | One-command workflows: `/review`, `/commit`, `/test`, `/simplify` | [docs &rarr;](docs/skills.md) |
| **Sandbox** | Bubblewrap isolation for bash commands | [docs &rarr;](docs/sandbox.md) |

---

## Quick Start

### Requirements

- Python 3.10+ (3.11+ recommended)
- An API key for [Anthropic](https://console.anthropic.com/) or any OpenAI-compatible provider

unset ANTHROPIC_AUTH_TOKEN
export ANTHROPIC_MODEL=kimi-for-coding
export ENABLE_TOOL_SEARCH=false
export ANTHROPIC_BASE_URL=https://api.kimi.com/coding/
export ANTHROPIC_API_KEY=sk-kimi-CcVKVk6DrY8fIw8e3sNzda6I22M9koqO46E6AwgfKj13u6EYq54ly55fndg6Cr4z  # 这里填在会 员页面生成的 API Key
claude



export ENABLE_TOOL_SEARCH=false
export ANTHROPIC_BASE_URL=https://api.kimi.com/coding/
export ANTHROPIC_API_KEY=sk-kimi-CcVKVk6DrY8fIw8e3sNzda6I22M9koqO46E6AwgfKj13u6EYq54ly55fndg6Cr4z  # 这里填在会员页面生成的 API Key

claude
### Install

```bash
# One-line install (recommended)
curl -fsSL https://raw.githubusercontent.com/e10nMa2k/cc-mini/main/install.sh | bash

# Or manual
git clone https://github.com/e10nMa2k/cc-mini.git
cd cc-mini
pip install -e ".[dev]"
```
export CC_MINI_MODEL="Qwen3.5-9B-MLX-4bit"                    
export CC_MINI_PROVIDER=openai
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=w2hqq0809
export CC_MINI_MAX_TOKENS=32000
export CC_MINI_AUTO_APPROVE=1
export CC_MINI_AUTO_COMPACT=1


export CC_MINI_MODE=wiki_strict
claudekimi-key=
sk-kimi-CcVKVk6DrY8fIw8e3sNzda6I22M9koqO46E6AwgfKj13u6EYq54ly55fndg6Cr4z

export ENABLE_TOOL_SEARCH=false
unset ANTHROPIC_AUTH_TOKEN
export ANTHROPIC_BASE_URL=https://api.kimi.com/coding/
export ANTHROPIC_API_KEY=sk-kimi-CcVKVk6DrY8fIw8e3sNzda6I22M9koqO46E6AwgfKj13u6EYq54ly55fndg6Cr4z  
claude
unset ANTHROPIC_AUTH_TOKEN
export ENABLE_TOOL_SEARCH=false
export ANTHROPIC_BASE_URL=https://api.kimi.com/coding/
export ANTHROPIC_API_KEY=sk-kimi-xxxx
claude

"env": {
    "ANTHROPIC_AUTH_TOKEN": "w2hqq0809",
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:8000",
    "ANTHROPIC_MODEL": "Qwen3.5-9B-MLX-4bit",
    "NO_PROXY": "127.0.0.1,localhost",
    "no_proxy": "127.0.0.1,localhost"
  },  这个里面我可以配置token吗？

# ----------------------------
# Claude Code 模型切换
# ----------------------------
# 1. 本地 oMLX
alias claude-local="
  unset ANTHROPIC_API_KEY
  export ANTHROPIC_BASE_URL=http://127.0.0.1:8000
  export ANTHROPIC_AUTH_TOKEN=w2hqq0809
  export ANTHROPIC_MODEL=Qwen3.5-9B-MLX-4bit
  export ENABLE_TOOL_SEARCH=false
  claude
"

# 2. 云端 Kimi
alias claude-kimi="
  unset ANTHROPIC_AUTH_TOKEN
  export ANTHROPIC_BASE_URL=https://api.kimi.com/coding/
  export ANTHROPIC_API_KEY=sk-kimi-CcVKVk6DrY8fIw8e3sNzda6I22M9koqO46E6AwgfKj13u6EYq54ly55fndg6Cr4z
  export ENABLE_TOOL_SEARCH=false
  claude
"
### Set API Key

```bash
# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Or OpenAI-compatible
export CC_MINI_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://your-gateway.example.com/v1
```

### Run

```bash
cc-mini                              # Interactive REPL
cc-mini "what tests exist?"          # One-shot prompt
cc-mini -p "summarize this codebase" # Print and exit
cc-mini --auto-approve               # Skip permission prompts
cc-mini --resume 1                   # Resume previous session
cc-mini --coordinator                # Coordinator mode
```

### First Session Demo

```
cc-mini

> list all python files in this project
↳ Glob(**/*.py) ✓
Found 12 Python files...

> read engine.py and explain the tool loop
↳ Read(src/core/engine.py) ✓
The submit() method implements an agentic loop...

> /buddy
Hatching your companion...
✨ SHINY LEGENDARY DUCK
Glitch Quack hatched! ★★★★★

> /buddy mood
Glitch Quack's mood:
  Happy      ████████████████░░░░  65 (high)
  Bored      ██████████░░░░░░░░░░  50 (neutral)

> /review
Running skill: /review…
↳ Bash(git diff) … ✓ done
## Code Review: no issues found ✓
```

[Full configuration docs &rarr;](docs/configuration.md)

---

## Tools

| Tool | Description | Permission |
|------|-------------|------------|
| `Read` | Read file contents | auto-approved |
| `Glob` | Find files by pattern | auto-approved |
| `Grep` | Search file contents | auto-approved |
| `Edit` | Edit file (string replacement) | requires confirmation |
| `Write` | Write/create file | requires confirmation |
| `Bash` | Run shell command | requires confirmation |

Coordinator mode adds: `Agent` (spawn worker), `SendMessage` (continue worker), `TaskStop` (stop worker). See [coordinator docs](docs/coordinator.md).

---

## Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/compact` | Compress conversation context |
| `/resume` | Resume a past session |
| `/history` | List saved sessions |
| `/clear` | Clear conversation, start new session |
| `/skills` | List all available skills |
| `/buddy` | Companion pet — hatch, pet, stats, mood |
| `/buddy help` | Show all buddy commands and gameplay guide |
| `/review` | Code review (skill) |
| `/commit` | Git commit (skill) |
| `/test` | Run tests (skill) |
| `/simplify` | Review and fix code (skill) |

Type `/` to see autocomplete suggestions.

---

## Project Structure

```
src/core/
├── main.py           # CLI entry point + REPL
├── engine.py         # Streaming API loop + tool execution
├── llm.py            # LLM client (Anthropic + OpenAI)
├── config.py         # Configuration (CLI, env, TOML)
├── context.py        # System prompt builder
├── commands.py       # Slash command system
├── session.py        # Session persistence
├── compact.py        # Context compression
├── coordinator.py    # Coordinator mode
├── worker_manager.py # Background worker lifecycle
├── skills.py         # Skill loader and registry
├── skills_bundled.py # Built-in skills (simplify, review, commit, test)
├── memory.py         # KAIROS memory system
├── permissions.py    # Permission checker
├── cost_tracker.py   # Token usage tracking
├── _keylistener.py   # Esc/Ctrl+C detection
├── sandbox/          # Bubblewrap sandbox subsystem
├── tools/            # Tool implementations
└── buddy/            # AI companion pet system
```

## Running Tests

```bash
pytest tests/ -v
pytest tests/ -v -k "not integration"  # skip bwrap tests
```

---

## Documentation

| Topic | Link |
|-------|------|
| Configuration (API keys, TOML, CLI flags) | [docs/configuration.md](docs/configuration.md) |
| Buddy (AI companion pet) | [docs/buddy.md](docs/buddy.md) |
| Coordinator Mode (background workers) | [docs/coordinator.md](docs/coordinator.md) |
| KAIROS Memory System | [docs/memory.md](docs/memory.md) |
| Skills (custom workflows) | [docs/skills.md](docs/skills.md) |
| Sandbox (bash isolation) | [docs/sandbox.md](docs/sandbox.md) |
