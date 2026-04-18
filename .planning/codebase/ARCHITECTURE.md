# cc-mini Architecture

## System Overview

cc-mini is an AI coding assistant harness implementing core Claude Code features: an interactive REPL, an agentic tool loop, a permission system, session persistence, and a **Wiki-Strict Mode** designed for local 32K token contexts. It has two runtime modes:

- `standard` (default): Full toolset, multi-agent coordination, standard file read/edit.
- `wiki_strict`: Structured workflow with AST-based code reading, strict patch verification, automated lifecycle management, and token-budget protection.

The architecture is layered: CLI/REPL at the top, the Engine as the central streaming loop, Tools as the action layer, and subsystems (Wiki, Knowledge, Sandbox, Buddy, Memory) providing orthogonal services.

---

## Layer Diagram

```
+-------------------------------------------------------------+
|  CLI / REPL  (src/core/main.py)                             |
|  - argparse, prompt_toolkit bordered prompt, slash commands |
|  - streaming markdown renderer, spinner manager             |
|  - image attachment parsing (@path), terminal mode (!)      |
+-------------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------------+
|  Engine  (src/core/engine.py)                               |
|  - streaming API loop (LLM -> text / tool_use)              |
|  - retry logic, abort/cancel, token budget pre-flight       |
|  - tool execution: sequential write, concurrent read-only   |
|  - checkpoint on OOM, dehydration, compact integration      |
+-------------------------------------------------------------+
                           |
           +---------------+---------------+
           |                               |
           v                               v
+----------------------------+  +---------------------------+
|  LLM Client (src/core/llm.py) |  |  Tool System (src/core/tools/) |
|  - Anthropic + OpenAI       |  |  - base.py: Tool / ToolResult   |
|  - streaming normalization  |  |  - read: FileRead, ASTRead      |
|  - content block adapters   |  |  - write: FileEdit, FileEdit_S  |
|                             |  |  - search: Glob, Grep           |
|                             |  |  - exec: Bash (sandboxed)       |
|                             |  |  - coord: Agent, SendMessage    |
|                             |  |  - plan: EnterPlanMode, Exit    |
|                             |  |  - interact: AskUserQuestion    |
+----------------------------+  +---------------------------+
           |                               |
           v                               v
+----------------------------+  +---------------------------+
|  Config (src/core/config.py)  |  |  Permissions (src/core/permissions.py) |
|  - CLI args > env > TOML    |  |  - read-only auto-approve     |
|  - provider/model aliases   |  |  - plan mode restrictions     |
|  - RunMode enum (standard/  |  |  - sandbox auto-allow         |
|    wiki_strict)             |  |  - interactive y/n/a prompt   |
+----------------------------+  +---------------------------+

+-------------------------------------------------------------+
|  Subsystems (orthogonal services)                           |
|  - Wiki (src/core/wiki/): taskpack, target_identity,        |
|    post_edit_guard, archive, reconcile, maintenance, lint   |
|  - Knowledge (src/core/knowledge/): ingester, watcher,      |
|    dehydrator                                               |
|  - Sandbox (src/core/sandbox/): manager, wrapper, checker   |
|  - Buddy (src/core/buddy/): companion, animator, observer,  |
|    mood, poke_game                                          |
|  - Memory (src/core/memory.py): daily logs, dream, index    |
|  - Session (src/core/session.py): JSONL persistence         |
|  - Compact (src/core/compact.py): context compression       |
|  - Skills (src/core/skills.py + skills_bundled.py):         |
|    SKILL.md discovery and execution                         |
+-------------------------------------------------------------+
```

---

## Data Flow: User Input to Output

```
User Input
    |
    v
[main.py]  REPL loop
    - parse_command() -> slash command or free text
    - _parse_input() -> extract @image attachments
    |
    v
[Engine.submit()]  (engine.py)
    - append user message to conversation history
    - pre-flight token budget check (TokenBudgetManager)
        - if WARNING -> dehydrate old tool_results
        - if COMPACT -> run CompactService
        - if CHECKPOINT/HARD_STOP -> write checkpoint, stop
    |
    v
[LLMClient.stream_messages()]  (llm.py)
    - Anthropic: messages.stream() -> text_stream
    - OpenAI: chat.completions.create(stream=True) -> chunk iter
    - normalized to common content blocks: text, tool_use, tool_result
    |
    v
[Engine loop]  process streamed response
    - text chunks -> yield ("text", chunk) to REPL
    - tool_use blocks -> collect, batch by read-only vs write
    |
    v
[PermissionChecker.check()]  (permissions.py)
    - read-only -> auto-allow
    - write -> prompt user (y/n/a) or auto-approve
    - plan mode -> restrict to read-only + plan file writes
    |
    v
[Tool.execute()]  (tools/*.py)
    - read-only tools: execute in ThreadPoolExecutor (parallel)
    - write tools: execute sequentially
    - BashTool: optionally wrap with bwrap sandbox
    |
    v
[Engine]  append tool_results as user message
    - post-tool token budget check
    - loop back to LLM call (multi-turn tool loop)
    |
    v
[main.py run_query()]  render output
    - _StreamingMarkdown: incremental Rich Markdown rendering
    - _SpinnerManager: contextual spinners (Thinking, Running X...)
    - tool call / result indicators with checkmarks
```

---

## Component Boundaries and Interactions

### 1. Engine (src/core/engine.py) — Central Orchestrator

**Responsibilities:**
- Manage conversation message history (`self._messages`)
- Stream API calls with retry/backoff (`_MAX_RETRIES = 3`)
- Dispatch tool calls, batching concurrent read-only operations
- Token budget pre-flight and post-flight protection
- Checkpoint writing on context overflow
- Track written artifacts for checkpoint reporting

**Key interactions:**
- Uses `LLMClient` for all API communication
- Uses `PermissionChecker` before executing write tools
- Uses `TokenBudgetManager` + `CheckpointManager` for OOM protection
- Uses `CompactService` for automatic context compression
- Uses `SessionStore` for message persistence
- Uses `CostTracker` for usage tracking

**Public API:**
```python
class Engine:
    def submit(self, user_input: str | list) -> Iterator[tuple]
    def abort(self) -> None
    def cancel_turn(self) -> None
    def set_messages(self, messages: list[dict]) -> None
    def set_model(self, model: str) -> None
```

### 2. LLM Client (src/core/llm.py) — Provider Abstraction

**Responsibilities:**
- Abstract Anthropic and OpenAI SDKs behind a unified interface
- Normalize content blocks between SDK formats
- Handle streaming (`stream_messages`) and non-streaming (`create_message`)
- Classify errors: authentication, retryable, API errors

**Key classes:**
- `LLMClient`: main entry point, provider-aware
- `_AnthropicStream` / `_OpenAIStream`: streaming context managers
- `LLMMessage` / `LLMUsage`: normalized dataclasses

**Normalization:**
- Anthropic blocks: `text`, `tool_use`, `tool_result`, `image`
- OpenAI blocks: converted to same schema via `_normalize_openai_message`

### 3. Tool System (src/core/tools/)

All tools inherit from `Tool` base class (`base.py`) and implement:
- `to_api_schema()` -> JSON schema for LLM
- `execute(**kwargs)` -> `ToolResult(content, is_error)`
- `is_read_only()` -> bool (affects permission and concurrency)

**Read-only tools** (auto-approved, parallel execution):
| Tool | File | Purpose |
|------|------|---------|
| Read | `file_read.py` | Read file with line numbers, offset/limit |
| ASTRead | `ast_read.py` | Read by symbol/span/anchor (Python AST) |
| Glob | `glob_tool.py` | File pattern matching |
| Grep | `grep_tool.py` | Content search with regex |
| AskUserQuestion | `ask_user.py` | Interactive multi-choice questions |

**Write tools** (require permission, sequential execution):
| Tool | File | Purpose |
|------|------|---------|
| Edit | `file_edit.py` | Exact string replacement |
| Edit (strict) | `file_edit_strict.py` | Wiki-strict mode with backup, preview, rollback, human fallback on 2 failures |
| Write | `file_write.py` | Create/overwrite files |
| Bash | `bash.py` | Shell execution with optional sandbox |

**Coordination tools:**
| Tool | File | Purpose |
|------|------|---------|
| Agent | `agent.py` | Spawn background worker |
| SendMessage | `agent.py` | Continue existing worker |
| TaskStop | `agent.py` | Stop running worker |
| EnterPlanMode | `plan_tools.py` | Switch to plan mode |
| ExitPlanMode | `plan_tools.py` | Exit plan mode |

### 4. Permission System (src/core/permissions.py)

`PermissionChecker` implements three-tier approval:
1. **Auto-allow**: read-only tools, `--auto-approve` flag, sandboxed bash in auto-allow mode
2. **Always-allow**: user pressed 'a' for a specific tool name (stored in `_always_allow`)
3. **Interactive prompt**: single-character y/n/a response, with ESC cancellation support

Plan mode adds additional restrictions: only read tools + plan file writes allowed.

### 5. Sandbox (src/core/sandbox/)

Bubblewrap-based sandbox subsystem:
- `config.py`: `SandboxConfig` dataclass, TOML load/save
- `manager.py`: `SandboxManager` — unified interface, mode switching
- `wrapper.py`: `build_bwrap_args()` — generates bwrap command lines
- `checker.py`: `check_dependencies()` — Linux/bwrap/userns validation
- `command_matcher.py`: Excluded command pattern matching (prefix/exact/wildcard)

Sandbox modes: `auto-allow` (bash auto-approved), `regular` (still prompts), `disabled`.

### 6. Wiki-Strict Subsystem (src/core/wiki/)

Activated when `CC_MINI_MODE=wiki_strict`:

| Module | File | Purpose |
|--------|------|---------|
| TaskPack | `taskpack.py` | Structured task planning with GoalStack, EditSpec, entity status |
| Target Identity | `target_identity.py` | Disambiguate file/symbol targets for `/prime` |
| Post-Edit Guard | `post_edit_guard.py` | Patch impact analysis, completion state machine |
| Archive | `archive.py` | Automatic archiving with age thresholds |
| Reconcile | `reconcile.py` | Detect and recover stale wiki entities |
| Maintenance | `maintenance.py` | Lifecycle management of snapshots/taskpacks |
| Lint | `lint.py` | Health checks for wiki structure |
| Query Archive | `query_archive.py` | Query archived items |

**Flow-State Machine** (`flow_state.py`):
```
PLAN -> LOCATE -> IMPLEMENT -> VERIFY
```
- PLAN: Read wiki index for architecture overview
- LOCATE: Use ASTRead for precise symbol extraction
- IMPLEMENT: Use strict Edit with exact matching
- VERIFY: Run tests/lint, loop back to LOCATE on failure

### 7. Knowledge System (src/core/knowledge/)

- `ingester.py`: `WikiIngester` — scan workspace, parse Python AST, generate entity markdown files with frontmatter status tracking
- `watcher.py`: `start_wiki_watcher()` — filesystem watcher for incremental re-ingestion
- `dehydrator.py`: `MinimalDehydrator` — message dehydration for context compression

Entity status lifecycle: `raw_ast` -> `partially_digested` -> `digested` | `stale`

### 8. Companion / Buddy (src/core/buddy/)

Deterministic companion pet system:
- `companion.py`: `get_companion()` — deterministic generation from user ID hash
- `animator.py`: `CompanionAnimator` — 500ms tick loop, idle/excited animations, speech bubbles
- `observer.py`: `fire_companion_observer()` — background thread generating reactions via LLM
- `mood.py`: Rule-based mood engine (6 dimensions, event classification, time decay)
- `storage.py`: JSON persistence for companion data
- `sprites.py`: ASCII sprite rendering
- `poke_game/`: Idle Adventure roguelike mini-game

### 9. Memory System (src/core/memory.py)

KAIROS cross-session memory:
- Daily log appending (`append_to_daily_log`)
- `<memory>` tag extraction from assistant responses
- Dream consolidation (`build_dream_prompt`): 4-phase process to consolidate logs into topic files
- `MEMORY.md` index maintenance
- Lock-based auto-dream gating

### 10. Session Persistence (src/core/session.py)

JSONL-based conversation storage:
- `SessionStore.append_message()` — append to `{session_id}.jsonl`
- `SessionStore.list_sessions()` — fast listing via `.meta.json` files
- `SessionStore.load_session()` — restore metadata + messages
- Storage: `~/.mini-claude/sessions/{sanitized_cwd}/`

### 11. Context Compression (src/core/compact.py)

`CompactService` summarizes old messages to free token budget:
- Splits messages into (history, recent) preserving tool_use/tool_result pairs
- Calls LLM with structured summarization prompt
- Replaces history with `[summary]` + `[ack]` messages
- Auto-triggered when `should_compact()` returns True

### 12. Skills System (src/core/skills.py + skills_bundled.py)

SKILL.md-based reusable prompts:
- Discovery: `~/.cc-mini/skills/` (user) + `{cwd}/.cc-mini/skills/` (project)
- Frontmatter parsing (minimal YAML, no PyYAML dependency)
- Execution modes: `inline` (inject into conversation) or `fork` (isolated turn)
- Bundled skills registered in code via `register_skill()`

### 13. Coordinator / Workers (src/core/coordinator.py + worker_manager.py)

Multi-agent coordination mode (`--coordinator` or `CC_MINI_COORDINATOR=1`):
- `WorkerManager`: spawns background threads running isolated `Engine` instances
- `AgentTool` / `SendMessageTool` / `TaskStopTool`: worker lifecycle tools
- Notifications delivered as `<task-notification>` XML user messages
- Coordinator prompt: research -> synthesis -> implementation -> verification workflow

---

## Entry Points and Initialization

### Main Entry Point

**File:** `src/core/main.py` (1393 lines)

```python
def main() -> None:
    # 1. Parse CLI arguments
    parser = argparse.ArgumentParser(prog="cc-mini")
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("-p", "--print", action="store_true")
    parser.add_argument("--auto-approve", action="store_true")
    parser.add_argument("--provider", choices=("anthropic", "openai"))
    parser.add_argument("--model")
    parser.add_argument("--mode", choices=["standard", "wiki_strict"], default="standard")
    parser.add_argument("--coordinator", action="store_true")
    # ... more args
    args = parser.parse_args()

    # 2. Load configuration (CLI > env > TOML)
    app_config = load_app_config(args)

    # 3. Initialize sandbox
    sandbox_config = load_sandbox_config(app_config.config_paths)
    sandbox_mgr = SandboxManager(config=sandbox_config)

    # 4. Memory setup
    memory_dir = app_config.memory_dir
    ensure_memory_dir(memory_dir)

    # 5. Skill registration
    register_bundled_skills()
    discover_skills(cwd)

    # 6. Build tools (mode-dependent)
    base_tools = _build_base_tools()  # standard vs wiki_strict
    tools = _build_tools_for_mode(coordinator_enabled)

    # 7. Build system prompt
    system_prompt = _build_system_prompt_for_mode(coordinator_enabled)

    # 8. Create engine
    engine = Engine(
        tools=tools,
        system_prompt=system_prompt,
        permission_checker=permissions,
        provider=app_config.provider,
        model=app_config.model,
        # ...
    )

    # 9. Wiki-strict mode: ingest workspace, start watcher
    if run_mode == RunMode.WIKI_STRICT:
        ingester = WikiIngester(cwd)
        ingester.ingest_all()
        watcher_thread = start_wiki_watcher(cwd, ingester)

    # 10. REPL loop
    while True:
        user_input = _bordered_prompt(...)
        # handle slash commands, terminal mode, companion, etc.
        run_query(engine, user_input, print_mode=False, permissions=permissions)
```

### Non-Interactive Mode

```bash
# One-shot prompt
cc-mini "what tests exist?"

# Piped input
cat file.txt | cc-mini --print
```

In non-interactive mode, `run_query()` runs once and exits. Background workers may still be running.

### Session Resume

```bash
cc-mini --resume 1        # by index
cc-mini --resume abc123   # by session ID prefix
```

Loads messages from `~/.mini-claude/sessions/{cwd}/{session_id}.jsonl`.

---

## Key Design Patterns

1. **Streaming Yield Pattern**: Engine.submit() yields typed tuples (`("text", ...)`, `("tool_call", ...)`, `("tool_result", ...)`) consumed by the REPL renderer
2. **Tool Base Class**: Abstract base with `to_api_schema()`, `execute()`, `is_read_only()`
3. **Normalized Content Blocks**: LLM client normalizes Anthropic/OpenAI formats to common dict schema
4. **Mode-Conditional Tool Construction**: `main.py` builds different tool sets for standard vs wiki_strict vs coordinator modes
5. **Checkpoint + Resume**: Token budget manager triggers checkpoint writes; `/resume-from-checkpoint` skill restores state
6. **Background Worker Threads**: `WorkerManager` runs isolated Engine instances in daemon threads
7. **Deterministic Companion Generation**: Companion bones regenerated from hash(userId) — no mutable state in bones
8. **Append-Only Memory**: Daily logs never deleted; dream consolidation produces topic files
