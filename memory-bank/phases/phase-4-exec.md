# Phase 4 Exec — 精准修改与局部 Debug 闭环

## 前置条件
- Phase 3 已通过验收
- TaskPack / EditSpec / Goal Stack 已可用
- 当前任务已能局部定位

## 本阶段目标
实现“定点读、定点改、定点调”，并在 patch/debug/retry 中加入 Re-anchor 与失败记忆，避免小模型反复跑偏。

## In Scope
1. `ASTReadTool`
2. `file_edit.py` 的 strict patch 模式
3. ask_user fallback
4. patch preview / rollback
5. traceback / stderr 清洗
6. verify / retry loop
7. Re-anchor Loop
8. patch/debug 中的 Drift Detector
9. failed attempts 与 snapshot 在 debug/retry 中的接入

## Out of Scope
1. 不实现 archive / reconcile / query-archive
2. 不实现 Obsidian / Git 深度运维
3. 不做全仓级修改，只做局部 patch

## 允许修改的文件
- `src/core/tools/ast_read.py`
- `src/core/tools/file_edit.py`
- `src/core/engine.py`
- `src/core/flow_state.py`
- `src/core/knowledge/dehydrator.py`
- `src/core/session.py`
- `memory-bank/progress.md`
- `memory-bank/architecture.md`

## 验收标准
1. ASTReadTool 可按 file+symbol/span/anchor 工作
2. strict patch apply 可用
3. ask_user fallback 可用
4. traceback 清洗可用
5. verify / retry loop 可用
6. 路径错误和重复 patch 失败不会导致无限反复思考
7. 一次小范围 modify/debug 可在不全文读文件的前提下完成

## Stop Conditions
1. 如果需要 archive/reconcile，停止，留到 Phase 5
2. 如果需要 Obsidian/Git 运维，停止，留到 Phase 6

## Direct Runner Prompt
请只执行 Phase 4。
只实现：ASTRead、strict patch、ask_user fallback、traceback 清洗、verify/retry、Re-anchor Loop。
不要实现 archive/reconcile/Obsidian 运维。
必须保持局部修改，不允许整文件重写。
完成后只输出：
1. 新增/修改了哪些文件
2. 是否通过本 Phase 验收
3. 哪些内容被刻意延后
