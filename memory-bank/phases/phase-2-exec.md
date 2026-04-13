# Phase 2 Exec — 语义消化与状态升级

## 前置条件
- Phase 1 已通过验收
- `.cc-mini/wiki/` 已可初始化
- 基础结构骨架已经存在

## 本阶段目标
让系统不再只有结构图，而是拥有“可操作的局部熟知识”。
同时接入最小 Context Safeguard：在接近 OOM 时，能够生成最小 snapshot 并写入外部状态。

## In Scope
1. `/scan`
2. `/digest`
3. `/digest --changed`
4. 页面状态从 `raw_ast` 升级到 `partially_digested` / `digested`
5. `flow_state.py` 最小状态检查
6. `knowledge/dehydrator.py` 最小版
7. Runtime Snapshot 最小对象
8. 将 snapshot 写入 checkpoint 或 `wiki/log.md`
9. 在 scan / digest 中加入最小 drift check（例如路径反复失败时停止）

## Out of Scope
1. 不实现正式 TaskPack / EditSpec
2. 不实现 `/prime`
3. 不重构 `/plan`
4. 不实现 ASTRead / strict patch
5. 不实现 debug / retry 闭环
6. 不实现 archive / reconcile

## 允许修改的文件
- `src/core/flow_state.py`
- `src/core/knowledge/dehydrator.py`
- `src/core/wiki/digest.py` 或等价模块
- `src/core/wiki/logger.py` 或等价模块
- `src/core/main.py` / `src/core/coordinator.py` / `src/core/engine.py`（仅为命令或挂点接入）
- `.cc-mini/wiki/entities/**`
- `.cc-mini/wiki/log.md`
- `memory-bank/progress.md`
- `memory-bank/architecture.md`

## 验收标准
1. `/scan` 可用
2. `/digest` 可用
3. `/digest --changed` 可用
4. 至少 5 个核心文件可升级为 digested 页面
5. risk level 达到 critical 时，可写出一次最小 snapshot
6. 连续路径失败时不会无休止继续猜测，而会停止并写 deferred issue

## Stop Conditions
1. 如果需要 TaskPack / EditSpec，停止，留到 Phase 3
2. 如果需要 patch / debug，停止，留到 Phase 4
3. 如果需要 archive / reconcile，停止，留到 Phase 5

## Direct Runner Prompt
请只执行 Phase 2。
只实现 scan、digest、digest --changed、状态升级、最小 dehydration、最小 drift check。
不要实现 TaskPack、EditSpec、patch、debug、archive/reconcile。
完成后只输出：
1. 新增/修改了哪些文件
2. 是否通过本 Phase 验收
3. 哪些内容被刻意延后
