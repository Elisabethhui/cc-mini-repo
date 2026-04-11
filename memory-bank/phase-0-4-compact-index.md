# Phase 0–Phase 4 精简执行索引

## 使用原则
1. 一次只执行一个 Phase。
2. 不跨阶段混用未开放能力。
3. 后续阶段问题只记录为 deferred issue。
4. 每个 Phase 文档都应可直接喂给 Codex / cc-mini 执行。

## Phase 0
规则层升级：新增 Context Safeguard / Goal Policy / Phase Boundary Policy。

## Phase 1
`wiki_strict` 模式接入、Wiki 目录初始化、token risk monitor 骨架、Goal Stack 占位接入。

## Phase 2
`/scan`、`/digest`、`/digest --changed`、页面状态升级、最小 dehydration + snapshot。

## Phase 3
TaskPack、EditSpec、`/prime`、`/plan`、Goal Stack 正式对象、Deferred Issue、Micro-Fork。

## Phase 4
ASTRead、strict patch、ask_user fallback、traceback 清洗、verify/retry、Re-anchor Loop。

## 当前推荐起点
项目当前建议从 **Phase 0** 重新开始，而不是继续使用旧 Step 4 产物。
