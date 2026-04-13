# Conventions

## 文档目的
本文件定义 Wiki 和配套文档的命名、结构、页面元数据、更新方式与最小一致性要求，避免后续实现出现格式漂移。

## 适用范围
- 适用于 Wiki 页面、TaskPack 页面、报告页、规则页及相关索引页。
- 适用于后续 `.cc-mini/wiki/` 运行时目录与当前 `memory-bank/` 中的规则文档。

## 不适用范围
- 不规定某个具体模块的实现逻辑。
- 不定义 digest 的执行策略细节。
- 不定义冲突裁决细节。
- 不决定运行时 Python 数据结构应使用何种类型系统。

## Step 3 的核心边界（本步必须拍板）
本步只解决 **“页面元数据契约”**，不解决“元数据系统实现”。

### 本步必须确定什么
1. 哪些页面必须带 frontmatter。
2. frontmatter 使用什么格式。
3. 通用字段有哪些。
4. 哪些字段必填，哪些字段选填。
5. 字段允许的取值范围和基础约束。
6. 不同页面类型的最小元数据要求。
7. 哪些页面当前阶段可以豁免完整 frontmatter。

### 本步明确不处理什么
1. 不实现 frontmatter 解析器。
2. 不实现 frontmatter 校验器。
3. 不实现 frontmatter 自动补全或自动迁移脚本。
4. 不决定运行时 Python 模型使用 `dataclass`、`pydantic` 还是 `dict`。
5. 不决定 lint 在代码中如何逐字段报错。
6. 不决定 archive / reconcile 的具体执行算法。

## 命名约定
1. 文件名使用小写英文加连字符或下划线，避免空格。
2. 目录名应体现页面类型或职责，而不是临时任务名。
3. 页面命名应优先稳定、可复用、可搜索，不用一次性描述句。

## 目录约定
Wiki 顶层建议固定为：
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

## 文档规则层与运行时数据结构是两层概念（新增）
1. `memory-bank/schema/*.md` 与未来 `.cc-mini/wiki/schema/*.md` 属于**规则文档层**。
2. Python 中的 `dataclass`、`pydantic`、普通 `dict` 属于**运行时数据结构层**。
3. TaskPack / EditSpec 的持久化文件格式，属于**落盘表示层**。
4. 这三层可以相关，但不能混为一谈。
5. 当讨论“schema”时，必须先明确是在说：
   - 规则文档 schema
   - 代码类型 schema
   - 持久化文件 schema

## Frontmatter 总体约定（Step 3 定稿）

### 1. 唯一标准格式
后续所有 **正式 Wiki 页面** 应优先使用 **YAML frontmatter**。

标准形式：

```md
---
key: value
list_field:
  - item1
  - item2
---
```

当前阶段不采用：
- JSON frontmatter
- 单独 metadata sidecar 文件
- 自定义 `.schema` 或 `.meta` 文件

### 2. 哪些页面必须带 frontmatter
以下页面类型在进入正式 Wiki 后，默认都应带 frontmatter：
- `entities/*`
- `concepts/*`
- `comparisons/*`
- `reports/*`
- `source_notes/*`
- `taskpacks/*`
- `lint_reports/*`
- `archive/*`

### 3. 当前阶段可豁免的页面
以下页面在当前阶段允许不强制带完整 frontmatter：
- `index.md`
- `log.md`
- `schema/*.md`
- `progress.md`
- `architecture.md`

> 说明：这些页面目前主要承担导航、规则和项目记录职责，不直接进入核心状态机。

## 时间与列表字段格式约定
1. 时间字段统一使用 ISO 8601 字符串。
2. 有时区时推荐使用 UTC，例如：`2026-04-10T08:30:00Z`。
3. 仅日期场景允许使用 `YYYY-MM-DD`，但同一字段在同一类页面中应保持一致。
4. 所有多值字段统一使用 YAML 列表，不使用逗号拼接字符串。
5. 空列表使用 `[]`，不要用空字符串代替。

## 通用字段定义（统一元数据契约）
以下字段是 Step 3 固化的统一字段集合。并非所有页面都必须使用全部字段，但字段含义和取值范围在项目内应保持一致。

### A. 基础身份字段
- `type`：页面类型。
- `title`：页面标题或短名称。
- `status`：页面状态。
- `domain`：页面所属领域。
- `tags`：标签列表。

### B. 来源与追踪字段
- `source_ids`：来源标识列表。
- `repo`：代码仓库名。
- `branch`：分支名。
- `commit`：提交哈希。
- `updated_at`：页面最近更新时间。
- `validated_at`：最近一次人工或程序确认时间。
- `confidence`：当前页面可信度。

### C. 关系字段
- `supersedes`：本页替代了哪些旧页面。
- `superseded_by`：本页被哪些新页面替代。
- `related_pages`：相关页面列表。
- `goal_refs`：关联的 Goal Stack 引用（v2.0 新增）。
- `snapshot_refs`：关联的 Context Snapshot 引用（v2.0 新增）。
- `deferred_issue_refs`：关联的 Deferred Issue 引用（v2.0 新增）。

### D. 任务类字段
- `task_id`：任务包唯一标识。
- `mode`：执行模式，例如 `standard` / `wiki_strict`。
- `target_files`：目标文件列表。
- `primary_symbols`：主要目标符号列表。

## 字段取值约束（本步定稿）

### 1. `type` 允许值
统一允许值：
- `entity`
- `concept`
- `comparison`
- `report`
- `source_note`
- `taskpack`
- `lint_report`
- `archive_record`

### 2. `status` 允许值
统一允许值：
- `raw_ast`
- `partially_digested`
- `digested`
- `stale`
- `historical`
- `superseded`

> 说明：本步只统一状态名，不在本步写出完整状态机实现。

### 3. `domain` 建议值
当前阶段建议值：
- `code`
- `docs`
- `module`
- `paper`
- `runtime`
- `process`
- `project`

### 4. `confidence` 允许值
- `low`
- `medium`
- `high`

### 5. v2.0 新增字段说明

#### `goal_refs`
- **用途**：指向当前任务相关的 Goal Stack 页面或标识。
- **适用页面**：taskpack、进入核心状态机的任务型页面。
- **格式**：YAML 列表，例如 `["goal-2026-0411-001"]`。
- **必填性**：当页面与具体执行任务相关时建议填写。

#### `snapshot_refs`
- **用途**：指向当前任务关联的 Context Snapshot。
- **适用页面**：taskpack、debug 记录、retry 状态页。
- **格式**：YAML 列表，例如 `["snap-2026-0411-001"]`。
- **必填性**：当任务经历过 checkpoint 或 OOM 恢复后建议填写。

#### `deferred_issue_refs`
- **用途**：指向因阶段边界而被延后处理的问题。
- **适用页面**：taskpack、plan 记录、任何标记了后续问题的页面。
- **格式**：YAML 列表，例如 `["issue-2026-0411-001"]`。
- **必填性**：当页面记录了非当前阶段处理的问题时建议填写。

## 必填 / 选填规则（Step 3 定稿）

### 1. 所有“受管理正式页面”的最小必填字段
以下字段适用于绝大多数正式页面：
- `type`
- `title`
- `updated_at`

### 2. 所有“进入核心状态机的知识页面”必须额外具备
适用页面：
- `entity`
- `concept`
- `comparison`
- `report`
- `source_note`

额外必填：
- `status`
- `tags`

### 3. 来源驱动页面的条件必填字段
当页面内容来自代码仓库、原始文档、论文或外部材料时，应补充：
- `source_ids`

当页面明确描述代码仓库内容时，应尽量补充：
- `repo`
- `branch`
- `commit`

### 4. 高置信度知识页面的建议字段
当页面要作为后续 patch、review 或 debug 的直接依据时，建议补充：
- `validated_at`
- `confidence`

### 5. TaskPack 页面最小必填字段
适用 `type: taskpack` 页面：
- `type`
- `title`
- `task_id`
- `mode`
- `updated_at`
- `target_files`
- `primary_symbols`

> 说明：TaskPack 的正文结构、EditSpec 的嵌套方式和最终落盘组织，留到后续步骤处理。

### 6. Archive 页面最小必填字段
适用 `type: archive_record` 页面：
- `type`
- `title`
- `updated_at`
- `status`

其中 `status` 一般应为：
- `historical`
- 或 `superseded`

### 7. Lint Report 页面最小必填字段
适用 `type: lint_report` 页面：
- `type`
- `title`
- `updated_at`

## 不同页面类型的最小 frontmatter 要求

### A. Entity 页面
```yaml
---
type: entity
title: engine-coordinator
status: raw_ast
domain: code
source_ids:
  - SRC-2026-0409-001
repo: cc-mini
branch: main
commit: abc1234
updated_at: 2026-04-10T08:30:00Z
validated_at: 2026-04-10T09:00:00Z
confidence: medium
tags:
  - engine
  - coordinator
related_pages: []
supersedes: []
superseded_by: []
---
```

### B. Concept 页面
```yaml
---
type: concept
title: wiki-strict-task-priming
status: digested
domain: process
source_ids:
  - SRC-2026-0409-PLAN
updated_at: 2026-04-10T08:30:00Z
validated_at: 2026-04-10T09:00:00Z
confidence: high
tags:
  - taskpack
  - priming
related_pages: []
supersedes: []
superseded_by: []
---
```

### C. Report 页面
```yaml
---
type: report
title: digest-gap-analysis
status: historical
domain: project
source_ids:
  - SRC-2026-0409-REPORT
updated_at: 2026-04-10T08:30:00Z
confidence: medium
tags:
  - analysis
  - digest
related_pages: []
supersedes: []
superseded_by: []
---
```

### D. TaskPack 页面
```yaml
---
type: taskpack
title: patch-engine-submit-guard
task_id: TP-2026-0410-001
mode: wiki_strict
updated_at: 2026-04-10T08:30:00Z
target_files:
  - src/core/engine.py
primary_symbols:
  - Engine.submit
related_pages:
  - entities/code/engine.md
tags:
  - patch
  - guard
---
```

## 页面状态约定（初版）
允许的标准状态：
- `raw_ast`
- `partially_digested`
- `digested`
- `stale`
- `historical`
- `superseded`

## 页面结构约定（初版）
正式页面应优先包含：
1. Role / Purpose
2. Scope
3. Key Content
4. Dependencies / Related Pages
5. Risks / Limits
6. Source Trace

## 更新约定
1. 规则先定，再写实现。
2. 重大变更后更新 `progress.md` 与 `architecture.md`。
3. 当页面事实来源变化时，先标注状态，再决定是否 digest / reconcile。
4. 无来源的高风险结论不得写入高置信度页面。

## 质量约定
1. 一个文件应只有一个主职责。
2. 规则文件必须能清楚回答：它约束什么，不约束什么。
3. 模板和约定应服务后续自动化，而不是增加无意义格式负担。
4. 本步只固化元数据契约，不提前锁死运行时实现细节。
5. 未来若新增字段，必须遵循：
   - 先说明新增字段解决什么问题
   - 再说明适用页面范围
   - 再说明是否必填
