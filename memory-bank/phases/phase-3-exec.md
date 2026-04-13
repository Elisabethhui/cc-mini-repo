# Phase 3 Exec — 任务预热与结构化计划

## 前置条件
- Phase 2 已通过验收
- digest 页面已可用
- 最小 snapshot 能写出

## 本阶段目标
把“当前任务最小知识包”和“结构化修改计划”正式做出来，让系统在修改前先获得可控的局部熟知识。

## In Scope
1. TaskPack 正式定义与持久化
2. EditSpec 正式定义与持久化
3. `/prime`
4. `wiki_strict` 下 `/plan` 的结构化输出
5. Goal Stack 正式对象
6. Deferred Issue Log
7. Micro-Fork Note
8. TaskPack / EditSpec / Goal Stack / Snapshot 之间的引用关系
9. `flow_state.py` 中：`raw_ast` 先 digest、`stale` 先 reconcile/defer

## Out of Scope
1. 不真正执行 patch
2. 不实现 ASTReadTool
3. 不实现 debug / retry 闭环
4. 不实现 archive / reconcile / query-archive

## 允许修改的文件
- `src/core/plan.py` 或 `plan_manager`
- `src/core/wiki/taskpack.py`
- `src/core/flow_state.py`
- `src/core/engine.py`（仅为 Goal Stack / deferred issue / micro-fork 接入）
- `.cc-mini/wiki/taskpacks/**`
- 可选 `.cc-mini/wiki/reports/deferred-issues/**`
- 可选 `.cc-mini/wiki/reports/micro-forks/**`
- `memory-bank/progress.md`
- `memory-bank/architecture.md`

## 验收标准
1. `/prime` 可用
2. `wiki_strict` 下 `/plan` 输出 TaskPack + EditSpec + Patch Plan
3. TaskPack 持久化可用
4. Deferred Issue Log 可记录越界问题
5. Micro-Fork Note 可记录轻量分叉问题
6. 当前计划不会继续自由散开到别的阶段问题

## Stop Conditions
1. 如果需要真正 patch，停止，留到 Phase 4
2. 如果需要 archive/reconcile，停止，留到 Phase 5

## Direct Runner Prompt
请只执行 Phase 3。
只实现：TaskPack、EditSpec、prime、wiki_strict 下的 plan、Goal Stack、Deferred Issue、Micro-Fork。
不要实现 patch/debug。
如果遇到后续阶段问题，只写 deferred issue，不继续扩写。
完成后只输出：
1. 新增/修改了哪些文件
2. 是否通过本 Phase 验收
3. 哪些内容被刻意延后
