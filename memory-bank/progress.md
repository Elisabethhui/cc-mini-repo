# Progress

## 项目
CC-MINI Wiki-Strict 模式升级项目

## 当前状态
**Phase 5 模块已完成：reconcile / archive / query-archive / lint / maintenance**

项目已完成全部 Phase 0-5 模块：
- Phase 0: 规则与契约定稿
- Phase 1: 运行时固化 + Goal Stack 占位
- Phase 2: scan / digest / snapshot / drift-stop
- Phase 3: TaskPack / EditSpec / /prime / /plan
- Phase 4: ASTRead / strict patch / verify-retry / Re-anchor
- Phase 5: reconcile / archive / query-archive / lint / maintenance

pytest 回归通过（277 passed）

**Phase 0-5 全部完成，项目 v2.0 完整实现**

### 已完成的基础工作
- Step 1：memory-bank 基础文件 ✓
- Step 2：schema 规则层骨架 ✓
- Step 3：frontmatter 规范 ✓
- v2.0 Human Docs 完整版 ✓
  - `system-design-v2-full.md`
  - `phase-0-4-full-guide.md`
  - `context-safeguard-full.md`
  - `goal-anchoring-full.md`

### 旧 Step 4 状态
**作废，不再作为后续执行依据**。相关内容已标记为 deprecated。

## Phase 1 模块已完成任务

### Phase 1 加速版模块（phase-1-module-runtime-and-placeholder）
完成时间：2026-04-13

**Subtask A — 运行时规则固化**
- [x] Python 运行时规则写入 `AGENTS.md`
- [x] `findings.md` 记录当前项目运行时口径（解释器、工作目录、PYTHONPATH）
- [x] `decisions.md` 新增 D-009（禁止依赖外层 shell 虚拟环境）

**Subtask B — Goal Stack 最小占位**
- [x] `coordinator.py` 新增 `get_minimal_goal_stack()` 函数
- [x] 返回结构包含：global_goal, step_goal, task_goal, current_action, done_definition, out_of_scope
- [x] 验证导入通过

**Subtask C — mode 传递与 token risk 补齐**
- [x] 验证 mode 传递链完整：main.py → coordinator.py → engine.py
- [x] `engine.py` 新增 token risk 最小可见输出（非 NORMAL 状态时打印）
- [x] pytest 回归通过（277 passed, 9 skipped）

**Subtask D — 文档同步**
- [x] 更新 `progress.md`（本文件）
- [x] 更新 `architecture.md`

**延后问题（仍保留到 Phase 2+）**
- `/scan`, `/digest`, `/digest --changed` → Phase 2
- 完整 dehydration / Runtime Snapshot 写入闭环 → Phase 2
- TaskPack / EditSpec / `/prime` / `/plan` → Phase 3
- ASTRead / patch / debug / retry → Phase 4

## Phase 0 进行中任务

### 已完成的 Phase 0 工作
1. [x] 验证 schema 规则层完整性（9个 policy 文件已就位）
2. [x] 补充 conventions.md 的 v2.0 新增字段（goal_refs, snapshot_refs, deferred_issue_refs）
3. [x] 创建 `phases/` 目录
4. [x] 创建 `phase-0-exec.md`
5. [x] 更新 `architecture.md` 记录 v2.0 架构元素
6. [x] 更新 `progress.md` 记录 Phase 0 状态
7. [x] Phase 0 最终验收

## Phase 2 加速版模块已完成任务

### Phase 2 模块（phase-2-accelerated-scan-digest-snapshot）
完成时间：2026-04-13

**Subtask A — 命令与入口接入**
- [x] `commands.py` 新增 `/scan` 命令处理函数 `_cmd_scan()`
- [x] `commands.py` 新增 `/digest` 命令处理函数 `_cmd_digest()`
- [x] 支持 `/digest --changed` 模式
- [x] 命令已注册到 `_COMMAND_TABLE`

**Subtask B — scan / digest / digest-changed 最小闭环**
- [x] `WikiIngester` 支持 entity 状态升级（raw_ast → partially_digested → digested/stale）
- [x] 新增 `DigestStatus` 枚举定义四种状态
- [x] Entity 文件写入 frontmatter 包含 status、source_hash、updated_at
- [x] `ChangedFileTracker` 实现变更文件跟踪
- [x] `/digest --changed` 可消费变更列表

**Subtask C — 最小 dehydration + snapshot**
- [x] 新建 `knowledge/dehydrator.py` 模块
- [x] `RuntimeSnapshot` 数据结构包含：current_step, active_goal, target_files, primary_symbols, last_error, next_action, token_estimate, budget_state
- [x] `RuntimeSnapshotWriter` 支持写入 wiki/log.md 和独立 JSON 文件
- [x] `MinimalDehydrator` 在 token risk 临界时触发 dehydration 并写入 snapshot
- [x] `engine.py` 集成 dehydrator 调用

**Subtask D — 最小 drift stop**
- [x] 新建 `DriftTracker` 类跟踪失败次数
- [x] 最大重试次数阈值（MAX_RETRY = 3）
- [x] 超过阈值时写入 `deferred_issues.md`
- [x] `WikiIngester.ingest_file()` 集成 drift stop 检查

**Subtask E — 文档同步**
- [x] 更新 `progress.md`（本文件）
- [x] 更新 `architecture.md`
- [x] 更新 `findings.md`

**延后问题（仍保留到 Phase 3+）**
- ~~TaskPack / EditSpec~~ → Phase 3 ✅ 已完成
- ~~`/prime`, `/plan` 命令~~ → Phase 3 ✅ 已完成
- ASTRead / patch / debug / retry → Phase 4

**Phase 0 已完成，Phase 1 模块已完成，Phase 2 模块已完成，Phase 3 模块已完成，Phase 4 模块已完成，Phase 5 模块已完成**

## Phase 3 加速版模块已完成任务

### Phase 3 模块（phase-3-accelerated-taskpack-prime-plan）
完成时间：2026-04-13

**Subtask A — 正式对象定义**
- [x] `TaskPack` 正式对象 - `wiki/taskpack.py`
- [x] `EditSpec` 正式对象 - 结构化修改意图
- [x] `GoalStack` 正式对象 - 四层目标锚点
- [x] `DeferredIssue` 结构 - 延后问题记录
- [x] `MicroForkNote` 结构 - 轻量分叉记录

**Subtask B — `/prime` 命令**
- [x] `commands.py` 新增 `_cmd_prime()` 处理函数
- [x] 从 digest 生成 TaskPack
- [x] 输出最小 Goal Stack
- [x] 持久化到 `.cc-mini/wiki/taskpacks/*.json`

**Subtask C — `wiki_strict` 下 `/plan`**
- [x] `commands.py` 新增 `_cmd_plan_wiki()` 处理函数
- [x] 结构化输出：Goal Stack、TaskPack、EditSpec
- [x] Patch Plan（仅计划，不执行）
- [x] Deferred Issues 记录

**Subtask D — 状态与越界控制**
- [x] `raw_ast` 文件检测并阻止进入 patch
- [x] `stale` 文件检测并写入 deferred issue
- [x] 越界问题写入 Deferred Issue Log
- [x] Plan 不会自由散开到 Phase 4

**Subtask E — 文档同步**
- [x] 更新 `progress.md`（本文件）
- [x] 更新 `architecture.md`
- [x] 更新 `findings.md`
- [x] 更新 `decisions.md`

## 新增的关键系统能力（v2.0）
1. **Context Safeguard**：OOM 预警 / 上下文脱水 / 快照恢复
2. **Goal Anchoring & Drift Recovery**：目标锚定 / 防偏航 / Re-anchor / Micro-Fork

## 新增/更新的规则文件
- `schema/context_safeguard_policy.md` ✓
- `schema/goal_policy.md` ✓
- `schema/phase_boundary_policy.md` ✓
- `schema/conventions.md`（已更新 v2.0 字段）✓
- `phases/phase-0-exec.md` ✓

## 后续路线图
- **Phase 0**（当前）：规则与契约定稿 → 完成后进入 Phase 1
- **Phase 1**：模式接入与结构骨架
- **Phase 2**：语义消化与状态升级
- **Phase 3**：任务预热与结构化计划
- **Phase 4**：精准修改与局部 debug 闭环

## 当前不应该做的事情
1. 不要继续沿用旧 Step 4 文件
2. 不要直接进入新的代码实现阶段（Python 代码）
3. 不要让本地 32K 小模型继续主导制度层裁决
4. 不要把后续 Phase 1–4 的实现与当前 Phase 0 混在一起
5. 不要在 Phase 0 中实现 `/scan`、`/digest`、`/prime`、patch、debug 等功能

## Phase 4 加速版模块已完成任务

### Phase 4 模块（phase-4-accelerated-safe-edit-debug）
完成时间：2026-04-13

**Subtask A — ASTReadTool**
- [x] `tools/ast_read.py` - 增强支持三种读取模式
- [x] symbol 模式 - 通过类/函数名读取
- [x] span 模式 - 通过行号范围 [start, end] 读取  
- [x] anchor 模式 - 通过锚文本匹配读取
- [x] outline 模式 - 返回文件大纲

**Subtask B — strict patch**
- [x] `tools/file_edit_strict.py` - 增强 strict patch 功能
- [x] preview_only 模式 - 仅预览 diff 不应用
- [x] backup 机制 - 时间戳命名备份
- [x] rollback 方法 - 从备份回滚
- [x] exact-match-first - 严格匹配优先

**Subtask C — verify / retry / traceback cleaning**
- [x] 新建 `tools/error_handler.py`
- [x] `clean_traceback()` - 清洗内部堆栈帧
- [x] `summarize_error()` - 错误摘要与建议
- [x] `RetryLoop` - 自动重试控制
- [x] `verify_and_retry()` - 包装函数

**Subtask D — Re-anchor 与 failed attempts**
- [x] 新建 `tools/reanchor.py`
- [x] `ReanchorLoop` - 六问回正逻辑
- [x] `ReanchorContext` - 失败上下文跟踪
- [x] `should_reanchor()` - 重定位检测
- [x] `check_ask_user_fallback()` - 人工兜底阈值
- [x] Micro-Fork Note 自动记录

**Subtask E — 文档同步**
- [x] 更新 `progress.md`（本文件）
- [x] 更新 `architecture.md`
- [x] 更新 `findings.md`
- [x] 更新 `decisions.md`

## Phase 5 加速版模块已完成任务

### Phase 5 模块（phase-5-accelerated-maintenance-lifecycle）
完成时间：2026-04-13

**Subtask A — reconcile（页面协调）**
- [x] `core/wiki/reconcile.py` - ReconcileEngine 模块
- [x] `scan_for_stale()` - 扫描 stale/error 状态的 entity 文件
- [x] `check_source_drift()` - 对比源文件哈希检测漂移
- [x] `reconcile()` - 主入口，生成 reconcile items
- [x] `apply_action()` - 应用协调动作（RE_DIGEST, ARCHIVE, DELETE, DEFER）

**Subtask B — archive / query-archive（归档与查询）**
- [x] `core/wiki/archive.py` - ArchiveEngine 模块
- [x] `archive_item()` - 单文件归档，带元数据
- [x] `auto_archive()` - 基于年龄阈值的自动归档
- [x] DEFAULT_AGE_DAYS: snapshot=7d, taskpack=30d, report=14d, entity=90d
- [x] `core/wiki/query_archive.py` - QueryArchive 模块
- [x] 查询方法: by_type, by_date_range, by_original_path, search, list_all
- [x] `get_summary()` - 归档统计摘要

**Subtask C — lint（健康检查）**
- [x] `core/wiki/lint.py` - WikiLinter 模块
- [x] `run_all_checks()` - 运行所有健康检查
- [x] 结构检查: wiki_dir, index_md, entities_dir, taskpacks_dir, reports_dir
- [x] 孤儿检查: orphan_taskpacks, orphan_snapshots, orphan_reports
- [x] 一致性检查: entity_consistency（frontmatter, status 字段）

**Subtask D — stale recovery / maintenance（生命周期维护）**
- [x] `core/wiki/maintenance.py` - MaintenanceEngine 模块
- [x] `run_maintenance()` - 完整维护周期（dry_run 支持）
- [x] 阈值: snapshot=7d, deferred_issue=30d, taskpack=30d, micro_fork=14d
- [x] `stale_recovery()` - 恢复 stale entity（重 digest 或归档）
- [x] `_update_index()` - 自动更新 wiki index.md 统计

**Subtask E — 文档同步**
- [x] 更新 `progress.md`（本文件）
- [x] 更新 `architecture.md`
- [x] 更新 `findings.md`
- [x] 更新 `decisions.md`

**Phase 5 全部完成，生命周期管理闭环已实现**

## Phase 5 后最小真实功能验证 (current-ccmini-minimal-real-validation)
完成时间：2026-04-13

### 验证目标
验证当前升级后的 cc-mini 是否已经满足本地 32K 场景目标

### 验证结果
| 子任务 | 验证内容 | 状态 |
|--------|----------|------|
| A | Runtime & Standard Baseline | ✅ 通过 |
| B | 分析链 (scan/digest) | ✅ 通过 |
| C | 计划链 (TaskPack/GoalStack) | ✅ 通过 |
| D | 修改链 (ASTRead/patch/verify) | ✅ 通过 |
| E | 保护链 & 维护链 | ✅ 通过 |
| F | 文档同步 | ✅ 完成 |

### 关键验证项
- **Runtime**: Python 3.11.14, PYTHONPATH=src 正确 ✅
- **Pytest**: 277 passed, 9 skipped ✅
- **模块导入**: 13/13 核心模块全部导入成功 ✅
- **ASTRead**: symbol/span/anchor/outline 四种模式全部可用 ✅
- **FileEdit**: 精确匹配修改成功 ✅
- **最小真实任务闭环**: ASTRead → FileEdit → 验证，完整跑通 ✅

### 最终结论
**当前升级后的 cc-mini 已满足本地 32K 场景目标，达到 Beta 可用标准。**

## 备注
本文件从现在开始，服务于 **v2.0 升级后的项目状态记录**。

## Phase 6-A Progress

### Module 1
状态：`conditional pass`

#### 已完成
- Module 1 源码侧实现已完成
- `validate_target_identity.sh` 已执行
- `summary.txt` 已生成
- 允许进入 Module 2

#### 未完成
- 安装态 smoke test 未单独执行
- 最终产品运行态验证留待 Final Validation 阶段统一收口

#### 决策
- 为了继续推进 Phase 6-A 主线，允许在 Module 1 安装态 smoke test 暂缓的前提下进入 Module 2
- 必须在 Final Validation 中明确写入该项为 deferred validation

### Module 2
状态：`ready_to_start`

### Module 3
状态：`blocked_until_module_2_pass`

### Final Validation
状态：`pending`