# Decisions

> 用途：记录当前项目的“已拍板决定”，防止 Claude / 小模型在后续会话里反复重猜。
> 规则：只记录已经确认的决定；未确认问题放到 Deferred Decisions。

## Active Decisions
### D-001 项目状态回退
- 当前项目正式回退到 Step 3 完成态。
- 旧 Step 4 相关内容不再作为后续执行依据。

### D-002 当前总设计依据
- 当前后续执行统一以 `memory-bank/system-design-v2.md` 为准。
- 旧版总设计文件只保留为历史背景，不作为当前执行依据。

### D-003 当前阶段起点
- 当前从 **Phase 0 已完成** 的状态进入后续开发。
- 下一正式阶段为 **Phase 1**。

### D-004 当前工作模式
- ChatGPT 负责：设计、拆任务、定边界、复核。
- Claude Code 负责：执行当前任务、运行测试、更新状态。
- 当前不启用完整多 agent 团队模式。

### D-005 当前控制平面
- `memory-bank/` 是当前项目的长期规则层与外部记忆层。
- `current-task.md` 是当前唯一任务真相源。
- `findings.md` 记录已确认事实与能力地图。
- `decisions.md` 记录已拍板决定。

### D-006 当前开发策略
- 当前代码已部分可执行，因此优先采用“保护现状 + 增量补缺”的方式。
- 禁止默认按“从零接入 wiki_strict”的思路重写已有入口、配置或运行模式。

### D-007 阶段边界
- Phase 1 只做模式接入与结构骨架。
- Phase 2 之后的 digest / TaskPack / patch / debug 逻辑，不得在 Phase 1 提前实现。

### D-008 质量门禁
- 只有当前任务要求的测试通过，才允许更新 `progress.md` 和 `architecture.md`。
- 若测试失败且超过允许修复轮数，必须停止并输出阻塞报告。

### D-009 Python 运行时规则固化
- 禁止依赖外层 shell 已激活虚拟环境的隐式状态。
- 固定解释器：`/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python`
- 固定工作目录：`/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo`
- 导入 `src/core/...` 模块时必须使用：`PYTHONPATH=src`
- 禁止使用裸 `python` 或 `python3`

### D-010 Phase 2 Entity 状态升级规则
- Entity 文件必须包含 YAML frontmatter
- 状态字段：`status` 取值 {raw_ast, partially_digested, digested, stale, error}
- 变更检测：`source_hash` (SHA256 前16位)
- 时间戳：`updated_at`
- 状态流转：raw_ast → partially_digested (有 docstring) → digested | stale

### D-011 Phase 2 Drift Stop 阈值
- 最大重试次数：`MAX_RETRY = 3`
- 超过阈值后：写入 `.cc-mini/deferred_issues.md` 并停止重试
- 适用场景：文件不存在、解析失败、路径错误

### D-012 Phase 3 TaskPack 落盘格式
- TaskPack 采用 JSON 格式持久化到 `.cc-mini/wiki/taskpacks/*.json`
- Deferred Issue 采用 JSON 格式持久化到 `.cc-mini/wiki/reports/deferred-issues/*.json`
- Micro-Fork Note 采用 JSON 格式持久化到 `.cc-mini/wiki/reports/micro-forks/*.json`
- 文件命名：`{task_id}.json` 或 `{timestamp}.json`

### D-013 Phase 3 越界控制规则
- `raw_ast` 状态的 Entity 必须先 digest 才能进入 plan/patch 阶段
- 检测到 `raw_ast` 时：写入 Deferred Issue 并阻止生成 EditSpec
- 检测到 `stale` 时：写入 Deferred Issue 但允许继续（警告）

### D-014 Phase 4 ASTRead 读取模式
- symbol 模式：通过类/函数名读取，仅支持 Python 文件
- span 模式：通过行号范围 [start, end] 读取，支持任意文本文件
- anchor 模式：通过锚文本匹配读取上下文，支持任意文本文件
- outline 模式：返回文件大纲，仅支持 Python 文件

### D-015 Phase 4 Patch 阈值
- 最大 patch 尝试次数：`MAX_PATCH_ATTEMPTS = 3`
- 最大路径尝试次数：`MAX_PATH_ATTEMPTS = 3`
- 最大 symbol 尝试次数：`MAX_SYMBOL_ATTEMPTS = 3`
- ask_user 兜底阈值：6 次总失败 或 2 次完整重试循环

### D-016 Phase 4 Re-anchor 六问
1. What was the original intent for modifying the target?
2. Has the file structure changed?
3. Is the symbol still at the expected location?
4. Are there conflicting changes in the codebase?
5. Should we broaden or narrow the search scope?
6. What alternative approaches exist to achieve the same goal?

### D-017 Phase 5 归档年龄阈值
- snapshot: 7 天自动归档
- taskpack: 30 天自动归档
- report: 14 天自动归档
- entity: 90 天自动归档
- 所有归档操作支持 dry_run 模式预览

### D-018 Phase 5 维护生命周期
- MaintenanceEngine 提供统一生命周期管理入口
- reconcile: 检测 stale/drift 并生成恢复计划
- archive: 自动归档过期文件，保留元数据
- lint: 健康检查覆盖结构、孤儿文件、一致性
- stale_recovery: 支持重 digest 或归档恢复
- 所有操作优先 dry_run，实际执行需显式确认

## Deferred Decisions
- 所有 Phase 已完成，无剩余延后决策
- ~~archive / reconcile 的精确算法~~ → Phase 5 ✅ 已完成
- ~~TaskPack 的最终落盘格式细节~~ → Phase 3 ✅ 已完成
- ~~Snapshot writer 的具体实现方式~~ → Phase 2 ✅ 已完成

## Phase 5 解决的历史遗留决策
- archive / reconcile 算法已定稿（D-017, D-018）
- 生命周期管理阈值已确定（7d/14d/30d/90d）
- dry_run 优先原则确立（实际执行需显式确认）

### D-019 Beta 可用性判定
**决定**: 当前升级后的 cc-mini 已达到 Beta 可用标准  
**验证依据**: current-ccmini-minimal-real-validation (2026-04-13)
- Runtime 验证通过
- Pytest 277 passed
- 分析链/计划链/修改链/保护链/维护链全部验证通过
- 最小真实任务闭环跑通

### D-020 本地 32K 场景目标达成
**决定**: cc-mini v2.0 已满足本地 32K 场景目标  
**能力覆盖**:
- ✅ Standard 模式未损坏
- ✅ wiki_strict 模式可进入
- ✅ 分析链 (scan/digest/entity) 可用
- ✅ 计划链 (Goal Stack/TaskPack/EditSpec) 可用
- ✅ 修改链 (ASTRead/patch/verify/retry/Re-anchor) 可用
- ✅ 保护链 (token/dehydration/checkpoint) 存在
- ✅ 维护链 (lint/reconcile/archive/maintenance) 可用

## Superseded Decisions
- 旧 Step 4 相关设计与执行包：已降级为历史草稿，不再作为执行依据。
