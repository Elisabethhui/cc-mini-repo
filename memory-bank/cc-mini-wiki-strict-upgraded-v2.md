# CC-MINI Wiki-Strict 模式升级方案与开发计划（v2.0）

版本：v2.0  
日期：2026-04-11  
适用对象：cc-mini 框架二次开发 / 本地 32K 小模型代码助手 / 持久化知识库场景

## 1. 升级目标
在不破坏 `standard` 模式的前提下，升级 `wiki_strict`，重点解决两类新增问题：
1. 上下文临近 OOM 时缺少主动脱水与状态固化
2. 小模型在 plan / modify / debug 过程中容易偏航、失忆、切到别的任务

## 2. v2.0 新增横切能力
### A. Context Safeguard
- token 使用率监控
- OOM 预警
- 上下文脱水（Dehydration）
- Context Snapshot
- Resume from Snapshot

### B. Goal Anchoring & Drift Recovery
- Goal Stack（总目标 / 步骤目标 / 子任务目标 / 当前动作）
- Drift Detector
- Re-anchor Loop
- Deferred Issue Log
- Micro-Fork Note

## 3. v2.0 主线
Goal Anchoring → 结构扫描 → 语义消化 → 任务预热 → 精准定位 → 局部 patch → 局部 debug → Re-anchor → Context Snapshot → Wiki 运维

## 4. 六层结构
### Layer 0：Raw Sources
不可变事实层，只读。

### Layer 1：Structural Ingest
生成 index / raw_ast entities。

### Layer 2：Semantic Digest
局部 digest，升级页面状态。

### Layer 3：Task Priming / Task Pack
压缩当前任务最小知识包。

### Layer 4：Safe Edit / Verify
ASTRead、strict patch、ask_user fallback、verify / retry。

### Layer 5：Compounding LLM Wiki
archive、lint、reconcile、知识复利。

## 5. v2.0 关键设计结论
1. 任何任务都必须先带 Goal Stack。
2. 任何接近 OOM 的会话都必须能生成 Snapshot。
3. 任何连续失败都必须触发 Re-anchor。
4. 任何后续阶段问题都应进入 Deferred Issue，而不是污染当前阶段。
5. 任何 patch 都必须是局部 patch，而不是整文件重写。

## 6. 分阶段路线（概览）
- Phase 0：规则与契约定稿
- Phase 1：模式接入与结构骨架
- Phase 2：语义消化与状态升级
- Phase 3：任务预热与结构化计划
- Phase 4：精准修改与局部 debug
- Phase 5：知识复利闭环
- Phase 6：Obsidian / Git 运维层

## 7. 当前执行建议
由于旧 Step 4 基于 32K 小模型草稿产物，建议项目状态回退到 Step 3，并以本 v2.0 设计为新的总设计依据。
