# Findings

> 用途：记录已经验证过的事实、入口定位结果、能力地图、风险和延后问题。
> 规则：这里只记录**已确认**或**已执行检查后得到**的信息，不写猜测。

## Current Baseline
- 项目状态：Phase 4 模块已完成，Phase 0-4 全部完成
- 设计基线：以 `memory-bank/system-design-v2.md` 为准
- 历史状态：旧 Step 4 已失效，不再作为执行依据
- 当前策略：先保护现有可运行状态，再做最小增量 patch
- Phase 1 完成内容：运行时固化、Goal Stack 占位、mode 传递校验、token risk 最小可见输出
- Phase 2 完成内容：/scan、/digest、/digest --changed、entity 状态升级、dehydration + snapshot、drift stop
- Phase 3 完成内容：TaskPack、EditSpec、Goal Stack、Deferred Issue、Micro-Fork、/prime、/plan、越界控制

## Verified Facts

### Python 运行时口径（已固化）
- **固定解释器**：`/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python`
- **Python 版本**：3.11.14
- **固定工作目录**：`/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo`
- **导入规则**：必须显式使用 `PYTHONPATH=src`
- **禁止**：裸 `python` / `python3` / 依赖外层 shell venv 状态

### 当前 CLI 入口
- **入口**：`cc-mini` (由 `pyproject.toml` 定义)
- **实际函数**：`core.main:main`
- **入口文件**：`src/core/main.py`
- **mode 参数**：`--mode` 已存在，支持 `standard` / `wiki_strict`

### 当前配置文件
- **主配置**：`src/core/config.py`
- **RunMode**：已定义 `STANDARD` / `WIKI_STRICT`
- **get_run_mode()**：已存在，从环境变量 `CC_MINI_MODE` 读取

### 当前 mode 相关实现
- `RunMode` enum：✅ 可用
- `get_run_mode()`：✅ 可用
- `--mode` CLI 参数：✅ 已定义 (main.py 第719-723行)
- coordinator 中的 mode 判断：✅ 已接入

### 当前 token budget / compact / session / checkpoint 相关实现
- `TokenBudgetManager`：✅ 可用
- `BudgetState`：✅ 5级状态 (normal/warning/compact/checkpoint/hard_stop)
- `FlowState`：✅ 可用 (PLAN/LOCATE/IMPLEMENT/VERIFY)
- `CheckpointManager`：✅ 可用
- `dehydration`：✅ 可用
- `compact`：✅ 可用
- `session`：✅ 可用

### 当前 wiki / knowledge / docs 持久化相关实现
- `WikiIngester`：✅ 可用，支持 Python AST 解析
- `WikiDebounceWatcher`：✅ 可用
- `.cc-mini/wiki/index.md`：✅ 已存在
- `.cc-mini/wiki/entities/`：✅ 已存在

### 当前最小可用测试命令
```bash
# 运行时验证
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python --version
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.config import RunMode; print('runtime ok')"

# 模块测试
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.token_budget import TokenBudgetManager; ..."
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.flow_state import FlowState; ..."
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.knowledge.ingester import WikiIngester; ..."

# pytest
/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -m pytest tests/ -q
```

## Capability Map

### CLI / Entry
- `main.py`：CLI 入口，参数解析，REPL 循环
- `--mode` 参数：支持 standard/wiki_strict
- `--coordinator` 参数：支持 coordinator 模式

### Config Layer
- `config.py`：配置加载，环境变量，TOML 文件
- `RunMode`：standard/wiki_strict 枚举
- `get_run_mode()`：从环境变量读取当前模式

### Coordinator / Engine
- `coordinator.py`：模式判断，系统 prompt 生成
- `engine.py`：核心引擎，工具循环
- 已接入 wiki_strict 判断（`get_coordinator_system_prompt()`）

### Token Budget / Compact
- `token_budget.py`：TokenBudgetManager，5级 BudgetState
- `compact.py`：上下文压缩
- `flow_state.py`：PLAN/LOCATE/IMPLEMENT/VERIFY 状态机

### Session / Checkpoint
- `session.py`：会话持久化
- `checkpoint.py`：快照保存/恢复
- `dehydration.py`：消息脱水

### Wiki / Knowledge (Phase 3 更新)
- `knowledge/ingester.py`：Wiki 生成，AST 解析，Entity 状态升级 (DigestStatus)
- `knowledge/watcher.py`：文件监听，防抖处理，ChangedFileTracker
- `knowledge/dehydrator.py`：RuntimeSnapshot + MinimalDehydrator (Phase 2 新建)
- `wiki/taskpack.py`：TaskPack, EditSpec, GoalStack, DeferredIssue, MicroForkNote (Phase 3 新建)
- `wiki/__init__.py`：Wiki 模块初始化 (Phase 3 新建)
- `.cc-mini/wiki/`：运行时 Wiki 目录
- `.cc-mini/wiki/entities/`：Entity 文件包含 frontmatter (status, source_hash, updated_at)
- `.cc-mini/wiki/log.md`：Runtime Snapshot 写入目标
- `.cc-mini/wiki/snapshots/`：独立 JSON 快照目录
- `.cc-mini/wiki/taskpacks/*.json`：TaskPack 持久化文件 (Phase 3)
- `.cc-mini/wiki/reports/deferred-issues/*.json`：Deferred Issue 文件 (Phase 3)
- `.cc-mini/wiki/reports/micro-forks/*.json`：Micro-Fork Note 文件 (Phase 3)
- `.cc-mini/deferred_issues.md`：Drift stop 记录的延后问题

### Phase 5 新增 (Maintenance & Lifecycle)
- `core/wiki/reconcile.py`：`ReconcileEngine` - 页面协调引擎 (Phase 5)
- `core/wiki/archive.py`：`ArchiveEngine` - 归档引擎，支持自动归档 (Phase 5)
- `core/wiki/query_archive.py`：`QueryArchive` - 归档查询引擎 (Phase 5)
- `core/wiki/lint.py`：`WikiLinter` - Wiki 健康检查器 (Phase 5)
- `core/wiki/maintenance.py`：`MaintenanceEngine` - 生命周期维护引擎 (Phase 5)
- `.cc-mini/wiki/archive/`：归档根目录，包含 manifest.json 清单 (Phase 5)

### Tests / Verification
- `tests/`：26个测试文件
- `conftest.py`：pytest  fixtures

## Risks (Phase 2 Update)
- [低风险] `main.py` 依赖 prompt_toolkit，需要完整环境才能启动
- [已解决] mode 传递链验证完整（main → coordinator → engine）
- [已解决] Goal Stack 已注入占位实现 (`get_minimal_goal_stack()`)
- [低风险] Drift Tracker 最大重试次数硬编码为 3，可能需要配置化
- [中风险] ChangedFileTracker 依赖文件系统写入，可能在高并发下有竞态条件

## Deferred Issues (Updated)
- ~~`/scan`, `/digest` 命令实现~~ → Phase 2 ✅ 已完成
- ~~`dehydrator.py` 完整闭环~~ → Phase 2 ✅ 已完成
- ~~`Runtime Snapshot` 写入~~ → Phase 2 ✅ 已完成
- ~~`TaskPack` / `EditSpec`~~ → Phase 3 ✅ 已完成
- ~~`/prime`, `/plan` 命令~~ → Phase 3 ✅ 已完成
- ~~`ASTReadTool` / `patch` / `retry`~~ → Phase 4 ✅ 已完成
- ~~`reconcile` / `archive` / `maintenance`~~ → Phase 5 ✅ 已完成
- 所有 Phase 已完成，无剩余延后问题

## Phase 0-5 全部完成
项目 v2.0 已完整实现 wiki_strict 模式的全部五个阶段：
1. **Phase 1**: 基础运行时和 Goal Stack
2. **Phase 2**: scan/digest 和 dehydration/snapshot
3. **Phase 3**: TaskPack 和 /prime//plan
4. **Phase 4**: ASTRead, strict patch, verify/retry, Re-anchor
5. **Phase 5**: reconcile, archive/query-archive, lint, maintenance

## Phase 1 模块已完成
- [x] 在 `coordinator.py` 中增加 `get_minimal_goal_stack()` 占位函数
- [x] 验证 mode 传递链完整性
- [x] 确保 token risk 在控制台可见

## Phase 2 模块已完成
- [x] `/scan` 命令实现 - `commands.py` `_cmd_scan()`
- [x] `/digest` 命令实现 - `commands.py` `_cmd_digest()`
- [x] `/digest --changed` 实现 - `ChangedFileTracker`
- [x] Entity 状态升级 - `DigestStatus` (raw_ast → partially_digested → digested/stale)
- [x] `dehydrator.py` 完整闭环 - `MinimalDehydrator` + `RuntimeSnapshotWriter`
- [x] `Runtime Snapshot` 写入 - wiki/log.md + .cc-mini/wiki/snapshots/*.json
- [x] Drift Stop 实现 - `DriftTracker` (MAX_RETRY=3) + deferred_issues.md

## Phase 3 模块已完成
- [x] TaskPack / EditSpec / Goal Stack 正式对象 - `wiki/taskpack.py`
- [x] Deferred Issue Log 结构 - `DeferredIssue` 类
- [x] Micro-Fork Note 结构 - `MicroForkNote` 类
- [x] `/prime` 命令实现 - `commands.py` `_cmd_prime()`
- [x] `wiki_strict` 下 `/plan` 实现 - `commands.py` `_cmd_plan_wiki()`
- [x] 越界控制 - raw_ast 检测阻止 patch + Deferred Issue 写入

## Phase 4 模块已完成
- [x] ASTReadTool 增强 - symbol/span/anchor 三种模式
- [x] strict patch - preview、backup、rollback 支持
- [x] traceback 清洗 - `clean_traceback()` 去除内部堆栈
- [x] verify/retry loop - `RetryLoop` 自动重试控制
- [x] Re-anchor Loop - 六问回正 + Micro-Fork 记录
- [x] ask_user fallback - 失败阈值后人工兜底

## Phase 5 模块已完成
- [x] reconcile 模块 - `core/wiki/reconcile.py` - 页面协调引擎
- [x] archive 模块 - `core/wiki/archive.py` - 归档引擎（自动归档）
- [x] query-archive 模块 - `core/wiki/query_archive.py` - 归档查询
- [x] lint 模块 - `core/wiki/lint.py` - Wiki 健康检查
- [x] maintenance 模块 - `core/wiki/maintenance.py` - 生命周期维护
- [x] 年龄阈值：snapshot=7d, taskpack=30d, report=14d, entity=90d
- [x] 归档清单：`.cc-mini/wiki/archive/manifest.json`

## References
- `memory-bank/system-design-v2.md`
- `memory-bank/progress.md`
- `memory-bank/architecture.md`
- `memory-bank/phases/phase-1-exec.md`
- `memory-bank/schema/phase_boundary_policy.md`
- `memory-bank/schema/goal_policy.md`
- `memory-bank/schema/context_safeguard_policy.md`
