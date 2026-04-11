# Architecture

## 文档目的
本文件用于记录 **CC-MINI Wiki-Strict 模式升级项目** 当前的文档结构、文件职责和后续新增模块的作用说明。

当前版本主要覆盖 **Memory Bank 初始化阶段**、**Step 2 规则层固化阶段** 与 **Step 3 frontmatter 规范定稿阶段** 的文件职责，后续每当新增代码文件、规则文件、Wiki 页面模板或运行流程模块时，都必须持续补充本文件。

---

## 一、当前目录结构（当前阶段）

```text
memory-bank/
  game-design-document.md
  tech-stack.md
  implementation-plan.md
  progress.md
  architecture.md
  schema/
    AGENTS.md
    conventions.md
    digest_policy.md
    conflict_policy.md
    taskpack_policy.md
    watchdog_policy.md
```

---

## 二、当前文件职责

### 1. `memory-bank/game-design-document.md`
**职责：**
- 记录项目的核心愿景、目标、非目标、系统分层与工作流。
- 定义为什么要做 `wiki_strict`，以及 MVP 的边界。
- 作为所有后续实现的“意图来源”。

**当前作用：**
- 约束项目不能偏离“双模式并存、Wiki-first、局部 patch、控制 OOM”这条主线。

---

### 2. `memory-bank/tech-stack.md`
**职责：**
- 定义本项目的推荐技术栈与工程组织方式。
- 说明为什么当前阶段优先选择 Python、Markdown、Git、tree-sitter/AST、watchdog、pytest 等方案。
- 明确“最简单但最健壮”的技术选型原则。

**当前作用：**
- 防止后续开发过程中引入不必要的重型基础设施。
- 统一技术口径，避免多人/多轮实现时出现技术栈漂移。

---

### 3. `memory-bank/implementation-plan.md`
**职责：**
- 记录整个项目的分步实施计划。
- 把开发过程拆成小步、可验证、可回写的执行单元。
- 规定每一步完成后必须更新 `progress.md` 和 `architecture.md`。

**当前作用：**
- 作为后续逐步执行的主导航文件。
- 防止实现顺序混乱、跨步开发、先写代码后补规则。

---

### 4. `memory-bank/progress.md`
**职责：**
- 记录项目已完成的步骤、验证结果、问题与下一步建议。
- 为后续新的开发轮次或新的“AI 执行者”提供连续性上下文。

**当前作用：**
- 当前用于记录 Memory Bank 初始化和 Step 2 规则层固化进展。
- 后续每完成一个重大步骤都必须更新。

---

### 5. `memory-bank/architecture.md`
**职责：**
- 记录当前已有文件和后续新增文件的职责。
- 说明各模块之间的关系、边界和依赖。
- 提供“这个文件为什么存在”的解释，帮助后续维护者快速理解工程结构。

**当前作用：**
- 当前覆盖文档启动阶段与规则层阶段。
- 后续会扩展到 `src/core/`、`knowledge/`、`wiki/`、`tools/`、`schema/` 等目录中的实际实现文件。

---

### 6. `memory-bank/schema/AGENTS.md`
**职责：**
- 定义 AI 执行者在本项目中的通用工作纪律。
- 固化“开始前必须读什么、每次只做一步、完成后必须回写”的强规则。
- 新增“先分清规则级问题和实现级问题”的步骤边界约束。

**当前作用：**
- 防止后续执行时把实现细节提前拖入当前步骤。

---

### 7. `memory-bank/schema/conventions.md`
**职责：**
- 定义文档命名、目录约定、页面结构、frontmatter 规范与一致性要求。
- 明确规则文档层、运行时数据结构层、持久化表示层是三件不同的事。

**当前作用：**
- 防止后续把 Markdown 规则文件、Python 类型系统、YAML/JSON 落盘格式混为一谈。
- 作为 Step 3 的 frontmatter 契约来源，统一页面元数据字段、必填规则和页面类型样例。

---

### 8. `memory-bank/schema/digest_policy.md`
**职责：**
- 定义 digest 的作用范围、触发条件、输出要求和状态转换原则。
- 说明页面状态转换可由时间、Git/文件变化、人工命令三类事件触发。

**当前作用：**
- 提前钉住状态机的“触发类别边界”，但不在本步锁死所有实现阈值。

---

### 9. `memory-bank/schema/taskpack_policy.md`
**职责：**
- 定义 TaskPack 的制度身份、最小字段、范围控制和进入 patch 的门槛。
- 说明 TaskPack 与 EditSpec 的分工关系。

**当前作用：**
- 先把 TaskPack 确认为正式且应持久化的对象，再把具体实现细节留到后续步骤。

---

### 10. `memory-bank/schema/conflict_policy.md`
**职责：**
- 定义未来 reconcile / superseded / 冲突裁决相关规则。

**当前作用：**
- 当前作为规则层占位与后续扩展入口。

---

### 11. `memory-bank/schema/watchdog_policy.md`
**职责：**
- 定义 Watchdog 的职责边界与变化监听规则。
- 明确 Watchdog 只负责低成本保守动作，不包揽全部状态触发机制。

**当前作用：**
- 防止把“状态变化来源很多”误解为“全部由 Watchdog 自动执行”。

---

## 三、当前已拍板 vs 延后拍板

### 当前已拍板
1. `standard` 与 `wiki_strict` 必须显式隔离。
2. Wiki 页面优先使用 Markdown + YAML frontmatter。
3. TaskPack 是正式概念，应支持持久化，不只是聊天中的临时文本。
4. 页面状态允许由三类事件触发：时间、Git/文件变化、人工命令。
5. EditSpec 的 target 不应只停留在 file 级，至少要能继续收缩到 symbol / span / anchor。
6. Watchdog 只负责保守监听、stale 标记和排队，不做越权深度总结。

### Step 4 新增拍板内容（Wiki 目录结构与页面模板）
1. **已创建 `memory-bank/wiki-layout.md`**，定义了 Wiki 目录结构规范，包含 9 个一级目录：
   - `index.md` - Wiki 首页，全局导航入口
   - `log.md` - 运行日志，时间线记录
   - `entities/` - 实体知识目录（file.md, function.md, module.md 等）
   - `concepts/` - 概念知识目录
   - `comparisons/` - 对比知识目录
   - `reports/` - 报告知识目录
   - `source_notes/` - 来源笔记目录
   - `taskpacks/` - 任务包目录
   - `lint_reports/` - Lint 报告目录
   - `archive/` - 归档目录

2. **已创建 `memory-bank/templates/` 目录**，包含 8 个页面模板文件：
   - `entity-template.md` - 实体页面模板
   - `concept-template.md` - 概念页面模板
   - `comparison-template.md` - 对比页面模板
   - `report-template.md` - 报告页面模板
   - `source-note-template.md` - 来源笔记模板
   - `taskpack-template.md` - 任务包模板
   - `lint-report-template.md` - Lint 报告模板
   - `archive-record-template.md` - 归档记录模板

3. **所有模板使用 YAML frontmatter**，符合 `conventions.md` 规范。

4. **各模板包含通用字段**：type、name、summary、status、timestamp 等。

5. **各模板包含专属字段**：
   - entity-template: entities 数组（type, name, path, details, code_example 等）
   - concept-template: entities 数组（含 related, references）
   - comparison-template: entities 数组（含 second, conclusion）
   - report-template: findings、remediation 字段
   - source-note-template: content、tag、confidence 字段
   - taskpack-template: tasks、operations 字段
   - lint-report-template: issues 数组、remediation 字段
   - archive-record-template: 关联页面、reason、status 字段

### 明确延后到后续步骤再拍板
1. TaskPack 的 Python 运行时类型使用 `dataclass`、`pydantic` 还是普通 `dict`。
2. TaskPack 与 EditSpec 最终放一个物理文件还是两个物理文件。
3. `taskpacks/` 目录最终按 task_id、file、symbol 还是时间组织。
4. `stale` 的精确时间阈值、巡检频率和自动调度方式。
5. `historical` 与 `superseded` 的精确自动判定算法。
6. `.cc-mini/wiki/` 运行时代码的具体实现（ingest、digest、lint、archive、reconcile）。
7. template 与运行时对象的绑定方式。


## 四、Step 3 新增拍板内容（frontmatter 契约）

### 本步已拍板
1. 正式 Wiki 页面统一采用 Markdown + YAML frontmatter。
2. `entities/`、`concepts/`、`comparisons/`、`reports/`、`source_notes/`、`taskpacks/`、`lint_reports/`、`archive/` 下的正式页面默认必须带 frontmatter。
3. `index.md`、`log.md`、`schema/*.md`、`progress.md`、`architecture.md` 当前阶段可豁免完整 frontmatter。
4. `type`、`status`、`domain`、`confidence` 等关键字段的允许值已统一。
5. 已区分“所有正式页面的最小必填字段”和“不同页面类型的最小元数据要求”。

### 本步明确延后
1. frontmatter 解析器、校验器、自动补全器的实现方式。
2. frontmatter 缺项时 lint 的报错格式与自动修复策略。
3. frontmatter 自动迁移脚本与兼容旧页面的批量转换方案。
4. 运行时如何把 frontmatter 映射为 Python 对象。


---

## 五、后续预计新增的关键目录

以下目录在后续步骤中预计会逐步引入；当前尚未真正落地，只作为规划视图记录：

### 1. Wiki 工作目录
```text
.cc-mini/wiki/
  index.md
  log.md
  schema/
  entities/
  concepts/
  comparisons/
  reports/
  source_notes/
  taskpacks/
  lint_reports/
  inbox/
  archive/
```

**预期职责：**
- 承载 Wiki 中间层、规则层、任务级知识包与长期沉淀内容。

---

### 2. 代码实现目录（规划中）
```text
src/core/
  main.py
  config.py
  coordinator.py
  flow_state.py
  plan.py
  knowledge/
    ingester.py
    watcher.py
  tools/
    ast_read.py
    file_edit.py
  wiki/
    service.py
    ingest.py
    digest.py
    taskpack.py
    archive.py
    lint.py
    reconcile.py
    indexer.py
    logger.py
```

**预期职责：**
- `main.py`：模式入口与生命周期初始化。
- `config.py`：模式与统一配置表达。
- `coordinator.py`：标准模式与 wiki_strict 模式的流程分发。
- `flow_state.py`：状态检查与状态转换约束。
- `plan.py`：TaskPack / EditSpec 等结构化计划能力。
- `knowledge/`：结构摄入与 watcher。
- `tools/`：ASTRead、strict patch 等局部工具能力。
- `wiki/`：Wiki 服务层能力，包括 digest、archive、lint、reconcile 等。

---

## 六、当前架构边界约束

在后续任何文件落地时，都必须遵守以下边界：

1. `standard` 与 `wiki_strict` 必须显式隔离。
2. 不允许把全部新逻辑堆入单个大文件。
3. 任务必须先计划、再定位、再修改、再验证。
4. `Raw Sources` 视为不可变事实层。
5. Wiki 是中间层，不是临时缓存。
6. 修改优先局部 patch，不允许默认整文件重写。
7. Watchdog 只负责 stale 标记与排队，不负责越权深度总结。
8. 每一步都必须先区分“本步该定的规则边界”和“后续再定的实现细节”。

---

## 六、更新规则

后续每当出现以下变化之一，都必须更新本文件：

1. 新增了规则层文件（如 `schema/*.md`）。
2. 新增了可执行模块（如 `ingester.py`、`ast_read.py`）。
3. 新增了新的状态机逻辑或关键数据结构（如 TaskPack、EditSpec）。
4. 新增了新的目录或页面模板。
5. 对已有文件职责发生明显变化。

更新时至少说明：
- 新文件路径
- 文件职责
- 与其他文件的关系
- 为什么需要这个文件
