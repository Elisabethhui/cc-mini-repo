<div align="center">

# cc-mini

**AI Coding Harness with Wiki-Strict Mode for Local 32K Scenarios**

**Agentic** · **Wiki-Strict Mode** · **Built to Extend** · **From Claude Code**
这是一个给 cc-mini 增加 wiki_strict 模式的增强框架，核心目标是让本地 32K 小模型也能进行中长程、可恢复、可维护的代码任务执行。系统通过 memory-bank 和 .cc-mini/wiki 把规则、计划、知识、任务、快照和归档都持久化到文件系统里，再通过 current-task.md 驱动 Claude Code 做受控执行。项目现在已经具备从 scan/digest、TaskPack/plan，到安全 patch、retry、Re-anchor、reconcile、archive、lint、maintenance 的完整链路。

</div>

---

## Overview

cc-mini is an AI coding assistant harness that implements core Claude Code features: interactive REPL, agentic tool loop, permission system, and session persistence. It includes advanced features like **Wiki-Strict Mode** (for local 32K token contexts), Coordinator mode (background workers), Buddy (AI companion), and a complete wiki-based knowledge system.

**Key Capability: Wiki-Strict Mode** — A structured workflow mode designed for local 32K token limits, featuring AST-based code reading, strict patch verification, and automated lifecycle management.

一、项目说明（Project Overview）
项目名称

CC-MINI Wiki-Strict 增强框架

项目目标

在不破坏原有 standard 模式的前提下，为 cc-mini 增加一套更适合本地 32K 小模型的 wiki_strict 工作模式。

解决的问题

这个项目主要解决以下问题：

上下文太短
小模型容易 OOM
长任务容易失忆
需要把知识持久化到文件，而不是只靠上下文
代码修改容易失控
模型容易整文件重写
修改前没有先定位目标
debug 时容易重复失败、无限重试
任务边界容易漂移
模型计划时会中途跑偏
会把后续阶段问题提前拉进来
需要 Goal Stack / Re-anchor / Deferred Issue 约束
知识维护能力不足
只会生成 Wiki，不会维护
stale 页面、旧 snapshot、旧 taskpack 无法持续回收
需要 reconcile / archive / query-archive / lint / maintenance
二、系统核心理念
1. 双模式
standard：原有模式
wiki_strict：增强模式，适合本地小模型
2. 文件系统是长期记忆

项目不是靠“聊天历史”长期维持状态，而是靠：

memory-bank/
.cc-mini/wiki/
3. 任务必须先压缩再执行

不是直接“改代码”，而是：

先有 current-task.md
再执行
再验证
再更新文档
4. 先计划，后定位，后修改，后验证

整个系统的一个基本原则就是：

不允许跳过定位直接 patch
不允许跳过验证直接标完成
三、目录说明
1. memory-bank/

这是项目的长期规则层和任务控制层。

主要文件包括：

game-design-document.md
tech-stack.md
implementation-plan.md
reset-note-v2.md
system-design-v2.md
progress.md
architecture.md
findings.md
decisions.md
current-task.md
schema/*.md
phases/*.md
它的作用
定义规则
记录进度
记录架构
记录决定
定义当前任务
2. .cc-mini/wiki/

这是 Wiki 工作区。

常见内容包括：

index.md
log.md
entities/**
taskpacks/**
reports/**
archive/**
它的作用
结构测绘
语义消化
任务预热
运行时日志
快照与归档
长期维护
四、五个阶段分别做什么
Phase 1：模式接入与结构骨架

你已经做的核心包括：

runtime 规则固化
mode 支持
Goal Stack 占位
基础骨架接入
Phase 2：scan / digest / snapshot

核心包括：

/scan
/digest
/digest --changed
entity 状态升级
dehydration / Runtime Snapshot
最小 drift stop
Phase 3：TaskPack / EditSpec / prime / plan

核心包括：

TaskPack
EditSpec
Goal Stack 正式对象
/prime
/plan
Deferred Issue / Micro-Fork
Phase 4：安全 patch 与局部 debug

核心包括：

ASTRead
strict patch
verify / retry
traceback cleaning
Re-anchor
ask_user fallback
Phase 5：维护、回收、归档

核心包括：

reconcile
archive
query-archive
lint / health check
stale recovery
维护引擎
五、你现在怎么实际使用这个项目
使用前提

统一使用以下 Python 解释器：

/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python

统一工作目录：

/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo

需要导入 src/core/... 时统一加：

PYTHONPATH=src

六、推荐的日常工作流
Step 1：准备 current-task

每次只维护一个：

memory-bank/current-task.md

里面写清楚：

当前目标
Allowed Read
Allowed Modify
Out of Scope
Required Tests
Pass Criteria
If Tests Fail
On Success
Step 2：把 current-task 交给 Claude Code

Claude 只执行当前任务，不进入下一阶段。

Step 3：Claude 跑测试

必须先过测试，才能更新文档。

Step 4：Claude 更新文档

成功后更新：

progress.md
architecture.md
findings.md
decisions.md
Step 5：停止

成功后停止，不自动进入下一个阶段。

---

## Features

### Core

- **Interactive REPL** with streaming output, command history, slash command autocomplete
- **Agentic tool loop** — Claude calls tools autonomously until the task is complete
- **11 built-in tools**: `Read`, `Edit`, `Write`, `Glob`, `Grep`, `Bash`, `AskUser`, `Agent`, `SendMessage`, `TaskStop`, `ASTRead`
- **Permission system** — reads auto-approved, writes/bash ask for confirmation
- **Session persistence** — auto-save conversations, `/resume` to continue later
- **Context compression** — auto-compact when approaching token limits
- **Anthropic + OpenAI compatible** — works with any compatible API endpoint

### Wiki-Strict Mode (v2.0)

Structured workflow mode for local 32K contexts:

| Phase | Component | Purpose |
|-------|-----------|---------|
| Phase 1 | Runtime + Goal Stack | Fixed interpreter, mode validation |
| Phase 2 | Scan / Digest / Snapshot | AST-based entity generation, drift detection |
| Phase 3 | TaskPack / EditSpec | Structured task planning |
| Phase 4 | ASTRead / Strict Patch / Re-anchor | Precise modification with retry logic |
| Phase 5 | Reconcile / Archive / Maintenance | Lifecycle management, stale recovery |

**Wiki-Strict Tools:**
- `ASTRead` — Read code by symbol, span, anchor, or outline
- `ReconcileEngine` — Detect and recover stale entities
- `ArchiveEngine` — Automatic archiving with age thresholds
- `WikiLinter` — Health checks for wiki structure
- `MaintenanceEngine` — Lifecycle management

### Advanced Features

| Feature | Description | Docs |
|---------|-------------|------|
| **Coordinator Mode** | Background workers for parallel research | [docs/coordinator.md](docs/coordinator.md) |
| **Buddy** | AI companion pet with personality and mood | [docs/buddy.md](docs/buddy.md) |
| **KAIROS Memory** | Cross-session memory with auto-consolidation | [docs/memory.md](docs/memory.md) |
| **Skills** | One-command workflows: `/review`, `/commit`, `/test` | [docs/skills.md](docs/skills.md) |
| **Sandbox** | Bubblewrap isolation for bash commands | [docs/sandbox.md](docs/sandbox.md) |
| **Wiki System** | Structured knowledge management | [docs/wiki/](docs/wiki/) |

---

## Quick Start

### Requirements

- Python 3.11+
- An API key for [Anthropic](https://console.anthropic.com/) or any OpenAI-compatible provider

### Install

```bash
git clone https://github.com/e10nMa2k/cc-mini.git
cd cc-mini
pip install -e ".[dev]"
```

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
cc-mini --mode wiki_strict           # Wiki-strict mode
```

### Wiki-Strict Mode Example

```bash
export CC_MINI_MODE=wiki_strict
cc-mini

> scan src/core/wiki
> digest --changed
> prime
> plan
```

---

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `ANTHROPIC_BASE_URL` | Custom Anthropic gateway (optional) |
| `OPENAI_API_KEY` | OpenAI-compatible API key |
| `OPENAI_BASE_URL` | Custom OpenAI gateway URL |
| `CC_MINI_PROVIDER` | `anthropic` or `openai` |
| `CC_MINI_MODEL` | Model name (e.g., `claude-sonnet-4-6`) |
| `CC_MINI_MAX_TOKENS` | Max output tokens |
| `CC_MINI_EFFORT` | Reasoning effort: `low`, `medium`, `high` |
| `CC_MINI_MODE` | `standard` or `wiki_strict` |
| `CC_MINI_BUDDY_MODEL` | Model for companion reactions |
| `CC_MINI_BUDDY_SEED` | Seed for specific companion |
| `CC_MINI_COORDINATOR` | Set to `1` to enable coordinator mode |

### CLI Flags

```bash
cc-mini \
  --provider anthropic \
  --model claude-sonnet-4-6 \
  --max-tokens 32000 \
  --effort medium \
  --mode wiki_strict \
  --auto-approve \
  --coordinator
```

### TOML Config Files

Loaded in order (later overrides earlier):

1. `~/.config/cc-mini/config.toml`
2. `.cc-mini.toml` in current working directory

Example:

```toml
provider = "anthropic"

[anthropic]
api_key = "sk-ant-..."
model = "claude-sonnet-4-6"
max_tokens = 32000

[openai]
api_key = "sk-..."
base_url = "https://your-gateway.example.com/v1"
```

---

## Tools

### Standard Tools

| Tool | Description | Permission |
|------|-------------|------------|
| `Read` | Read file contents | auto-approved |
| `Glob` | Find files by pattern | auto-approved |
| `Grep` | Search file contents | auto-approved |
| `Edit` | Edit file (string replacement) | requires confirmation |
| `Write` | Write/create file | requires confirmation |
| `Bash` | Run shell command | requires confirmation |
| `AskUser` | Ask user a question | interactive |

### Wiki-Strict Tools

| Tool | Description |
|------|-------------|
| `ASTRead` | Read code by symbol, span, anchor, or outline |

### Coordinator Tools

| Tool | Description |
|------|-------------|
| `Agent` | Spawn a background worker |
| `SendMessage` | Continue an existing worker |
| `TaskStop` | Stop a running worker |

---

## Slash Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/compact` | Compress conversation context |
| `/resume` | Resume a past session |
| `/history` | List saved sessions |
| `/clear` | Clear conversation, start new session |
| `/skills` | List all available skills |

### Buddy Commands

| Command | Description |
|---------|-------------|
| `/buddy` | Hatch or show companion |
| `/buddy pet` | Pet your companion |
| `/buddy mood` | Check companion's mood |
| `/buddy mute` / `/buddy unmute` | Toggle reactions |

### Wiki-Strict Commands

| Command | Description |
|---------|-------------|
| `/scan` | Scan files for wiki entities |
| `/digest` | Digest files into wiki format |
| `/digest --changed` | Digest only changed files |
| `/prime` | Generate TaskPack from digest |
| `/plan` | Create structured patch plan |

### Skills

| Command | Description |
|---------|-------------|
| `/review` | Code review (read-only) |
| `/simplify` | Review and fix code |
| `/commit` | Git commit with generated message |
| `/test` | Run tests and analyze failures |

Type `/` to see autocomplete suggestions.

---

## Project Structure

```
src/core/
├── main.py              # CLI entry point + REPL
├── engine.py            # Streaming API loop + tool execution
├── llm.py               # LLM client (Anthropic + OpenAI)
├── config.py            # Configuration (CLI, env, TOML)
├── context.py           # System prompt builder
├── commands.py          # Slash command system
├── session.py           # Session persistence
├── compact.py           # Context compression
├── checkpoint.py        # Checkpoint saving
├── token_budget.py      # Token budget management
├── dehydration.py       # Message dehydration
├── flow_state.py        # Flow state machine (PLAN/LOCATE/IMPLEMENT/VERIFY)
├── coordinator.py       # Coordinator mode
├── worker_manager.py    # Background worker lifecycle
├── skills.py            # Skill loader and registry
├── skills_bundled.py    # Built-in skills
├── memory.py            # KAIROS memory system
├── permissions.py       # Permission checker
├── cost_tracker.py      # Token usage tracking
├── sandbox/             # Bubblewrap sandbox subsystem
│   ├── manager.py
│   ├── config.py
│   └── wrapper.py
├── tools/               # Tool implementations
│   ├── base.py
│   ├── file_read.py
│   ├── file_edit.py
│   ├── file_edit_strict.py
│   ├── file_write.py
│   ├── bash.py
│   ├── glob_tool.py
│   ├── grep_tool.py
│   ├── ask_user.py
│   ├── agent.py
│   ├── ast_read.py      # AST-based code reading
│   ├── error_handler.py
│   ├── reanchor.py
│   └── plan_tools.py
├── buddy/               # AI companion system
│   ├── companion.py
│   ├── mood.py
│   ├── animator.py
│   └── ...
├── knowledge/           # Wiki knowledge system
│   ├── ingester.py
│   ├── watcher.py
│   └── dehydrator.py
└── wiki/                # Wiki maintenance system
    ├── taskpack.py
    ├── reconcile.py
    ├── archive.py
    ├── query_archive.py
    ├── lint.py
    └── maintenance.py
```

---

## Wiki System

cc-mini includes a complete wiki-based knowledge system for structured project documentation.

### Wiki Directory Structure

```
.cc-mini/wiki/
├── index.md                 # Wiki index
├── entities/                # Code entities (auto-generated)
│   └── *.py.md
├── taskpacks/               # Task packs
│   └── *.json
├── snapshots/               # Runtime snapshots
│   └── *.json
├── reports/                 # Reports
│   ├── deferred-issues/
│   └── micro-forks/
└── archive/                 # Archived items
    ├── snapshots/
    ├── taskpacks/
    └── manifest.json
```

### Wiki Schema

Each wiki page (except index.md and log.md) must have YAML frontmatter:

```yaml
---
title: Page Title
source: raw file path, URL, or "session"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
status: current|draft|stale
source_hash: a1b2c3d4e5f67890
compiled_at: 2026-04-07T12:00:00+00:00
---
```

See [docs/wiki/SCHEMA.md](docs/wiki/SCHEMA.md) for details.

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Skip integration tests (sandbox/bwrap)
pytest tests/ -v -k "not integration"

# Run specific test file
pytest tests/test_engine.py -v
```

---

## Wiki Maintenance Scripts

```bash
# Check LLM-wiki version
python3 scripts/version_check.py

# Validate wiki structure
python3 scripts/wiki_check.py

# Check raw file manifests
python3 scripts/raw_manifest_check.py

# Find untracked raw files
python3 scripts/untracked_raw_check.py

# Find stale wiki pages
python3 scripts/stale_report.py

# Check source provenance
python3 scripts/provenance_check.py
```

---

## Documentation

| Topic | Link |
|-------|------|
| Configuration (API keys, TOML, CLI) | [docs/configuration.md](docs/configuration.md) |
| Buddy (AI companion) | [docs/buddy.md](docs/buddy.md) |
| Coordinator Mode | [docs/coordinator.md](docs/coordinator.md) |
| KAIROS Memory | [docs/memory.md](docs/memory.md) |
| Skills | [docs/skills.md](docs/skills.md) |
| Sandbox | [docs/sandbox.md](docs/sandbox.md) |
| Wiki System | [docs/wiki/](docs/wiki/) |
| Wiki Schema | [docs/wiki/SCHEMA.md](docs/wiki/SCHEMA.md) |

---

## Development

### Local Development Setup

```bash
git clone <repo>
cd cc-mini
pip install -e ".[dev]"
```

### Running in Wiki-Strict Mode

```bash
export CC_MINI_MODE=wiki_strict
export PYTHONPATH=src
python -m core.main
```

---

## License

MIT


## Phase 6-A Status

### 当前进度
- Module 1：`conditional pass`
- Module 2：`✅ pass`
- Module 3：`✅ pass`
- Final Validation：`pending`

### 最近一次验证
- 时间：2026-04-15
- 模块：Module 3
- 结论：验证通过，7/7 测试通过

### Deferred Validation
- 已安装运行时（`.venv/bin/cc-mini`）下的 Module 1 smoke test
- 安装态 `/prime llm.py`
- 安装态 `/prime src/core/llm.py`
- 安装态不唯一 target 的 disambiguation 行为