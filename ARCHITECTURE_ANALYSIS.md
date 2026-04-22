# cc-mini 技术架构分析与 32K 支持评估

> 分析日期：2026-04-18
> 基于 commit：cfe00bc (codebase map)

---

## 一、技术架构总览

### 1.1 系统分层

```
用户输入
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: CLI / REPL (src/core/main.py ~1,400 lines)            │
│  - argparse 解析                                                  │
│  - prompt_toolkit REPL 循环                                       │
│  - 流式 Markdown 渲染 + Spinner                                  │
│  - slash command 分发                                             │
│  - auto-dream / companion / wiki watcher 生命周期                 │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Engine (src/core/engine.py ~600 lines)                │
│  - 流式 API 调用循环 (Anthropic/OpenAI)                          │
│  - 工具调用解析与执行                                             │
│  - Token 预算管理 (pre-flight + post-flight)                     │
│  - 消息脱水 (dehydration)                                        │
│  - 上下文压缩 (compact)                                          │
│  - 断点保存 (checkpoint)                                         │
│  - 重试与错误分类                                                 │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Subsystems                                              │
│  ├─ LLM Client (src/core/llm.py) — 供应商抽象                     │
│  ├─ Tools (src/core/tools/) — 14 个工具实现                       │
│  ├─ Permissions (src/core/permissions.py) — 读写权限确认           │
│  ├─ Session (src/core/session.py) — JSONL 持久化                 │
│  ├─ Memory/KAIROS (src/core/memory.py) — 跨会话记忆              │
│  ├─ Compact (src/core/compact.py) — 上下文压缩                    │
│  ├─ Sandbox (src/core/sandbox/) — bubblewrap 隔离                │
│  ├─ Skills (src/core/skills.py) — 技能注册与加载                 │
│  ├─ Wiki-Strict (src/core/wiki/) — 结构化工作流                   │
│  ├─ Knowledge (src/core/knowledge/) — 实体摄入与监控              │
│  ├─ Buddy (src/core/buddy/) — AI 陪伴系统                        │
│  └─ Coordinator (src/core/coordinator.py) — 后台工作线程          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流

```
用户输入 → main.py REPL
            │
            ▼
      engine.submit(user_input)
            │
            ├─ [Pre-flight] Token 估算 → BudgetDecision
            │       ├─ 脱水 (dehydration)
            │       ├─ 压缩 (compact)
            │       └─ 熔断 (checkpoint + stop)
            │
            ▼
      LLM API 流式调用
            │
            ▼
      接收 assistant 回复
            │
            ├─ 文本输出到用户
            ├─ 工具调用解析
            │       ├─ 读工具并行执行 (ThreadPoolExecutor)
            │       └─ 写工具串行确认
            │
            ├─ [Post-flight] usage 检查 → 二次脱水/断点
            │
            ▼
      循环直到无工具调用
```

### 1.3 关键设计模式

| 模式 | 应用位置 | 说明 |
|------|---------|------|
| **Streaming Yields** | `engine.py` | Generator 产出 `(type, data)` 元组给 REPL 渲染 |
| **Normalized Blocks** | `engine.py` | 统一 Anthropic/OpenAI 的 content block 格式 |
| **Tool ABC** | `tools/base.py` | 所有工具继承 `Tool`，实现 `to_api_schema()` + `execute()` |
| **Manager/Service** | 多处 | `TokenBudgetManager`, `CheckpointManager`, `CompactService` |
| **Mode-Conditional** | `main.py` | `wiki_strict` 模式在初始化时注入不同工具集和 prompt |

---

## 二、32K 上下文小模型支持评估

### 2.1 已实现的 32K 支持

| 组件 | 实现状态 | 文件 |
|------|---------|------|
| Token 预算管理器 | ✅ 硬编码 32K 阈值 | `token_budget.py` |
| 消息脱水 | ✅ 替换旧 tool_result 为摘要 | `dehydration.py` |
| 运行时快照 | ✅ 断点保存 + resume | `knowledge/dehydrator.py` |
| Flow State 提示 | ✅ PLAN→LOCATE→IMPLEMENT→VERIFY | `flow_state.py` |
| 自动压缩 | ✅ 基于 API 的摘要 | `compact.py` |

### 2.2 缺失的关键能力（按优先级排序）

#### 🔴 P0：Token 估算不准确

**问题：**
- `token_budget.py:50` 使用 `chars / 1.8` 估算 token，但代码（大量短 token）和中文的 token 密度远高于英文散文
- `engine.py:263` 硬编码乘以 `1.5` 作为安全缓冲，没有模型感知
- `compact.py:15` `CHARS_PER_TOKEN = 4` 与上面的 `1.8` 不一致

**影响：** 32K 模型下，1000 字符的代码可能是 400-600 token，按 `1.8` 估算只有 555 token，但实际可能是 2-3 倍。这会导致预算管理完全失效。

**建议：**
- 集成 tiktoken / transformers Tokenizer 做精确估算
- 至少为不同模型（Claude、GPT、本地模型）使用不同的 chars/token 比率
- 移除硬编码的 `1.5` 乘数，改为基于模型上下文窗口的动态缓冲

#### 🔴 P0：Compact 不适合小模型

**问题：**
- `compact.py` 使用 LLM API（可能是远程大模型）来做摘要，但如果用户用的是 32K 本地小模型，compact 本身就要消耗大量 token
- `COMPACT_MAX_OUTPUT_TOKENS = 4096`，一次 compact 可能消耗 5K-10K token
- 小模型的输出质量可能不足以生成有用的摘要

**建议：**
- 实现**分层压缩**：先用规则化摘要（提取文件列表、关键决策），只有必要时才用 LLM
- 对本地小模型，使用**滑动窗口摘要**而非全量压缩
- 提供 `no-compact` 模式，改用更激进的脱水 + checkpoint

#### 🔴 P0：没有模型感知的 BudgetThresholds

**问题：**
- `token_budget.py:17-23` 的阈值是硬编码的 32K 值：
  ```python
  soft_limit=16_000, compact_limit=20_000, checkpoint_limit=24_000, hard_stop_limit=26_000
  ```
- 如果用户用的是 8K 或 16K 模型，这些阈值完全不适用
- 如果用户用的是 128K 模型，阈值过于保守

**建议：**
- 根据 `model` 和 `max_tokens` 动态计算阈值
- 支持配置覆盖（`--token-soft-limit` 等）

#### 🟡 P1：Wiki-Strict 模式缺乏代码级状态机

**问题：**
- `flow_state.py` 只是一个**字符串 prompt 注入**，没有代码层面的状态跟踪和强制
- 模型可能跳过 LOCATE 直接 IMPLEMENT，或者跳过 VERIFY
- 没有状态转换验证

**建议：**
- 在 `Engine` 中添加 `current_flow_state` 属性
- 工具调用前检查当前状态是否允许该工具
- 状态转换由代码控制，而非仅靠 prompt

#### 🟡 P1：没有 Prompt Caching 策略

**问题：**
- System prompt (~5K chars) 每次 API 调用都重复发送
- 对于 32K 模型，5K 的 system prompt 占用了 15% 的上下文
- Claude 支持 prompt caching，但代码中没有利用

**建议：**
- 支持 Anthropic 的 `cache_control` (ephemeral)
- 将 system prompt 标记为可缓存
- 对 OpenAI，使用 `prompt` + `messages` 分离

#### 🟡 P1：缺少输出 Token 预算

**问题：**
- `max_tokens` 是单次响应的上限，不是 session 级别的
- 在 32K 限制下，如果模型一次输出 8K，留给上下文的只有 24K
- 没有考虑 "input + output <= context_window" 的约束

**建议：**
- 动态调整 `max_tokens` 基于当前上下文大小
- 预留固定比例的上下文给输出（如 25%）

#### 🟢 P2：Checkpoint 恢复粒度太粗

**问题：**
- Checkpoint 保存了整个对话，恢复时只能从断点重新开始
- 没有细粒度的 "回到某一步" 能力
- Checkpoint 元数据中没有保存当时的具体状态（当前文件、目标函数等）

**建议：**
- 在 checkpoint 中嵌入 `RuntimeSnapshot`（当前文件、目标符号、最近错误）
- 支持 `/resume-from-checkpoint --step N`

---

## 三、Plan Mode 与 Dream Mode Bug 分析

### 3.1 Plan Mode

#### Bug 1：`EnterPlanModeTool.is_read_only()` 返回 `True`（严重）

**位置：** `src/core/tools/plan_tools.py:77`

```python
def is_read_only(self) -> bool:
    return True  # ❌ 错误！
```

**问题：** Plan mode 会：
1. 修改 `engine._tools`（替换整个工具集）
2. 修改 `engine.system_prompt`（追加 plan mode section）
3. 创建计划文件

这些都是**写入操作**，但标记为 `read_only=True` 意味着它会被**自动批准**，不会经过用户确认。

**风险：** 模型可以在未经用户同意的情况下进入 plan mode，锁定工具集，阻止正常的文件编辑。

**修复：**
```python
def is_read_only(self) -> bool:
    return False
```

---

#### Bug 2：`PlanModeManager.enter()` 丢失工具状态

**位置：** `src/core/plan.py:122-131`

```python
plan_tools: list[Tool] = [
    FileReadTool(),
    GlobTool(),
    GrepTool(),
    FileEditTool(),   # 新实例
    FileWriteTool(),  # 新实例
    ...
]
self._engine.set_tools(plan_tools)
```

**问题：** 每次进入 plan mode 都创建新的 tool 实例，而不是复用已有实例。这意味着：
- `FileEditTool` 的失败计数、备份历史丢失
- `FileEditTool_S`（strict 模式）的备份目录状态丢失
- 任何工具的内部状态（如计数器、缓存）都被重置

**修复：** 从 `_saved_tools` 中筛选并复用实例，只替换不允许的工具。

---

#### Bug 3：Plan mode 期间 system prompt 被覆盖

**位置：** `src/core/plan.py:137`

```python
self._engine.system_prompt = self._saved_prompt + "\n\n" + plan_section
```

**问题：** `system_prompt` 是一个 property setter。如果 plan mode 期间有其他代码（如 auto-dream、companion）修改了 `engine.system_prompt`，退出时恢复的 `_saved_prompt` 是旧的，会丢失中间修改。

**具体场景：**
1. 用户进入 plan mode
2. auto-dream 触发，`build_system_prompt()` 重建 prompt（包含更新的 MEMORY.md）
3. 用户退出 plan mode → `_saved_prompt`（旧的，不含新 MEMORY.md）被恢复

**修复：** 退出时不直接恢复 `_saved_prompt`，而是重新调用 `build_system_prompt()` 再追加 plan section。

---

#### Bug 4：`FileEditTool` / `FileWriteTool` 权限检查缺失

**位置：** `src/core/plan.py:126-127`

```python
FileEditTool(),   # allowed only for plan file (checked by permissions)
FileWriteTool(),  # allowed only for plan file (checked by permissions)
```

**问题：** 注释说 "checked by permissions"，但 `permissions.py` 中没有针对 plan mode 的特殊逻辑。`FileEditTool` 可以编辑任何文件，不只是 plan 文件。

**风险：** 在 plan mode 中，模型仍然可以修改项目代码，违背了 plan mode "只读探索" 的设计意图。

**修复：** 在 `PermissionChecker` 中添加 plan mode 感知，或者给 plan mode 的 FileEditTool/FileWriteTool 添加路径白名单。

---

#### Bug 5：Plan file 生成可能无限循环

**位置：** `src/core/plan.py:102-107`

```python
for _ in range(10):
    slug = _generate_slug()
    path = plans_dir / f"{slug}.md"
    if not path.exists():
        break
```

**问题：** 如果 `~/.claude/plans/` 目录下已经存在大量文件（如 3000+ 个），10 次循环内找不到唯一 slug 的概率很高。循环结束后 `self._plan_file` 仍然被设为最后一个 `path`，即使它已存在。

**修复：** 检查循环结束后 `path.exists()`，如果仍存在则使用时间戳兜底。

---

### 3.2 Dream Mode

#### Bug 1：Dream 期间消息被意外持久化到 session

**位置：** `src/core/main.py:658-672`

```python
def _run_dream(engine, memory_dir, permissions, quiet=False):
    saved_messages = list(engine.messages)  # 浅拷贝
    engine.messages = []                     # 清空
    dream_prompt = build_dream_prompt(memory_dir)
    run_query(engine, dream_prompt, ...)     # 执行 dream
    engine.messages = saved_messages         # 恢复
```

**问题：**
1. `run_query()` 内部会调用 `engine.submit()`，而 `submit()` 会调用 `self._persist(message)`
2. `_persist()` 将消息追加到 `session_store`
3. 所以 dream 期间的所有消息（system prompt + dream instructions + assistant 回复）都被写入了 session JSONL
4. 恢复 `engine.messages` 只是恢复了内存状态，session 文件已经被污染

**后果：**
- `/resume` 会恢复包含 dream 对话的 session
- dream 对话通常很长（包含大量文件列表和指令），占用不必要的空间
- 如果 dream 失败或出错，session 中会有不完整的对话

**修复：** 在 `_run_dream` 中临时禁用 `session_store`：
```python
saved_store = engine._session_store
engine._session_store = None
# ... run dream ...
engine._session_store = saved_store
```

---

#### Bug 2：Dream 后 system prompt 重建可能覆盖 plan mode prompt

**位置：** `src/core/main.py:669`

```python
engine.system_prompt = build_system_prompt(memory_dir=memory_dir)
```

**问题：** 如果当前正处于 plan mode，`engine.system_prompt` 包含 `_saved_prompt + plan_section`。Dream 完成后，直接重建 system prompt 会**丢失 plan mode 的注入部分**，导致 plan mode 状态不一致。

**场景：**
1. 用户在 plan mode 中
2. auto-dream 触发
3. dream 完成 → `engine.system_prompt = build_system_prompt(...)`
4. 用户退出 plan mode → `_saved_prompt`（现在是不含 plan section 的）被恢复
5. 结果：system prompt 完全丢失了 plan mode 的上下文

**修复：** Dream 前检查 `plan_manager.is_active`，如果为真则不重建 system prompt，或者在重建后重新注入 plan section。

---

#### Bug 3：`should_auto_dream` 的 session 计数不准确

**位置：** `src/core/memory.py:132-151`

```python
def should_auto_dream(memory_dir, min_hours, min_sessions, current_session_id, sessions_dir=None):
    last = read_last_consolidated_at(memory_dir)
    # ...
    for f in scan_dir.iterdir():
        if f.suffix == ".jsonl" and current_session_id not in f.name and f.stat().st_mtime > last:
            count += 1
    return count >= min_sessions
```

**问题：**
1. `current_session_id not in f.name` 是子字符串匹配。如果当前 session ID 是 `"20260418"`，而旧文件是 `"20260418-old.jsonl"`，这个检查会误排除
2. 只检查 `.jsonl` 文件，但 session 文件可能包含时间戳，格式不统一
3. `sessions_dir` 默认是 `~/.mini-claude/sessions/`，但 `SessionStore` 使用 `{cwd_hash}/` 子目录结构（见 `session.py`），所以 `should_auto_dream` 扫描的目录可能根本不对

**修复：**
- 使用精确的文件名匹配而非子字符串
- 统一 session 目录扫描逻辑，递归扫描子目录
- 或者直接使用 `SessionStore` 的 API 获取 session 列表

---

#### Bug 4：Dream lock 的 PID 检查不可靠

**位置：** `src/core/memory.py:78-100`

```python
def try_acquire_lock(memory_dir):
    lp = _lock_path(memory_dir)
    my_pid = os.getpid()
    try:
        stat = lp.stat()
        age = datetime.now().timestamp() - stat.st_mtime
        holder_pid = int(lp.read_text().strip())
        if age < HOLDER_STALE_S:
            try:
                os.kill(holder_pid, 0)
                return False
            except OSError:
                pass
    except (OSError, ValueError):
        pass
    lp.write_text(str(my_pid))
    return True
```

**问题：**
1. `os.kill(holder_pid, 0)` 检查进程是否存在，但如果有**PID 复用**（旧进程死亡，新进程恰好拿到相同 PID），会错误地认为锁仍被持有
2. 没有原子性保证：`read_text()` 和 `write_text()` 之间可能有竞争条件
3. 如果 `lp.read_text().strip()` 返回空字符串，`int("")` 会抛出 `ValueError`，虽然被捕获了，但此时锁被无条件获取

**修复：** 使用文件锁（`fcntl` / `msvcrt`）替代 PID 文件。

---

#### Bug 5：`build_dream_prompt()` 假设工具可用

**位置：** `src/core/memory.py:277-329`

Dream prompt 指示模型使用 `Glob`、`Read`、`Write`、`Edit` 工具来整理记忆。但：
1. 如果当前处于 plan mode，工具集被替换为 plan tools，模型可能没有 `Write`/`Edit`
2. Dream 期间 `engine.messages` 被清空，但工具集没有被替换，模型可能尝试调用 `Bash` 等危险工具

**修复：** Dream 期间应该使用一个固定的、安全的工具子集（只有 Read/Glob/Write/Edit）。

---

## 四、总结与建议

### 4.1 32K 支持的优先修复清单

| 优先级 | 问题 | 预估工作量 |
|--------|------|-----------|
| P0 | 精确的 token 估算（集成 tiktoken） | 1-2 天 |
| P0 | 模型感知的 BudgetThresholds | 半天 |
| P0 | 小模型友好的 compact 策略 | 2-3 天 |
| P1 | Wiki-Strict 代码级状态机 | 3-5 天 |
| P1 | Prompt caching | 1-2 天 |
| P2 | Checkpoint 细粒度恢复 | 1-2 天 |

### 4.2 Plan/Dream 修复清单

| 优先级 | 问题 | 文件 |
|--------|------|------|
| 🔴 | `EnterPlanModeTool.is_read_only()` 返回 True | `plan_tools.py:77` |
| 🔴 | Plan mode 期间 FileEditTool 无路径限制 | `plan.py:126` |
| 🟡 | Dream 污染 session store | `main.py:663` |
| 🟡 | Dream 后覆盖 plan mode prompt | `main.py:669` |
| 🟡 | `should_auto_dream` session 计数错误 | `memory.py:132` |
| 🟡 | Plan file slug 碰撞 | `plan.py:102` |
| 🟢 | Dream lock PID 竞争条件 | `memory.py:78` |

### 4.3 架构层面的长期改进

1. **Engine 拆分：** `Engine` 类 600 行，承担太多职责。拆分为 `ToolExecutor`、`MessageNormalizer`、`BudgetController`
2. **main.py 拆分：** 1400 行的 REPL 逻辑应该拆分为 `REPL`、`Renderer`、`EventLoop`
3. **统一配置：** 分散在 `config.py`、`token_budget.py`、`sandbox/config.py` 的配置应该集中管理
4. **Wiki-Strict 测试：** 目前零测试覆盖，需要补充 `ASTRead`、`FileEditTool_S`、`PostEditGuard` 的测试
