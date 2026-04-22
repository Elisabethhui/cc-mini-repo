# cc-mini 项目会话总结 — clean_gsd_new

> 本文件用于新对话快速接入上下文。日期：2026-04-18

---

## 一、项目背景

**cc-mini** 是一个 AI 编码助手 harness，实现 Claude Code 核心功能（交互式 REPL、agentic 工具循环、权限系统、会话持久化），带有 **Wiki-Strict Mode** 专为本地 32K token 上下文小模型设计。

- **双模式**：`standard`（默认）和 `wiki_strict`（结构化工作流，AST 代码读取、严格 patch 验证、自动化生命周期管理）
- **核心挑战**：在 32K 上下文中管理 token 预算、脱水、压缩、断点恢复
- **仓库**：cc-mini-repo（当前工作分支：`project-cleanup`）

---

## 二、本次会话完成的工作

### 2.1 项目瘦身

目标：仅保留 cc-mini 源代码包和必要文件，删除所有非运行时中间文件。

**已删除/将删除的目录和文件：**

| 路径 | 说明 | 状态 |
|------|------|------|
| `memory-bank/` | 项目设计文档、计划、架构、决策（59 文件，408K） | 待提交删除 |
| `scripts/` | 维护脚本：wiki 检查、版本检查、验证脚本（18 文件，144K） | 待提交删除 |
| `docs/wiki/` | wiki 系统文档（项目管理层，非用户文档，9 文件） | 待提交删除 |
| `manifests/` | raw source manifest（2 文件） | 待提交删除 |
| `.cc-mini/` | 运行时自动生成的 wiki 工作区（165 文件，676K） | 待提交删除 |
| `validation-runs/` | 历史验证记录、日志、快照（20 文件，92K） | 待提交删除 |
| `.cursorrules` | Cursor IDE 规则文件 | 待提交删除 |
| `.windsurfrules` | Windsurf IDE 规则文件 | 待提交删除 |
| `AGENTS.md` | 通用 Agent 规则（中文） | 待提交删除 |
| `.claudeignore` | Claude Code 忽略配置 | 待提交删除 |
| `.claude/commands/` | 3 个自定义 slash command 定义 | 已处理 |

**保留在根目录的文件：**
- `src/core/` — 79 文件，844K，核心源代码
- `tests/` — 32 文件，180K，测试套件
- `pyproject.toml` — 包定义、依赖、CLI 入口
- `install.sh` — 安装脚本
- `docs/` — 用户文档（不含 wiki/ 子目录）
- `README.md` — 主文档（已更新）
- `.github/workflows/` — CI 配置
- `.gitignore` — 已更新，排除运行时生成目录
- `assets/buddy-pikachu.jpg` — buddy 功能图片资源
- `.claude/CLAUDE.md` — 项目指导文件
- `.planning/codebase/` — 代码库映射文档（7 文件，2433 行）
- `ARCHITECTURE_ANALYSIS.md` — 技术架构分析

**`.gitignore` 已更新内容：**
```gitignore
.cc-mini.toml
.cc-mini/
validation-runs/
memory-bank/
scripts/
manifests/
docs/wiki/
```

### 2.2 创建/更新的文件

1. **`.claude/CLAUDE.md`** — 项目专用指导文件
   - 行为准则：Think Before Coding、Simplicity First、Surgical Changes、Goal-Driven Execution
   - 项目架构概览：main.py → engine.py → subsystems
   - 常用命令：开发、测试、wiki 维护、验证
   - Wiki-First Workflow 规则
   - 关键目录和 Wiki Schema 规范

2. **`README.md`** — 已更新为精简版本
   - Overview、Quick Start、Configuration、Architecture、Tools/Slash Commands、Tests/Development
   - 已移除所有对已删除目录的引用

3. **`ARCHITECTURE_ANALYSIS.md`** — 技术架构分析与 32K 支持评估（~400 行）
   - 系统三层架构：CLI/REPL → Engine → Subsystems
   - 数据流完整链路
   - 32K 支持缺口（3 个 P0、2 个 P1、1 个 P2）
   - Plan Mode 4 个 bug、Dream Mode 5 个 bug
   - 架构层面长期改进建议

4. **`.planning/codebase/`** — 代码库映射（通过 4 个并行 gsd-codebase-mapper agent 生成）
   - `STACK.md` (203 行) — 技术栈
   - `INTEGRATIONS.md` (151 行) — 外部集成
   - `ARCHITECTURE.md` (414 行) — 系统设计
   - `STRUCTURE.md` (386 行) — 目录结构
   - `CONVENTIONS.md` (423 行) — 编码规范
   - `TESTING.md` (378 行) — 测试模式
   - `CONCERNS.md` (478 行) — 55 个关注点

---

## 三、发现的关键问题与 Bug

### 3.1 32K 小模型支持 — P0 缺口（按优先级）

| 优先级 | 问题 | 位置 | 影响 |
|--------|------|------|------|
| P0 | Token 估算不准确 | `token_budget.py:50` 用 `chars / 1.8`；`engine.py:263` 硬编码 `* 1.5`；`compact.py:15` `CHARS_PER_TOKEN = 4` | 预算管理完全失效，代码/中文的 token 密度远高于估算 |
| P0 | Compact 不适合小模型 | `compact.py` 使用 LLM API 做摘要，`COMPACT_MAX_OUTPUT_TOKENS = 4096` | 一次 compact 消耗 5K-10K token，小模型输出质量不足 |
| P0 | 没有模型感知的 BudgetThresholds | `token_budget.py:17-23` 硬编码 32K 阈值 | 8K/16K/128K 模型完全不适用 |
| P1 | Wiki-Strict 缺乏代码级状态机 | `flow_state.py` 只是字符串 prompt 注入 | 模型可能跳过状态，没有状态转换验证 |
| P1 | 缺少 Prompt Caching 策略 | System prompt (~5K chars) 每次重复发送 | 32K 模型中占 15% 上下文，Claude 支持 cache 但未利用 |
| P1 | 缺少输出 Token 预算 | `max_tokens` 是单次上限，非 session 级别 | input + output > context_window |
| P2 | Checkpoint 恢复粒度太粗 | 只能整段恢复，无 RuntimeSnapshot | 无法细粒度回到某一步 |

### 3.2 Plan Mode Bug（4 个）

| 严重度 | Bug | 位置 | 说明 |
|--------|-----|------|------|
| 🔴 | `is_read_only()` 返回 True | `plan_tools.py:77` | Plan mode 修改 tools 和 prompt，却标记为只读 → 自动批准，用户无确认 |
| 🔴 | FileEditTool 无路径限制 | `plan.py:126-127` | Plan mode 中模型仍可修改任意文件，违背"只读探索"意图 |
| 🟡 | 丢失工具状态 | `plan.py:122-131` | 每次进入 plan mode 创建新 tool 实例，失败计数、备份历史丢失 |
| 🟡 | System prompt 被覆盖 | `plan.py:137` | 直接赋值 `_saved_prompt + plan_section`，若中间被 auto-dream 修改会丢失 |
| 🟡 | Slug 碰撞 | `plan.py:102-107` | 10 次循环找唯一 slug，文件多时会失败 |

### 3.3 Dream Mode Bug（5 个）

| 严重度 | Bug | 位置 | 说明 |
|--------|-----|------|------|
| 🟡 | Dream 污染 session store | `main.py:658-672` | `_run_dream` 只恢复 `engine.messages` 但未禁用 `_session_store`，dream 对话写入 session JSONL |
| 🟡 | Dream 后覆盖 plan mode prompt | `main.py:669` | Dream 完成后重建 system prompt，若处于 plan mode 会丢失 plan section |
| 🟡 | Session 计数不准确 | `memory.py:132-151` | 子字符串匹配 `current_session_id not in f.name`；目录扫描可能不对 |
| 🟡 | Dream lock PID 竞争条件 | `memory.py:78-100` | PID 复用风险；无原子性；空字符串转 int 抛异常 |
| 🟡 | Dream prompt 假设工具可用 | `memory.py:277-329` | Dream 期间工具集未替换，模型可能调用 Bash 等危险工具 |

### 3.4 已知测试失败（非本次引入）

```
test_context.py::test_build_system_prompt_contains_base_instructions
期望 prompt 包含 "Claude Code"，实际是 "interactive agent"
```

---

## 四、用户偏好与决策

1. **删除前确认**：用户要求"删除前先问过我"。已逐个确认删除清单。
2. **保留根目录结构**：不移走文件到子目录，仅删除非必要文件。
3. **Simplicity First**：用户认同 CLAUDE.md 中的"最小代码解决问题"原则。
4. **GSD 工作流**：用户熟悉 `/gsd-new-project`、`/gsd-map-codebase`、`/gsd-help` 等命令。
5. **Brownfield 项目**：选择先 map codebase 再初始化项目。

---

## 五、下一步建议

### 5.1 立即行动（待提交）

```bash
# 1. 提交项目瘦身
git add -A
git commit -m "cleanup: remove non-runtime files (memory-bank, scripts, wiki, .cc-mini, validation-runs)"

# 2. 可选：重命名分支
git branch -m project-cleanup  # 或其他名称
```

### 5.2 Bug 修复优先级

**第一批次（高影响、低风险）：**
1. `plan_tools.py:77` — `is_read_only()` 改为 `False`（1 行）
2. `main.py:663` — Dream 期间禁用 `session_store`（~5 行）
3. `token_budget.py` — 为不同模型使用不同的 chars/token 比率（小改动）

**第二批次（中等复杂度）：**
4. `plan.py` — 复用 tool 实例、修复 prompt 覆盖、添加路径白名单
5. `memory.py` — 修复 session 计数、使用文件锁替代 PID
6. `main.py:669` — Dream 前检查 plan mode 状态

### 5.3 32K 支持改进

- 集成 tiktoken / transformers tokenizer 做精确估算
- 实现分层压缩（规则化摘要 + LLM 摘要）
- 动态 BudgetThresholds（基于 model + max_tokens）
- Flow State 代码级状态机（Engine 中添加 `current_flow_state`）

### 5.4 架构重构（长期）

- `Engine` 拆分为 `ToolExecutor`、`MessageNormalizer`、`BudgetController`
- `main.py` 拆分为 `REPL`、`Renderer`、`EventLoop`
- 统一配置管理（集中 `config.py`、`token_budget.py`、`sandbox/config.py`）

---

## 六、快速参考

### 常用命令
```bash
# 安装
pip install -e ".[dev]"

# 运行 REPL
PYTHONPATH=src python -m core.main

# Wiki-strict 模式
CC_MINI_MODE=wiki_strict PYTHONPATH=src python -m core.main

# 测试（跳过集成测试）
/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -m pytest tests/ -v -k "not integration"
```

### 关键文件路径
- 入口/REPL：`src/core/main.py`
- Engine：`src/core/engine.py`
- Token 预算：`src/core/token_budget.py`
- 压缩：`src/core/compact.py`
- 脱水：`src/core/dehydration.py`, `src/core/knowledge/dehydrator.py`
- Plan Mode：`src/core/plan.py`, `src/core/tools/plan_tools.py`
- Dream/KAIROS：`src/core/memory.py`
- Flow State：`src/core/flow_state.py`
- Wiki-Strict：`src/core/wiki/`（taskpack, reconcile, archive, post_edit_guard）

### 架构分析文档
- `ARCHITECTURE_ANALYSIS.md` — 完整的问题描述、代码引用、修复建议
- `.planning/codebase/CONCERNS.md` — 55 个关注点
