# Step 4 Design

## Current Status
根据你贴回来的 cc-mini 校准输出：
- `memory-bank/` 文件齐全
- `schema/` 文件齐全
- 当前已完成到 Step 3
- 下一步是 Step 4：定义目录结构与页面模板
- 当前边界已确认：不处理 ingest、digest、lint、archive 的代码逻辑

这说明 Step 1–3 现在可以视为**已在 repo 中真实落地**，Step 4 可以正式开始。

## Step 4 Goal
把“未来 Wiki 运行时应该长什么样”以及“不同页面应该长什么样”固定下来，形成后续实现可复用的**目录规范**与**模板规范**。

## Step 4 Core Boundary
本步只做两类事情：
1. 定义 Wiki 顶层目录结构
2. 定义不同页面类型的模板骨架

本步必须产出的是：
- 一个清晰的目录规范文件
- 一组模板文件
- 对 `progress.md` 与 `architecture.md` 的回写

## In Scope
1. 定义 `.cc-mini/wiki/` 的标准目录树
2. 说明每个目录的职责
3. 创建模板文件目录，例如 `memory-bank/templates/`
4. 为以下页面类型创建模板骨架：
   - entity
   - concept
   - comparison
   - report
   - source_note
   - taskpack
   - lint_report
   - archive_record
5. 模板应与 Step 3 的 frontmatter 规范保持一致
6. 更新 `progress.md`
7. 更新 `architecture.md`

## Out of Scope
1. 不实现 `.cc-mini/wiki/` 的运行时代码初始化逻辑
2. 不实现 ingest / digest / lint / archive / reconcile 的代码功能
3. 不实现 frontmatter 解析器或模板渲染器
4. 不处理 TaskPack 与 Conflict Policy 的裁决细节
5. 不处理 Watchdog 与冲突系统的协同代码
6. 不写任何业务逻辑代码

## About The Reported Policy “Conflicts”
你贴回来的 cc-mini 校准结果里，提出了：
- `taskpack_policy.md` 与 `conflict_policy.md` 的边界未完全说明
- `watchdog_policy.md` 与 `conflict_policy.md` 的协同尚未细化

这些点是**真实的后续细化问题**，但**不是 Step 4 的阻塞项**。
原因是：
- Step 4 只负责目录与模板
- 这些问题属于更后面的“冲突裁决细化”和“运行时行为细化”
- 如果在 Step 4 里提前处理，会再次把规则层和实现层混在一起

因此，本步处理方式应为：
- 在 `progress.md` 中记录这些是后续待细化项
- 不在 Step 4 中扩写 `conflict_policy.md`

## Files This Step May Read
- `memory-bank/implementation-plan.md`
- `memory-bank/schema/AGENTS.md`
- `memory-bank/schema/conventions.md`
- `memory-bank/progress.md`
- `memory-bank/architecture.md`

## Files This Step May Modify
- `memory-bank/progress.md`
- `memory-bank/architecture.md`

## Files This Step Should Create
- `memory-bank/wiki-layout.md`
- `memory-bank/templates/entity-template.md`
- `memory-bank/templates/concept-template.md`
- `memory-bank/templates/comparison-template.md`
- `memory-bank/templates/report-template.md`
- `memory-bank/templates/source-note-template.md`
- `memory-bank/templates/taskpack-template.md`
- `memory-bank/templates/lint-report-template.md`
- `memory-bank/templates/archive-record-template.md`

## Acceptance Criteria
只有同时满足以下条件，Step 4 才算完成：
1. `memory-bank/wiki-layout.md` 存在，并清楚说明未来 `.cc-mini/wiki/` 的目录结构和职责
2. `memory-bank/templates/` 目录存在
3. 至少 8 个模板文件存在
4. 模板中的 frontmatter 与 Step 3 一致
5. 模板正文结构能覆盖后续主要页面用途
6. `progress.md` 已记录 Step 4 完成情况
7. `architecture.md` 已记录新增模板文件与 layout 文件职责

## Stop-And-Ask Conditions
出现以下情况必须停下来，不要继续猜：
1. 需要引入新的页面类型，而现有 Step 3 没有覆盖
2. 需要修改 Step 3 的 frontmatter 规则
3. 需要把模板直接绑定到某个 Python 模块或运行时系统
4. 需要处理 TaskPack 与 Conflict Policy 的制度裁决
