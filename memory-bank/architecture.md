# Architecture

## 当前定位
本文件记录项目在”回退到 Step 3 + 升级到 v2.0”后的新架构口径。

## 仍然保留的旧资产
- game-design-document.md
- tech-stack.md
- implementation-plan.md
- 旧 schema 基础规则文件

## v2.0 新增架构元素

### Context Safeguard（上下文保障）
**定位**：横切子系统，负责在上下文风险升高时固化任务状态。

**核心职责**：
- token 风险监控（safe/watch/warning/critical/emergency 五级）
- OOM 预警
- 上下文脱水（Dehydration）
- Context Snapshot 生成（Runtime + Markdown 双轨）
- 会话恢复（Resume）

**关键文件**：
- Human Doc: `context-safeguard-full.md`
- Policy: `schema/context_safeguard_policy.md`

### Goal Anchoring & Drift Recovery（目标锚定与偏航恢复）
**定位**：横切子系统，负责防止小模型在长任务中偏离主线。

**核心职责**：
- Goal Stack（四层目标锚点：global_goal, step_goal, task_goal, current_action）
- Drift Detector（五类偏航检测）
- Re-anchor Loop（六问回正流程）
- Deferred Issue Log（延后问题外部化）
- Micro-Fork Note（轻量分叉记录）

**关键文件**：
- Human Doc: `goal-anchoring-full.md`
- Policy: `schema/goal_policy.md`

### Phase Boundary（阶段边界控制）
**定位**：防止跨阶段提前实现、防止小模型失控的正式控制机制。

**核心职责**：
- Phase 0-4 的 In Scope / Out of Scope 定义
- 跨阶段冲突处理规则
- Deferred Issue 强制写入机制

**关键文件**：
- Policy: `schema/phase_boundary_policy.md`
- Guide: `phase-0-4-full-guide.md`

## v2.0 文档体系结构

### Human Docs（总纲层）
给人读的设计说明书：
1. `system-design-v2-full.md` — 总设计完整版
2. `phase-0-4-full-guide.md` — Phase 0-4 路线图
3. `context-safeguard-full.md` — 上下文保障完整设计
4. `goal-anchoring-full.md` — 目标锚定完整设计

### Runner Docs（执行层）
给执行器跑的施工单：
- `phases/phase-0-exec.md` — Phase 0 执行包
- `phases/phase-1-exec.md` — Phase 1 执行包（待创建）
- `phases/phase-2-exec.md` — Phase 2 执行包（待创建）
- `phases/phase-3-exec.md` — Phase 3 执行包（待创建）
- `phases/phase-4-exec.md` — Phase 4 执行包（待创建）

### Schema Policy（规则层）
`schema/*.md` 共 9 个文件：
1. `AGENTS.md` — AI 执行者工作纪律
2. `conventions.md` — 命名、frontmatter、元数据契约
3. `digest_policy.md` — digest 定义与状态转换
4. `conflict_policy.md` — 冲突处理与优先级
5. `taskpack_policy.md` — TaskPack 定义与内容
6. `watchdog_policy.md` — Watchdog 职责边界
7. `context_safeguard_policy.md` — Context Safeguard 契约（v2.0 新增）
8. `goal_policy.md` — Goal Anchoring 契约（v2.0 新增）
9. `phase_boundary_policy.md` — Phase 0-4 边界定义（v2.0 新增）

## Phase 1 模块架构更新

### 新增/修改的代码文件
1. **`src/core/coordinator.py`**
   - 新增 `get_minimal_goal_stack()` 函数（Phase 1 占位实现）
   - 返回包含 6 个字段的字典：global_goal, step_goal, task_goal, current_action, done_definition, out_of_scope

2. **`src/core/engine.py`**
   - 新增 token risk 最小可见输出（Pre-flight check 中，非 NORMAL 状态时打印）
   - 维持 mode 传递链完整性

### 更新的文档文件
1. **`memory-bank/schema/AGENTS.md`**
   - 新增 Python 运行时规则章节（固定解释器、工作目录、PYTHONPATH=src）

2. **`memory-bank/decisions.md`**
   - 新增 D-009：Python 运行时规则固化决定

3. **`memory-bank/findings.md`**
   - 记录已验证的运行时口径和能力地图

## Phase 2 模块架构更新

### 新增/修改的代码文件
1. **`src/core/commands.py`**
   - 新增 `/scan` 命令处理函数 `_cmd_scan()`
   - 新增 `/digest` 命令处理函数 `_cmd_digest()`
   - 支持 `/digest --changed` 模式

2. **`src/core/knowledge/ingester.py`**
   - 新增 `DigestStatus` 枚举（raw_ast, partially_digested, digested, stale, error）
   - 新增 `DriftTracker` 类实现漂移停止（MAX_RETRY = 3）
   - `WikiIngester` 集成状态升级和 drift stop
   - Entity 文件写入 frontmatter 包含 status、source_hash、updated_at

3. **`src/core/knowledge/watcher.py`**
   - 新增 `ChangedFileTracker` 类跟踪变更文件
   - 新增 `get_changed_tracker()` 工厂函数
   - 支持 `/digest --changed` 消费变更列表

4. **`src/core/knowledge/dehydrator.py`**（新建）
   - `RuntimeSnapshot` 数据结构
   - `RuntimeSnapshotWriter` 写入 wiki/log.md 和独立 JSON 快照文件
   - `MinimalDehydrator` 在 token risk 临界时触发 dehydration 并写入 snapshot

5. **`src/core/engine.py`**
   - 集成 `MinimalDehydrator` 调用
   - 在 token risk warning/compact/checkpoint/hard_stop 状态时触发 dehydration + snapshot

## Phase 3 模块架构更新

### 新增/修改的代码文件
1. **`src/core/wiki/taskpack.py`**（新建）
   - `TaskPack` 正式对象 - 任务最小知识压缩包
   - `EditSpec` 正式对象 - 结构化修改意图
   - `GoalStack` 正式对象 - 四层目标锚点 + 完成定义 + 越界声明
   - `DeferredIssue` - 延后问题记录结构
   - `MicroForkNote` - 轻量分叉记录结构
   - `TaskPackManager` - TaskPack 持久化管理器

2. **`src/core/commands.py`**
   - 新增 `_cmd_prime()` - `/prime` 命令，从 digest 生成 TaskPack
   - 新增 `_cmd_plan_wiki()` - `wiki_strict` 下 `/plan`，结构化输出
   - 命令已注册到 `_COMMAND_TABLE`

3. **`src/core/wiki/`**（新建目录）
   - `__init__.py`
   - `taskpack.py`

### 持久化路径
- `.cc-mini/wiki/taskpacks/*.json` - TaskPack JSON 文件
- `.cc-mini/wiki/reports/deferred-issues/*.json` - Deferred Issue 文件
- `.cc-mini/wiki/reports/micro-forks/*.json` - Micro-Fork Note 文件

## Phase 4 模块架构更新

### 新增/修改的代码文件
1. **`src/core/tools/ast_read.py`**
   - 增强支持三种读取模式：symbol、span、anchor
   - symbol 模式 - 通过类/函数名读取代码块
   - span 模式 - 通过行号范围 [start, end] 读取
   - anchor 模式 - 通过锚文本匹配读取上下文
   - outline 模式 - 返回文件大纲

2. **`src/core/tools/file_edit_strict.py`**
   - 增强 strict patch 功能
   - preview_only 参数 - 仅预览 diff 不应用修改
   - 时间戳命名备份机制
   - rollback() 方法支持回滚
   - exact-match-first 严格匹配

3. **`src/core/tools/error_handler.py`**（新建）
   - `clean_traceback()` - 清洗内部堆栈帧
   - `summarize_error()` - 错误摘要与重试建议
   - `RetryLoop` - 自动重试控制
   - `verify_and_retry()` - 包装函数

4. **`src/core/tools/reanchor.py`**（新建）
   - `ReanchorLoop` - Re-anchor 六问回正逻辑
   - `ReanchorContext` - 失败上下文跟踪
   - `should_reanchor()` - 重定位阈值检测
   - `check_ask_user_fallback()` - 人工兜底阈值
   - Micro-Fork Note 自动记录

## Phase 5 模块架构更新

### 新增/修改的代码文件
1. **`src/core/wiki/reconcile.py`**（新建）
   - `ReconcileEngine` - 页面协调引擎
   - `scan_for_stale()` - 扫描 stale/error 状态的 entity 文件
   - `check_source_drift()` - 对比源文件哈希检测漂移
   - `reconcile()` - 主入口，生成 reconcile items
   - `apply_action()` - 应用协调动作（RE_DIGEST, ARCHIVE, DELETE, DEFER）

2. **`src/core/wiki/archive.py`**（新建）
   - `ArchiveEngine` - 归档引擎
   - `archive_item()` - 单文件归档，带元数据（original_path, archive_path, reason, size）
   - `auto_archive()` - 基于年龄阈值的自动归档
   - DEFAULT_AGE_DAYS: snapshot=7d, taskpack=30d, report=14d, entity=90d
   - manifest.json - 归档清单

3. **`src/core/wiki/query_archive.py`**（新建）
   - `QueryArchive` - 归档查询引擎
   - `query_by_type()` - 按类型查询（snapshot, taskpack, report, entity）
   - `query_by_date_range()` - 按日期范围查询
   - `query_by_original_path()` - 按原始路径模糊匹配
   - `search()` - 关键词搜索
   - `list_all()` - 列出所有归档项（默认最近100条）
   - `get_summary()` - 归档统计摘要

4. **`src/core/wiki/lint.py`**（新建）
   - `WikiLinter` - Wiki 健康检查器
   - `run_all_checks()` - 运行所有健康检查
   - 结构检查: wiki_dir_exists, index_md_exists, entities_dir, taskpacks_dir, reports_dir
   - 孤儿检查: orphan_taskpacks, orphan_snapshots, orphan_reports
   - 一致性检查: entity_consistency（frontmatter, status 字段验证）
   - CheckStatus: ok, warning, error, missing

5. **`src/core/wiki/maintenance.py`**（新建）
   - `MaintenanceEngine` - 生命周期维护引擎
   - `run_maintenance()` - 完整维护周期（支持 dry_run）
   - THRESHOLDS: snapshot=7d, deferred_issue=30d, taskpack=30d, micro_fork=14d
   - `stale_recovery()` - 恢复 stale entity（重 digest 或归档）
   - `_update_index()` - 自动更新 wiki index.md 统计信息
   - MaintenanceAction: CLEAN, ARCHIVE, MARK_STALE, UPDATE_INDEX

### 持久化路径
- `.cc-mini/wiki/archive/` - 归档根目录
- `.cc-mini/wiki/archive/snapshots/` - 归档的 snapshot 文件
- `.cc-mini/wiki/archive/taskpacks/` - 归档的 taskpack 文件
- `.cc-mini/wiki/archive/reports/` - 归档的报告文件
- `.cc-mini/wiki/archive/entities/` - 归档的 entity 文件
- `.cc-mini/wiki/archive/manifest.json` - 归档清单

## 当前架构状态

### 已完成
- [x] 旧 Step 4 标记为作废
- [x] v2.0 Human Docs 完整版全部就位
- [x] schema policy 9 个文件全部就位
- [x] conventions.md 已更新 v2.0 字段
- [x] phases/ 目录已创建
- [x] phase-0-exec.md 已创建
- [x] Phase 0 已完成，规则层定稿
- [x] Phase 1 加速版模块已完成：运行时固化 + Goal Stack 占位 + mode 传递校验
- [x] Phase 2 加速版模块已完成：scan / digest / snapshot / drift-stop
- [x] Phase 3 加速版模块已完成：TaskPack / EditSpec / Goal Stack + /prime / /plan
- [x] Phase 4 加速版模块已完成：ASTRead / strict patch / verify-retry / Re-anchor
- [x] Phase 5 加速版模块已完成：reconcile / archive / query-archive / lint / maintenance

### 进行中
- 无

### 后续阶段
- 无

## 验证结论 (current-ccmini-minimal-real-validation)
完成时间：2026-04-13

### 验证状态
**全部通过** - 当前升级后的 cc-mini 已满足本地 32K 场景目标。

### 验证覆盖
| 链路 | 验证项 | 状态 |
|------|--------|------|
| 运行时 | Python 3.11.14, PYTHONPATH=src | ✅ |
| 基线 | pytest 277 passed | ✅ |
| 分析链 | scan/digest/entity 状态升级 | ✅ |
| 计划链 | TaskPack/GoalStack/EditSpec | ✅ |
| 修改链 | ASTRead/FileEdit/retry/reanchor | ✅ |
| 保护链 | TokenBudget/FlowState/Checkpoint | ✅ |
| 维护链 | lint/reconcile/archive/maintenance | ✅ |
| 闭环 | 最小真实任务完整跑通 | ✅ |

### Beta 可用性判定
**当前升级后的 cc-mini 达到 Beta 可用标准**。

## 当前架构结论
1. 旧 Step 4 不再作为执行依据
2. 后续阶段以 v2.0 体系为准
3. 应从 Phase 0 重新开始，而不是继续旧 Step 4
4. Context Safeguard 和 Goal Anchoring 是横切子系统，不是单独新层
5. Phase Boundary 是防止小模型失控的正式控制机制
6. **全部 Phase 0-5 已实现并通过验证**
