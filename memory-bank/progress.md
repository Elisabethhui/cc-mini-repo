# Progress

## 项目
CC-MINI Wiki-Strict 模式升级项目

## 当前阶段
Step 4 已完成：已定义 Wiki 目录结构与页面模板。

## 已完成内容
1. 已整理并确认项目最小输入。
2. 已生成核心设计文档：`game-design-document.md`。
3. 已生成技术栈文档：`tech-stack.md`。
4. 已生成分步实施计划：`implementation-plan.md`。
5. 已创建 `memory-bank/` 目录并放入上述核心文档。
6. 已创建 `progress.md` 与 `architecture.md` 作为后续迭代记录入口。
7. 已创建 `memory-bank/schema/` 目录与规则层文件骨架：
   - `AGENTS.md`
   - `conventions.md`
   - `digest_policy.md`
   - `conflict_policy.md`
   - `taskpack_policy.md`
   - `watchdog_policy.md`
8. 已对 Step 2 做边界增强修订，明确：
   - 哪些问题属于本步必须拍板的规则级问题
   - 哪些问题属于后续步骤再决定的实现级问题
   - TaskPack、页面状态、frontmatter、Watchdog 的制度边界
9. 已完成 Step 3，在 `conventions.md` 中固化统一 frontmatter 规范，包括：
   - 正式页面统一采用 YAML frontmatter
   - 必须带 frontmatter 的页面范围
   - 当前阶段可豁免完整 frontmatter 的页面范围
   - 通用字段集合、字段含义和允许值
   - 必填 / 选填规则
   - entity / concept / report / taskpack 的最小元数据样例

## 当前验证结果
- `conventions.md` 已明确 frontmatter 的唯一标准格式为 YAML frontmatter。
- 已区分“受管理正式页面”与“当前阶段可豁免页面”。
- 已定义 `type`、`status`、`domain`、`confidence` 等关键字段的允许值。
- 已定义面向不同页面类型的最小 frontmatter 要求。
- 规范已足以支撑后续 watcher、lint、archive、reconcile 使用同一套元数据契约。

## 本阶段遗留但刻意延后的问题
以下问题不是遗漏，而是有意延后到后续实现步骤：
1. frontmatter 解析器与字段校验器如何实现。
2. frontmatter 缺项时，lint 报错格式与修复策略如何设计。
3. frontmatter 自动迁移脚本是否需要，以及何时引入。
4. 运行时页面对象在代码中如何建模。
5. TaskPack 正文结构与 EditSpec 嵌套方式的最终落盘方案。

## 本阶段遇到的问题
- Step 3 容易滑向“实现元数据系统”，例如提早讨论解析器、校验器、自动补全和自动迁移。
- 已通过边界约束解决：本步只固化元数据契约，不处理解析器与自动化实现。

## Step 4 完成情况

### 已做的改动
1. **新建文件**：
   - `memory-bank/wiki-layout.md` - Wiki 目录结构规范
   - `memory-bank/templates/` 目录
   - `memory-bank/templates/entity-template.md`
   - `memory-bank/templates/concept-template.md`
   - `memory-bank/templates/comparison-template.md`
   - `memory-bank/templates/report-template.md`
   - `memory-bank/templates/source-note-template.md`
   - `memory-bank/templates/taskpack-template.md`
   - `memory-bank/templates/lint-report-template.md`
   - `memory-bank/templates/archive-record-template.md`

2. **更新文件**：
   - `memory-bank/progress.md` - 更新为 Step 4 已完成
   - `memory-bank/architecture.md` - 将在后续更新

### 文件内容说明
- `memory-bank/wiki-layout.md` 定义了 9 个一级目录：
  - `index.md` - Wiki 首页
  - `log.md` - 运行日志
  - `entities/` - 实体知识目录
  - `concepts/` - 概念知识目录
  - `comparisons/` - 对比知识目录
  - `reports/` - 报告知识目录
  - `source_notes/` - 来源笔记目录
  - `taskpacks/` - 任务包目录
  - `lint_reports/` - Lint 报告目录
  - `archive/` - 归档目录

- 8 个模板文件都包含：
  - YAML frontmatter（符合 conventions.md 规范）
  - 通用页面结构
  - 针对各页面类型的专属字段
  - 示例内容占位符

### 验证标准
1. ✅ `memory-bank/wiki-layout.md` 文件存在且内容完整
2. ✅ `memory-bank/templates/` 目录存在
3. ✅ 模板文件数量 = 9（8 个模板文件 + 目录）
4. ✅ 所有模板使用 YAML frontmatter
5. ✅ `memory-bank/progress.md` 已更新为 Step 4 完成状态

### 遗留问题（刻意见后）
以下问题已在 Step 4 阶段刻意延后，将在后续步骤中处理：
1. frontmatter 解析器与字段校验器的具体实现
2. frontmatter 缺项时的 lint 报错格式与修复策略
3. frontmatter 自动迁移脚本
4. 运行时页面对象的代码建模
5. TaskPack 正文结构与 EditSpec 嵌套方式的落盘方案

### 下一步建议
**Step 5：实现目录结构与模板**

基于 Step 4 产出的目录结构与模板，开始实现：
1. 创建 `.cc-mini/wiki/` 运行时目录结构
2. 实现模板页面生成器
3. 更新 `memory-bank/architecture.md` 记录新增文件职责

**边界约束：**
- 只修改 exec pack 允许的文件（新建或更新）
- 不写 Python 业务逻辑
- 不修改 schema policy 文件
- 不处理 policy 裁决冲突
- 不进入 Step 6 及后续步骤

## 后续开发者注意事项
1. 每次开始新步骤前，先完整阅读 `memory-bank/` 下全部文件。
2. 每次只做一个步骤；当前步骤验证未通过前，不要提前进入下一步。
3. 每完成一个重大步骤，都要回写本文件，记录：
   - 做了什么
   - 如何验证
   - 有什么遗留问题
   - 下一步建议
4. 今后每一步都应明确：
   - 本步目标
   - 本步核心边界
   - 本步明确不处理什么
   - 本步影响哪些文件
   - 本步完成后的验证标准
