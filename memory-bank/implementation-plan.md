# Implementation Plan

> 说明：本文件是为“AI 开发执行者”准备的逐步实施计划。虽然沿用 `implementation-plan.md` 命名，但其实际内容对应 **CC-MINI Wiki-Strict 模式升级项目**。本计划严格遵守以下原则：**小步推进、每步都可验证、先基础闭环再扩展、文档先行、禁止在本计划中包含代码**。

---

## 1. 执行目标

在不破坏 cc-mini 原有 `standard` 模式的前提下，分阶段引入 `wiki_strict` 模式，并逐步打通以下最小闭环：

1. 模式切换可用
2. Wiki 骨架可生成
3. 页面状态可维护
4. 局部 digest 可执行
5. TaskPack / EditSpec 可生成
6. 局部读取与局部 patch 可执行
7. Review / Modify / Debug 至少各能跑通一个最小场景
8. Wiki 能进行最基础的持续维护与沉淀

---

## 2. 全局执行规则（AI 开发者必须遵守）

### 2.1 每次开始工作前必须阅读

1. `/memory-bank/game-design-document.md`
2. `/memory-bank/tech-stack.md`
3. `/memory-bank/implementation-plan.md`
4. `/memory-bank/progress.md`
5. `/memory-bank/architecture.md`

### 2.2 严格的执行边界

1. 一次只执行 **一个步骤**。
2. 在当前步骤的验证没有通过前，**不得开始下一步**。
3. 每完成一个步骤后，必须更新：
   - `progress.md`
   - `architecture.md`
4. 所有实现都必须遵守：
   - 模块化
   - 多文件
   - 单一职责
   - 禁止 monolith
5. `wiki_strict` 的新增逻辑必须与 `standard` 显式隔离。
6. 修改代码时，优先做局部 patch，不做整文件重写。
7. 如果信息不足以安全修改，则先补 digest 或补定位，不允许“猜着改”。

### 2.3 文档更新要求

每个重大步骤完成后：

- `progress.md` 记录：
  - 做了什么
  - 验证结果
  - 遇到的问题
  - 下一步建议

- `architecture.md` 记录：
  - 新增/修改了哪些文件
  - 每个文件的职责
  - 这些文件与现有模块的关系

---

## 3. 交付策略

本计划按以下顺序推进：

1. **规则先行**：先固定目录、状态、模板和策略，避免边做边改定义。
2. **骨架优先**：先让 `wiki_strict` 能启动并生成骨架。
3. **语义补全**：再让 digest 真正可用。
4. **任务级预热**：再引入 TaskPack / EditSpec。
5. **精准修改**：最后补局部 patch、debug 和 verify 闭环。
6. **长期运维**：最后补 archive / reconcile / lint / Git / Obsidian 相关能力。

---

## 4. 里程碑拆分

- **Milestone A**：规则层完成
- **Milestone B**：模式与骨架完成
- **Milestone C**：digest 能用
- **Milestone D**：TaskPack 与 `/plan` 可用
- **Milestone E**：局部 patch 与 debug 可用
- **Milestone F**：Wiki 运维闭环可用

---

# 5. 分步实施计划

---

## Step 1：创建 memory-bank 基础文件并确认命名约定

### 目标
建立统一的 memory-bank 目录与基础文档文件，避免后续工作缺少固定上下文入口。

### 需要做的事
1. 在项目根目录创建 `memory-bank/`。
2. 放入以下文件：
   - `game-design-document.md`
   - `tech-stack.md`
   - `implementation-plan.md`
   - `progress.md`
   - `architecture.md`
3. 确认所有文件名与后续提示词一致。
4. 在 `progress.md` 和 `architecture.md` 中写入初始占位说明。

### 验证
1. 确认目录存在且文件齐全。
2. 确认 AI 执行者能够通过固定路径读取这五个文件。
3. 确认命名与后续提示词完全一致，没有别名冲突。

### 完成标准
- memory-bank 目录完整存在。
- 五个核心文件可被稳定读取。

---

## Step 2：固化 schema 目录与规则层文件骨架

### 目标
把规则从“聊天里的描述”变成“仓库里的事实”，避免后续实现反复改口径。

### 需要做的事
1. 在 Wiki 根目录下创建 `schema/`。
2. 新建以下规则文件：
   - `AGENTS.md`
   - `conventions.md`
   - `digest_policy.md`
   - `conflict_policy.md`
   - `taskpack_policy.md`
   - `watchdog_policy.md`
3. 先只写结构化规则，不写实现细节。
4. 明确每个规则文件的用途和作用范围。

### 验证
1. 确认规则文件都存在。
2. 确认每个文件都能回答“这个规则管什么，不管什么”。
3. 检查是否存在重复定义或冲突定义。

### 完成标准
- 规则层文件齐全。
- 后续开发不再需要反复重新定义核心概念。

---

## Step 3：定义统一 frontmatter 规范

### 目标
固定 Wiki 页面元数据格式，为状态机、lint、reconcile 和 archive 奠定基础。

### 需要做的事
1. 在 `conventions.md` 中定义统一 frontmatter 字段。
2. 明确哪些字段是必填，哪些字段是选填。
3. 明确字段的取值约束，例如页面类型、状态、时间字段、引用字段。
4. 给出 entity、concept、report 等页面类型的最小元数据要求。

### 验证
1. 用至少三类页面样例检查规范是否足够表达。
2. 检查规范是否支持 `raw_ast`、`digested`、`stale`、`historical`、`superseded`。
3. 检查后续 watcher、lint、archive 是否都能依赖这些字段工作。

### 完成标准
- frontmatter 规范稳定。
- 页面状态与追踪字段可支撑后续流程。

---

## Step 4：定义目录结构与页面模板

### 目标
固定 Wiki 的目录与页面模板，确保不同类型的知识沉淀到正确位置。

### 需要做的事
1. 创建 Wiki 顶层目录结构。
2. 至少建立以下目录：
   - `entities/`
   - `concepts/`
   - `comparisons/`
   - `reports/`
   - `source_notes/`
   - `taskpacks/`
   - `lint_reports/`
   - `inbox/`
   - `archive/`
3. 为 entity 页面定义统一模板。
4. 为 taskpack 页面定义统一模板。
5. 为 report / archive 页面定义统一模板。

### 验证
1. 随机创建 1 个 entity 页面、1 个 taskpack 页面、1 个 report 页面，检查模板可用性。
2. 确认模板能覆盖角色、流程、依赖、风险、入口、验证建议等信息。
3. 确认目录划分不会导致内容去向模糊。

### 完成标准
- 目录结构清晰。
- 页面模板可直接投入后续实现使用。

---

## Step 5：明确状态机与状态转换规则

### 目标
让页面状态与任务状态都有统一解释，避免后续流程失控。

### 需要做的事
1. 定义页面状态的语义：
   - `raw_ast`
   - `partially_digested`
   - `digested`
   - `stale`
   - `historical`
   - `superseded`
2. 明确每种状态的进入条件和退出条件。
3. 明确 `raw_ast`、`stale` 页面在任务中的限制。
4. 明确何时允许进入 patch 阶段，何时必须先 digest / reconcile。

### 验证
1. 用 review、modify、debug 三类任务各做一次状态推演。
2. 检查是否存在“未经 digest 直接改代码”的漏洞。
3. 检查 stale 页面是否会被误当成可信摘要使用。

### 完成标准
- 状态定义可驱动流程分支。
- 后续 `flow_state.py` 有明确落地依据。

---

## Step 6：给 `main.py` 接入 `wiki_strict` 模式开关

### 目标
让系统能够在入口层识别并切换 `wiki_strict` 模式。

### 需要做的事
1. 为主入口增加 `--mode` 能力。
2. 支持至少两个明确值：
   - `standard`
   - `wiki_strict`
3. 为 `wiki_strict` 增加独立初始化分支。
4. 确保未指定时的默认行为符合当前系统预期。

### 验证
1. 使用默认模式启动，确认现有流程不被破坏。
2. 使用 `wiki_strict` 启动，确认系统能进入新模式初始化逻辑。
3. 检查错误模式值时是否有清晰提示。

### 完成标准
- 模式开关可用。
- `standard` 与 `wiki_strict` 入口行为隔离。

---

## Step 7：在 `config.py` 中固化 RunMode 与模式读取逻辑

### 目标
避免模式判断散落在项目中，统一配置来源与模式匹配逻辑。

### 需要做的事
1. 定义统一的 RunMode 表达方式。
2. 提供读取、校验、比较模式的统一逻辑。
3. 确保 session 层与主入口共享同一模式定义。
4. 禁止字符串魔法值在多个模块重复出现。

### 验证
1. 检查所有模式判断是否都能收敛到统一定义。
2. 检查新增模式时是否只需改动少量位置。
3. 检查 `standard` 逻辑未被隐式污染。

### 完成标准
- 模式配置集中管理。
- 后续 coordinator / flow_state / plan 可稳定复用。

---

## Step 8：建立 Wiki 生命周期初始化流程

### 目标
让 `wiki_strict` 模式启动时能够自动完成最基础的 Wiki 环境准备。

### 需要做的事
1. 初始化 Wiki 根目录。
2. 自动创建核心文件：
   - `index.md`
   - `log.md`
   - `inbox/digest_queue.md`
   - `inbox/reconcile_queue.md`
3. 如果目录和文件已存在，则保持幂等。
4. 记录首次初始化和重复启动的行为规则。

### 验证
1. 在空目录下启动，确认可自动生成基础文件。
2. 在已有目录下重复启动，确认不会覆盖现有内容。
3. 检查初始化失败时是否有明确错误反馈。

### 完成标准
- `wiki_strict` 启动后有稳定的 Wiki 工作目录。
- 初始化过程可重复执行而不破坏现有数据。

---

## Step 9：实现 Structural Ingest 的最小骨架

### 目标
先让系统具备“搭骨架”的能力，而不是一开始追求完整语义理解。

### 需要做的事
1. 新建 `knowledge/ingester.py`。
2. 支持读取项目目录结构。
3. 支持提取基础文件清单与 symbol 清单。
4. 输出 `index.md`。
5. 为目标文件生成基础 `raw_ast` entity 页面。

### 验证
1. 对一个 demo 项目执行一次结构摄入。
2. 检查是否生成 `index.md`。
3. 检查是否生成至少若干个基础 entity 页面。
4. 检查新生成页面状态是否为 `raw_ast`。

### 完成标准
- Wiki 骨架可自动生成。
- 结构层结果可作为后续 digest 的输入。

---

## Step 10：让 `index.md` 成为可用导航页

### 目标
使 `index.md` 不只是文件清单，而是能承担稳定入口职责。

### 需要做的事
1. 在 `index.md` 中体现顶层目录说明。
2. 展示核心主题和核心入口页面。
3. 展示最近更新与待处理状态入口。
4. 控制页面体量，保持小而稳。

### 验证
1. 新成员只看 `index.md`，是否能快速理解 Wiki 入口。
2. 检查是否存在信息过多、失去导航功能的问题。
3. 检查是否能跳转到核心模块和待处理队列。

### 完成标准
- `index.md` 可以作为全局导航页使用。

---

## Step 11：建立 `log.md` 的 append-only 规则

### 目标
为 ingest、digest、reconcile、archive、重要任务保留时间线记录。

### 需要做的事
1. 定义 `log.md` 的记录格式。
2. 规定哪些事件必须入 log。
3. 明确 log 只能追加，不覆盖历史。
4. 区分系统事件与人工备注。

### 验证
1. 记录至少三种不同类型事件。
2. 检查记录格式是否一致。
3. 检查后续是否容易回放关键变更历史。

### 完成标准
- `log.md` 可作为基本审计时间线使用。

---

## Step 12：接入 watcher，并只实现“标 stale + 入队列”

### 目标
先把 watcher 的职责边界收紧，避免它越权执行重工作。

### 需要做的事
1. 新建 `knowledge/watcher.py`。
2. 监听代码文件与 Wiki 文件变化。
3. 识别受影响页面。
4. 将受影响页面标记为 `stale`。
5. 把后续处理项写入：
   - `digest_queue.md`
   - `reconcile_queue.md`
6. 把事件写入 `log.md`。

### 验证
1. 修改一个被 ingest 过的源文件。
2. 检查对应页面是否被标为 `stale`。
3. 检查队列文件是否追加待处理项。
4. 确认 watcher 没有自动做高成本 digest。

### 完成标准
- watcher 能正常监听并标记 stale。
- watcher 职责没有越界。

---

## Step 13：实现 `/scan` 命令

### 目标
把结构测绘能力变成可调用命令，方便显式刷新骨架。

### 需要做的事
1. 提供 `/scan` 命令入口。
2. 支持对目标目录或项目根执行结构扫描。
3. 将结果写入 `index.md` 和 `raw_ast` entity 页面。
4. 确保该命令不会执行语义 digest。

### 验证
1. 在未执行 `/scan` 前后对比 Wiki 变化。
2. 确认 `/scan` 只更新结构层结果。
3. 检查重复执行时的幂等性与更新行为。

### 完成标准
- 用户可显式触发结构测绘。
- `/scan` 与 `/digest` 职责清晰分离。

---

## Step 14：实现 `/digest` 的最小闭环

### 目标
让系统第一次具备“按需补语义”的能力。

### 需要做的事
1. 提供 `/digest` 命令入口。
2. 支持对单文件执行 digest。
3. 支持对指定 symbol 执行 digest。
4. 将结果写回对应 entity 页面。
5. 从 `raw_ast` 升级为 `partially_digested` 或 `digested`。

### 验证
1. 选一个核心文件执行 digest。
2. 检查 entity 页面是否补充角色、流程、依赖、风险、入口等信息。
3. 检查页面状态是否升级。
4. 检查 digest 结果是否足以支持后续 review 任务。

### 完成标准
- `/digest` 可对目标对象做局部语义消化。

---

## Step 15：实现 `/digest --changed`

### 目标
让系统只围绕最近变更做补充 digest，而不是每次重读大量内容。

### 需要做的事
1. 基于变更范围识别最近受影响的文件或 symbol。
2. 只对这些变化目标执行 digest。
3. 更新对应页面状态与摘要。
4. 记录 digest 来源与变更依据。

### 验证
1. 对一组小范围变更执行该命令。
2. 检查只有相关页面被更新。
3. 检查与全量 digest 相比，影响范围明显缩小。

### 完成标准
- 系统能基于变化进行增量 digest。

---

## Step 16：让 digest 页面达到“可操作”而不仅是“可读”

### 目标
确保 digest 页面真的能指导 Review / Modify / Debug，而不是只写概述。

### 需要做的事
1. 强化 entity 页面模板中的以下字段：
   - Role
   - Key Symbols
   - Execution Flow
   - External Dependencies
   - Edge Cases
   - Hotspots
   - Suggested Edit Entry Points
   - Source Trace
2. 对至少 5 个核心文件完成 digest。
3. 检查这些页面是否具备“指导行动”的能力。

### 验证
1. 随机抽查 5 个 digested 页面。
2. 检查是否能回答“改哪里”“为什么改这里”“会影响什么”。
3. 检查是否仍然需要回头读整文件才能理解。

### 完成标准
- 至少 5 个核心文件达到可操作级 digest。

---

## Step 17：设计 TaskPack 结构

### 目标
让系统能在任务前先压缩“与本次任务最相关的最小知识包”。

### 需要做的事
1. 定义 TaskPack 的固定字段。
2. 至少包含：
   - task summary
   - target file
   - primary symbols
   - related symbols
   - hotspots
   - constraints
   - verify checklist
3. 明确 TaskPack 的大小控制原则。
4. 明确 TaskPack 的来源优先级。

### 验证
1. 针对单函数修改任务，手工模拟生成一个 TaskPack。
2. 检查是否足够支持后续定位与 patch 规划。
3. 检查是否包含过多无关信息。

### 完成标准
- TaskPack 数据结构稳定。
- 能服务单点任务，不膨胀。

---

## Step 18：设计 EditSpec 结构

### 目标
把“改什么、改到哪、不能碰什么、怎么验证”表达清楚。

### 需要做的事
1. 定义 EditSpec 的固定字段。
2. 至少包含：
   - task
   - mode
   - target
   - intent
   - constraints
   - verify
3. 明确 EditSpec 与 TaskPack 的关系。
4. 明确 EditSpec 只表达结构化修改意图，不直接承载整文件代码。

### 验证
1. 选一个 patch 场景，生成一份 EditSpec 草案。
2. 检查是否能明确边界和验证目标。
3. 检查是否仍然存在“范围不清”或“修改意图太模糊”的问题。

### 完成标准
- EditSpec 结构可指导精准修改。

---

## Step 19：实现 `/prime`

### 目标
让系统在真正进入 `/plan` 前，先完成任务级预热。

### 需要做的事
1. 提供 `/prime` 命令入口。
2. 根据用户任务生成 TaskPack。
3. 关联目标 file、symbol、热点与约束。
4. 输出任务预热结果到 `taskpacks/`。

### 验证
1. 用一个 review 任务执行 `/prime`。
2. 用一个 modify 任务执行 `/prime`。
3. 检查生成的 TaskPack 是否聚焦并可复用。

### 完成标准
- `/prime` 可以稳定生成任务级知识包。

---

## Step 20：改造 `/plan`，让 wiki_strict 下输出结构化计划

### 目标
让 `/plan` 从“直接写代码”转为“先出结构化计划”。

### 需要做的事
1. 保持 `standard` 下原行为尽量不变。
2. 在 `wiki_strict` 下让 `/plan` 输出：
   - TaskPack
   - EditSpec
   - Patch Plan
3. 禁止 wiki_strict 下退化为整文件代码生成。
4. 让 `/plan` 对 review / modify / debug 三类任务有不同输出重点。

### 验证
1. 对单函数修改任务执行 `/plan`。
2. 检查输出是否先有定位和边界，再谈 patch。
3. 检查 standard 模式是否未被破坏。

### 完成标准
- `wiki_strict` 下 `/plan` 行为完成重构。

---

## Step 21：在 `flow_state.py` 中接入 Wiki 状态检查

### 目标
让系统在进入执行前先做状态判断，而不是直接改。

### 需要做的事
1. 在计划前增加页面状态检查。
2. 若页面是 `raw_ast`，则要求先 digest。
3. 若页面是 `stale`，则要求先 reconcile 或 diff digest。
4. 只有 `digested` 才允许稳定进入 patch 阶段。

### 验证
1. 用 `raw_ast` 页面触发 modify 任务，确认系统不会直接改代码。
2. 用 `stale` 页面触发任务，确认系统会先要求修复状态。
3. 用 `digested` 页面触发任务，确认可以继续。

### 完成标准
- 状态机真正接入任务流。

---

## Step 22：实现 ASTReadTool

### 目标
让系统能按 file + symbol / span / anchor 做精确读取，避免全文读取。

### 需要做的事
1. 新建 `tools/ast_read.py`。
2. 支持按 file + symbol 读取。
3. 支持按 file + span 读取。
4. 支持按 file + anchor 读取。
5. 对读取范围设置明确上限。

### 验证
1. 读取指定 symbol，确认返回范围准确。
2. 检查读取不会无界扩大到整个文件。
3. 对错误 symbol / 错误 anchor 有清晰失败反馈。

### 完成标准
- 精确读取能力可用。
- OOM 防护开始真正落地。

---

## Step 23：改造 `file_edit.py` 为 strict patch 模式

### 目标
让系统具备安全的局部修改能力。

### 需要做的事
1. 限制 patch 影响范围。
2. 支持 exact-match-first 的替换策略。
3. 保留 backup / rollback 能力。
4. 引入 patch preview 概念。
5. 失败时不要自动模糊大改。

### 验证
1. 对一个小范围目标做 patch。
2. 检查 patch 是否只影响预期区域。
3. 检查 patch 失败时是否能安全退出，而不是破坏文件。

### 完成标准
- strict patch apply 可用。
- 修改边界得到控制。

---

## Step 24：引入 ask_user fallback

### 目标
当系统无法安全应用 patch 时，不盲改，而是升级为可控的人机协作。

### 需要做的事
1. 定义 ask_user 触发条件。
2. 明确哪些高风险情况必须中断自动修改。
3. 给出用户可理解的失败说明与下一步建议。
4. 保证 fallback 不会破坏已有文件。

### 验证
1. 模拟 patch 多次失败场景。
2. 检查系统是否进入 ask_user。
3. 检查用户收到的信息是否足以继续判断。

### 完成标准
- 自动修改失败时有安全退路。

---

## Step 25：打通 Review 最小闭环

### 目标
证明系统在不读整文件的前提下，也能完成一次可信审阅。

### 需要做的事
1. 选择一个单函数 review 场景。
2. 通过相关 entity / concept + ASTRead 局部读取完成分析。
3. 输出具体风险点、潜在 bug 和重构建议。
4. 必要时将结果沉淀为 review note。

### 验证
1. 检查 review 输出是否具体到函数或分支级别。
2. 检查是否没有依赖全文阅读。
3. 检查输出是否具备可执行建议，而非泛泛而谈。

### 完成标准
- Review 分支最小闭环跑通。

---

## Step 26：打通 Modify 最小闭环

### 目标
证明系统能完成一次“先 digest / prime / localize，再 patch / verify”的最小修改任务。

### 需要做的事
1. 选择一个单函数修改场景。
2. 执行 `/prime`。
3. 执行 `/plan`。
4. 通过 ASTRead 定位。
5. 生成并应用 strict patch。
6. 运行最小 verify。

### 验证
1. 检查是否没有整文件重写。
2. 检查 patch 是否只改动预定位置。
3. 检查 verify 是否通过。
4. 检查失败时是否会回到 TaskPack / patch 层，而不是退回全项目重读。

### 完成标准
- Modify 分支最小闭环跑通。

---

## Step 27：打通 Debug 最小闭环

### 目标
证明系统可以围绕局部报错做局部修复，而不是在错误面前退化为全文阅读。

### 需要做的事
1. 选择一个可复现的小错误场景。
2. 捕获并清洗 traceback。
3. 只保留关键调用栈。
4. 定位出错 symbol。
5. 若摘要不足则补 digest。
6. 生成修复 patch 并验证。

### 验证
1. 检查日志是否被有效清洗。
2. 检查读取范围是否聚焦于错误点附近。
3. 检查修复与验证是否形成闭环。

### 完成标准
- Debug 分支最小闭环跑通。

---

## Step 28：实现基础 verify / retry loop

### 目标
让修改和调试任务在失败时能有受控重试，而不是失控扩张。

### 需要做的事
1. 明确 verify 的最小执行集合。
2. 规定重试时允许保留哪些上下文。
3. 规定错误日志截断与摘要策略。
4. 规定超过一定失败次数后的 fallback 行为。

### 验证
1. 模拟一次 verify 失败后的重试。
2. 检查上下文是否仍然受控。
3. 检查不会无限扩张读取范围。

### 完成标准
- verify / retry 行为有边界且可解释。

---

## Step 29：实现 `/query-archive`

### 目标
开始建立“高价值问答与分析可沉淀”的能力。

### 需要做的事
1. 提供 `/query-archive` 命令。
2. 允许将高价值结果写入：
   - `concepts/`
   - `comparisons/`
   - `reports/`
3. 明确什么内容值得沉淀，什么不值得。
4. 为归档结果补充来源和状态字段。

### 验证
1. 选一个高价值分析结果做归档。
2. 检查归档位置是否正确。
3. 检查内容是否可被后续任务复用。

### 完成标准
- 系统开始具备知识复利能力。

---

## Step 30：实现 `/lint-wiki`

### 目标
防止 Wiki 页面膨胀、失效、断链和格式漂移。

### 需要做的事
1. 检查孤儿页。
2. 检查 stale 页。
3. 检查缺失 source 的页面。
4. 检查 frontmatter 缺项。
5. 输出 lint 报告到 `lint_reports/`。

### 验证
1. 人为制造几类问题页面。
2. 检查 lint 是否能识别。
3. 检查 lint 输出是否便于人工修复。

### 完成标准
- Wiki 有基础健康检查能力。

---

## Step 31：实现 `/reconcile`

### 目标
让系统能在源码变化后检查旧摘要是否与现状冲突。

### 需要做的事
1. 比较当前源码与已有 digest / archive 页面。
2. 标记冲突点与过期点。
3. 明确是更新原页、追加说明，还是生成 superseded 页面。
4. 输出 reconcile 报告。

### 验证
1. 选一个变更过的模块执行 reconcile。
2. 检查系统是否能识别摘要失效点。
3. 检查冲突结果是否可操作。

### 完成标准
- stale 页面有正式修复路径。

---

## Step 32：完善 Git 提交流程与变更审计约定

### 目标
让代码修改与 Wiki 修改都可回滚、可审计、可追溯。

### 需要做的事
1. 规定提交粒度。
2. 规定 commit message 的最小结构。
3. 规定 Wiki 更新与代码更新的关联策略。
4. 明确哪些步骤必须先验证再提交。

### 验证
1. 进行一次小范围改动并提交。
2. 检查提交信息是否清楚表达：
   - 模式
   - 模块
   - 任务类型
3. 检查是否能从 Git 历史中回放步骤。

### 完成标准
- Git 开始成为正式的审计与回滚底座。

---

## Step 33：补充 Obsidian / 运维层最小可用支持

### 目标
让 Wiki 进入长期可浏览、可维护状态，但不做过度美化。

### 需要做的事
1. 确保目录和 frontmatter 与 Obsidian 兼容。
2. 准备基础 Dataview 使用约定。
3. 让 `index.md`、stale、queue、archive 至少可被直观看到。
4. 不引入对主流程有强依赖的重型可视化要求。

### 验证
1. 用 Obsidian 打开 Wiki 根目录。
2. 检查页面结构、跳转、状态字段是否清晰。
3. 检查不使用 Obsidian 时，系统也不受影响。

### 完成标准
- 运维体验提升，但主流程不依赖它。

---

## Step 34：做一次完整的端到端演练

### 目标
在一个 demo 仓库或 demo 模块上验证整个最小闭环。

### 需要做的事
1. 执行一次 `/scan`。
2. 对核心模块执行 `/digest`。
3. 触发一次 `/prime`。
4. 执行一次 `/plan`。
5. 进行一次局部 patch。
6. 进行一次 verify。
7. 更新 Wiki 与 log。
8. 做一次 archive / lint / reconcile 中至少两项。

### 验证
1. 检查全流程是否真的不依赖整文件重写。
2. 检查 `standard` 模式是否未被破坏。
3. 检查整个过程中的读取范围、页面状态与队列是否合理。
4. 检查是否达成第一轮 MVP 八项。

### 完成标准
- 第一轮 MVP 闭环成立。

---

# 6. 每步完成后的固定输出格式

每完成一个步骤，AI 开发执行者必须输出以下内容：

## A. 本步完成内容
- 修改了哪些文件
- 新增了哪些文件
- 删除了哪些文件（如有）

## B. 本步验证结果
- 跑了哪些验证
- 哪些通过
- 哪些未通过
- 当前阻塞点是什么

## C. 对 `progress.md` 的更新摘要
- 记录完成项
- 记录问题
- 记录下一步建议

## D. 对 `architecture.md` 的更新摘要
- 新文件职责
- 修改文件职责变化
- 新的模块边界说明

---

# 7. 当前建议的实际执行顺序（优先级版）

如果时间有限，优先顺序如下：

1. Step 1 ~ Step 5：先把规则和模板固定
2. Step 6 ~ Step 12：先把模式、初始化、ingest、watcher 打通
3. Step 13 ~ Step 16：让 `/scan` 和 `/digest` 真正可用
4. Step 17 ~ Step 21：引入 TaskPack / EditSpec / `/prime` / `/plan`
5. Step 22 ~ Step 28：补 ASTRead、strict patch、debug 与 verify
6. Step 29 ~ Step 34：补 archive、lint、reconcile、Git、Obsidian、端到端演练

---

# 8. 第一轮 MVP 的硬验收标准

只有同时满足以下条件，第一轮才算完成：

1. `wiki_strict` 模式可独立启动。
2. `standard` 模式行为未被破坏。
3. 可自动生成 Wiki 骨架。
4. watcher 能标记 `stale` 并写入队列。
5. `/digest` 可对目标文件或 symbol 做局部语义消化。
6. `/plan` 在 `wiki_strict` 下输出结构化计划，而不是整文件代码。
7. ASTRead + strict patch 可支持一次单函数级修改。
8. 至少完成一次局部 debug 闭环。
9. Wiki 至少具备基础 archive / lint / reconcile 能力中的两项。
10. 全流程中没有退化为“大模型式全文通读+整文件重写”。

---

# 9. 结束语

本实施计划的核心不是“把功能堆满”，而是把 cc-mini 升级成一套真正适合本地 32K 小模型的受控工作体系。

最重要的不是快，而是：

- 不破坏原有 `standard`
- 不让小模型 OOM
- 不让修改任务失控
- 不让知识沉淀变成垃圾堆

因此整个执行必须始终围绕这条主线：

**规则固定 → 骨架建立 → 语义消化 → 任务预热 → 精准定位 → 局部 patch → 局部 debug → Wiki 复利运维**
