> Deprecated: 该文件基于旧 Step 4 设计，不再作为后续执行依据。
> 自 v2.0 起，后续阶段以 system-design-v2 与 phases/ 下的 Phase 文件为准。
# Step 4 Exec Pack

## Current Step
Step 4: 定义目录结构与页面模板

## Goal
在不写业务代码的前提下，创建 Wiki 目录规范文件和页面模板文件，为后续实现做准备。

## Read First
1. `memory-bank/implementation-plan.md`
2. `memory-bank/schema/AGENTS.md`
3. `memory-bank/schema/conventions.md`
4. `memory-bank/progress.md`
5. `memory-bank/architecture.md`

## In Scope
只允许做以下事情：
1. 创建 `memory-bank/wiki-layout.md`
2. 创建 `memory-bank/templates/`
3. 创建模板文件：
   - `entity-template.md`
   - `concept-template.md`
   - `comparison-template.md`
   - `report-template.md`
   - `source-note-template.md`
   - `taskpack-template.md`
   - `lint-report-template.md`
   - `archive-record-template.md`
4. 模板 frontmatter 必须遵守 `memory-bank/schema/conventions.md`
5. 更新 `memory-bank/progress.md`
6. 更新 `memory-bank/architecture.md`

## Out of Scope
严禁做以下事情：
1. 不实现 `.cc-mini/wiki/` 的运行时代码
2. 不实现 ingest / digest / lint / archive / reconcile 功能
3. 不修改 `taskpack_policy.md`、`conflict_policy.md`、`watchdog_policy.md`
4. 不处理 policy 裁决冲突
5. 不写任何 Python 业务代码
6. 不进入 Step 5

## Directory Layout To Specify
在 `memory-bank/wiki-layout.md` 中说明未来 `.cc-mini/wiki/` 应包含：
- `index.md`
- `log.md`
- `schema/`
- `entities/`
- `concepts/`
- `comparisons/`
- `reports/`
- `source_notes/`
- `taskpacks/`
- `lint_reports/`
- `inbox/`
- `archive/`

## Template Requirements
### General Rules
1. 每个模板都应为 Markdown 文件
2. 每个模板都应带 YAML frontmatter
3. frontmatter 字段必须与 Step 3 保持一致
4. 模板正文只放结构骨架，不放实现说明
5. 模板示例值应清晰、最小、可复用

### Template Body Expectations
- Entity: Role / Key Symbols / Execution Flow / Dependencies / Edge Cases / Hotspots / Suggested Edit Entry Points / Source Trace
- Concept: Purpose / Scope / Core Idea / Related Pages / Limits / Source Trace
- Comparison: Compared Objects / Similarities / Differences / Recommendation / Source Trace
- Report: Summary / Findings / Risks / Next Actions / Source Trace
- Source Note: Source Summary / Key Excerpts / Reliability / Notes
- TaskPack: Task Summary / Target Files / Primary Symbols / Related Symbols / Hotspots / Constraints / Verify Checklist
- Lint Report: Scope / Findings / Severity / Suggested Fixes
- Archive Record: Archived From / Reason / Historical Notes / Supersession Links

## How To Handle The Previously Reported Policy Issues
对于之前发现的 `taskpack_policy` / `conflict_policy` / `watchdog_policy` 边界模糊：
- 本步不要改这些 policy 文件
- 只在 `progress.md` 的“后续待细化项”里记录
- 不要把这些问题升级成 Step 4 阻塞

## Expected Output
完成后只输出：
1. 新增了哪些文件
2. 修改了哪些文件
3. Step 4 是否通过验证
4. 还有哪些内容被刻意延后

## Acceptance Checks
1. `memory-bank/wiki-layout.md` 存在
2. `memory-bank/templates/` 存在
3. 模板文件数量 >= 8
4. 所有模板使用 YAML frontmatter
5. `progress.md` 已记录 Step 4 完成
6. `architecture.md` 已记录新增文件职责

## Stop And Ask Conditions
如果出现以下情况，必须停止并提问：
1. 需要新增 frontmatter 字段
2. 需要修改已有字段语义
3. 需要决定模板与运行时代码的绑定方式
4. 需要改动 Step 2 或 Step 3 的规则文件
