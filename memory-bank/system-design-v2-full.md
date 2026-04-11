# CC-MINI Wiki-Strict 模式升级总设计（v2.0 完整版）

版本：v2.0 Full  
日期：2026-04-11  
适用对象：cc-mini 框架二次开发 / 本地 32K 小模型代码助手 / 持久化知识库场景  
文档定位：**Human Docs / 总纲完整版**

---

## 1. 这份文档是干什么的

这份文档不是给执行器直接跑的“施工单”，也不是给本地 32K 小模型当最小 prompt 的“压缩包”。它的用途更像是：

- 项目总设计说明书
- 架构升级的理由说明
- 后续阶段拆分的总依据
- 你自己理解整个系统的主文档

也就是说，这份文档首先是**给人读的**，其次才是给后续 ChatGPT / Claude Code / cc-mini 提供稳定上位约束。

如果把整个项目比作盖房子，那么：

- `phase-0-exec.md` 这类文件是施工队今天要做什么
- 本文则是总平面图、结构设计说明和施工原则

因此它必须回答的不只是“做什么”，而更重要的是：

- 为什么要这样做
- 为什么不能继续沿用旧方式
- 为什么要分层、分阶段、分角色
- 为什么要把某些问题推迟到后续阶段
- 为什么本地 32K 小模型和强模型的设计方法不能一样

---

## 2. 项目背景：为什么 v1.0 不够了

你最初的 v1.0 版本已经抓住了核心矛盾：cc-mini 在强模型场景下可以直接工作，但到了本地 32K 小模型场景，会遇到结构性瓶颈。原始文档已经明确指出这些问题：

- 通读大文件或跨模块上下文时容易 OOM
- 多轮任务中会“失忆”，工具调用历史很快撑满上下文
- 若只依赖实时检索，模型每次都要从 Raw Sources 重新拼知识
- 若只有 AST / tree-sitter 的结构地图，语义仍然过粗，真正细粒度改代码时还是得重新读源码 fileciteturn0file2

因此，v1.0 提出了几个非常重要的原则：

- Raw Sources 不可变
- Wiki 是中间层，不是附属缓存
- 任务前必须做局部语义消化
- 修改前必须做目标定位
- 代码生成必须是局部 patch，而不是整文件重写
- 新逻辑必须兼容 `standard` 模式 fileciteturn0file2

这些原则到今天依然成立，而且仍然是新版系统的地基。

但是，当你开始真正把这套系统往“本地 32K + 实际长期使用”的方向推进时，又暴露了两个比 v1.0 更深的问题：

### 2.1 问题一：快 OOM 时，系统没有真正的“记忆固化”

v1.0 虽然已经强调 OOM 风险，但更多停留在“限制读文件、限制 Task Pack 大小、分离 plan/定位/实现/验证”的层面。它没有把“上下文濒临溢出时如何保留任务连续性”设计成一个完整子系统。

现实中会发生什么？

- 模型已经读了一些代码
- 已经定位到某个函数
- 已经试过一次 patch 或 debug
- 已经踩过一条失败路径
- 然后上下文快满了

如果这时系统只是做简单 compact，甚至只是删掉历史消息，那么对 32K 小模型来说，它并不是“忘了一点没关系”，而是**直接失去任务连续性**。

失去连续性带来的不是单次性能下降，而是结构性灾难：

- 它会重新读文件
- 它会重新猜路径
- 它会重新尝试已经失败过的方法
- 它会把之前已经确认过的事实重新当成未知
- 它会越来越依赖上下文补脑，而不是依赖外部状态恢复

所以 v2.0 必须把这一块正式升级成一个横切子系统，而不是零散补丁。这个子系统后来在本文中命名为：

**Context Safeguard**

### 2.2 问题二：小模型 plan 模式容易偏航

另一个在实际使用中暴露得非常明显的问题是：小模型即使有 plan 模式，也不代表它会稳定沿着计划走。

你已经观察到一个非常典型的症状：

- 它本来在执行当前任务
- 中途因为一个路径不存在、grep 失败、文件读取失败等局部问题
- 开始在这个局部问题上反复思考
- 然后逐渐把问题升级成别的任务
- 最终忘了原始任务是什么

从表面看，这像是模型“笨”或者“上下文太短”；但从系统设计角度看，真正的问题是：

> 它缺少稳定的任务锚点、失败后的回正机制，以及对“当前问题是否属于本阶段范围”的纪律控制。

换句话说，v1.0 已经解决了“不要让模型全文吃项目”的问题，但还没有解决：

> 当模型已经进入任务后，如何防止它被局部错误、后续问题、制度细节、无效分叉拉离主线。

因此，v2.0 还必须引入第二个横切子系统：

**Goal Anchoring & Drift Recovery**

---

## 3. v2.0 的核心升级，不是“再加两个功能”，而是升级系统工作方式

如果只是从功能角度理解，很容易把 v2.0 误解成：

- v1.0 + token 预警
- v1.0 + 目标提醒

但这不是重点。

真正的升级在于：

### 3.1 从“消息驱动”升级为“外部状态驱动”

旧方式中，任务连续性主要依赖对话消息和最近工具调用历史。  
这对大上下文强模型还有一定容错空间，但对本地 32K 小模型来说，这种方式过于脆弱。

v2.0 要求系统在几个关键层面外部化状态：

- Wiki 页面
- TaskPack
- Goal Stack
- Context Snapshot
- Deferred Issue Log
- Micro-Fork Note
- Checkpoint

也就是说，后续 agent 不应该依赖“我还记得刚才在说什么”，而应该依赖：

> 我可以从外部状态恢复我刚才做到哪了。

### 3.2 从“自由 plan”升级为“受控 plan”

旧方式中的 plan，更像“模型先想一想”。  
而在小模型场景里，plan 如果不受约束，很容易变成：

- 当前问题 + 一点未来问题 + 一点制度讨论 + 一点实现细节

最后把上下文吃满，而且还没有真正推进当前任务。

v2.0 里的 `/plan` 必须升级成结构化产物生成器，它的输出不再是“大段自由讨论”，而是：

- Goal Stack
- TaskPack
- EditSpec
- Patch Plan
- Deferred Issues
- Micro-Fork Notes

这样 plan 才是“控制任务边界”的工具，而不是“放大上下文消耗”的来源。

### 3.3 从“失败后继续试”升级为“失败后回正”

在旧方式里，失败通常意味着：

- 再试一次
- 再读一点文件
- 再看一点日志

但对小模型来说，这很容易走向：

- 重复尝试
- 死循环
- 失忆后再试同一路径

v2.0 要求任何连续失败都要先经过一个固定动作：

**Re-anchor Loop**

也就是：

1. 当前总目标是什么
2. 当前步骤目标是什么
3. 当前子任务目标是什么
4. 这个失败属于哪个层级
5. 是否值得切换任务
6. 若不值得，下一步最小动作是什么

这个机制的意义，不在于“更聪明”，而在于“更不容易跑偏”。

---

## 4. v2.0 的总体设计原则

以下原则是新版系统的总设计约束。后续所有 phases、schema、exec 包都必须服从这些原则。

### 4.1 模式隔离原则

必须保留两个主模式：

- `standard`：原有强模型 / 通用模式，不动主流程
- `wiki_strict`：面向本地 32K 小模型的受控工作模式

这一条很重要，因为你的升级目标不是推翻 cc-mini，而是在不破坏原体系的前提下，给它增加一条更适合小模型的执行通道。

也就是说，所有新能力都必须回答两个问题：

1. 它在 `wiki_strict` 里怎么工作？
2. 它会不会污染 `standard`？

如果一个新能力不能明确回答这两个问题，那它暂时就不应该落地。

### 4.2 熟知识优先原则

在 `wiki_strict` 下，系统默认不应该优先读 Raw Sources，而应该优先读：

1. `index.md`
2. 已 `digested` 的 entity / concept 页面
3. 当前 TaskPack
4. 当前 Goal Stack
5. 当前 Context Snapshot
6. 少量目标 symbol 源码切片

这个顺序的意义在于：

- 先拿到高密度熟知识
- 再补最小量原始证据

而不是每次都从原始代码重新开始。

### 4.3 分层原则

不能只靠 AST，也不能让 LLM 一上来全量“吃项目”。  
必须拆成：

- 结构测绘
- 语义消化
- 任务预热
- 目标定位
- 局部 patch
- 局部 debug
- 上下文保障
- 偏航恢复
- Wiki 运维

这里最关键的是：

> “上下文保障”和“偏航恢复”不再是额外功能，而是核心工作流的一部分。

### 4.4 计划、定位、修改、验证分离原则

本地 32K 小模型不能稳定地在一轮里同时完成：

- 规划
- 定位
- 改代码
- 调试
- 回归验证

必须通过状态机，把这些动作拆开。

这不仅是为了节省 token，也是为了让每个阶段的产物都能被外部持久化。

### 4.5 目标锚定优先于自由思考原则

任何 plan / modify / debug，都必须先有 Goal Stack。  
模型不是不能思考，而是不能在没有目标锚点的情况下自由发散。

### 4.6 上下文保护是横切能力原则

Context Safeguard 不是 Layer 6、Layer 7 这种单独新层，而是横跨：

- token budget
- engine
- compact
- session
- wiki/log
- taskpack
- debug/retry

它像是整个系统的“生命维持系统”。

---

## 5. 最终架构：六层主结构 + 两个横切子系统

v2.0 仍然保留 v1.0 的六层主结构，因为这套结构本身是合理的。变化主要发生在：

- 各层之间增加了更多正式状态对象
- Layer 3 和 Layer 4 被大幅强化
- Layer 5 不再只处理 archive / reconcile，也要承接 snapshot / deferred issue 等长期资产
- Context Safeguard 与 Goal Anchoring 成为横切子系统

### 5.1 六层主结构

#### Layer 0：Raw Sources

这是不可变事实层。  
它的价值不是“直接让模型读”，而是作为系统中所有高层结论的最终证据来源。

Raw Sources 包括：

- 项目源码
- Markdown / TXT / 文献资料
- 历史设计文档
- 导出的聊天记录 / 会议纪要

基本要求：

- 只读
- 带 `source_id`
- 对代码源记录 `repo / branch / commit / 日期`

v2.0 里这一层没有本质变化，但其意义更明确了：

> Goal Stack、TaskPack、Snapshot 都不能伪装成事实层，它们永远只是解释层和执行层辅助对象。

#### Layer 1：Structural Ingest

这是“搭骨架”的层。  
它负责把一个代码库、一个文档集、一个项目目录变成最基础的结构化地图。

能力包括：

- tree-sitter / AST 扫描
- 文本/文档标题结构解析
- 目录结构和 symbol 建模
- 生成 `index.md` 和基础 `entities/*.md`

这一层的产物是：

- `status: raw_ast`

为什么叫 `raw_ast`？  
因为这类页面只具备结构信息，还不能被当成可靠语义摘要使用。

v2.0 对这一层新增的要求是：

- 结构测绘结果也要能挂接 Goal / Snapshot 引用
- 便于后续 digest、TaskPack 和恢复逻辑引用

#### Layer 2：Semantic Digest

这是“给骨架加血肉”的层。  
它负责把 `raw_ast` 变成“可操作的、能指导 review / modify / debug 的页面”。

能力包括：

- 按文件、按 symbol、按 span 做切片式 LLM 精读
- 提炼角色、流程、边界条件、依赖、风险点、修改入口
- 更新 entity 页面，使其具备“可操作性”

输出状态：

- `partially_digested`
- `digested`
- `stale`

v2.0 对这一层最重要的升级是：

- digest 页面不只是“更好读”，还必须便于后续 Goal Stack / TaskPack / Snapshot 引用
- 也就是说，digest 页面开始成为后续恢复执行的基础锚点之一

#### Layer 3：Task Priming / Task Pack

这是 v2.0 升级的重心之一。

在 v1.0 中，Task Pack 已经被定义为“当前任务相关的最小知识包”。这个方向完全正确，但在实际推进中暴露出一个问题：

> 如果 TaskPack 只是局部摘要，而没有绑定目标锚点、恢复状态和失败记忆，那么它仍然不够稳定。

所以 v2.0 里，TaskPack 需要和以下对象建立正式关系：

- Goal Stack
- Context Snapshot
- Deferred Issue Log
- EditSpec

新版 TaskPack 至少要包含：

- 用户任务目标
- 目标文件
- 目标 symbol
- 相关 digested 页面
- 最近 diff
- 风险点
- 验证建议
- Goal Stack 引用
- 最近 snapshot 引用（若存在）

这样它才不只是“任务摘要”，而是真正的任务准备层。

#### Layer 4：Safe Edit / Verify

这是执行层，也是小模型最容易失控的地方。

能力包括：

- ASTRead / Symbol Read
- Search/Replace Patch
- strict file_edit
- ask_user fallback
- lint / test / bash verify
- traceback 清洗与重试
- Re-anchor Loop

v2.0 对这一层的升级，主要集中在两点：

##### 升级点 A：执行前必须带 Goal Stack / TaskPack / EditSpec

过去可能会直接“生成 patch 再说”，现在不允许。  
没有定位结果，不进入 patch。没有 Goal Stack，不进入 plan。没有 EditSpec，不进入修改。

##### 升级点 B：debug / retry 必须和 Context Safeguard 联动

也就是说，debug 不只是“看错误再修”，而是必须记录：

- last_error
- failed_attempts
- current_action
- next_action
- snapshot refs

否则小模型很快就会在调试中迷路。

#### Layer 5：Compounding LLM Wiki

这是知识复利层。  
它负责把高价值结论、已消化知识、历史决策、失败路径变成长期可维护资产。

能力包括：

- ingest
- query
- query-archive
- lint
- reconcile
- index / log / schema 维护
- Obsidian / Git 运维支持

v2.0 对这一层的重要升级是：

- Context Snapshot 也进入长期管理体系
- Deferred Issue / Micro-Fork 也可被管理
- 不只是“好答案归档”，而是“执行历史和失败记忆也能变成资产”

### 5.2 横切子系统一：Context Safeguard

#### 目标
当上下文临近 OOM 时，不是简单删历史，而是把当前任务状态固化成可恢复对象。

#### 为什么必须是独立子系统
因为它不能只挂在 compact 上，也不能只挂在 engine 上。它必须同时影响：

- token 监控
- 消息压缩
- debug/retry
- session checkpoint
- wiki/log
- taskpack

#### 核心能力
1. Token 使用率监控
2. 风险等级判断
3. 上下文脱水（Dehydration）
4. Context Snapshot 生成
5. Snapshot 持久化
6. 会话恢复

#### 风险等级建议
- `safe`：< 0.65
- `watch`：0.65 ~ 0.78
- `warning`：0.78 ~ 0.85
- `critical`：0.85 ~ 0.92
- `emergency`：> 0.92

#### 为什么不是单阈值
如果只设 85% 一条线，很多时候已经太晚。  
本地 32K 小模型的一个 tool output 或 traceback 就可能瞬间把剩余预算吃掉。

#### Snapshot 为什么分两类

##### Runtime Snapshot
这是系统自己用来恢复执行的结构化状态。

至少包含：
- session_id
- task_id
- mode
- current_step
- active_goal
- target_files
- primary_symbols
- changed_files
- last_error
- failed_attempts
- next_action
- token_ratio
- created_at

##### Markdown Snapshot
这是给人和后续 agent 读的“高密度任务交接单”。

建议包含：
1. 当前任务目标
2. 已确认事实
3. 当前目标文件 / symbol
4. 已修改内容
5. 最近失败路径
6. 当前阻塞点
7. 下一步最合理动作
8. 恢复提示

两者并存的意义是：

- Runtime Snapshot 保证可恢复
- Markdown Snapshot 保证可解释

#### 触发点
必须至少在以下位置检查：

1. 用户输入后
2. 模型请求前
3. 工具输出回填后
4. debug / retry 回合之间

#### 持久化位置
- session checkpoint
- `.cc-mini/wiki/log.md`
- 可选 `reports/context_snapshots/`

### 5.3 横切子系统二：Goal Anchoring & Drift Recovery

#### 目标
防止小模型在长任务中偏离主线，尤其是在：

- 路径不存在
- grep/读文件失败
- patch 失败
- plan 扩展到后续阶段问题

时仍能稳定回到任务主线。

#### Goal Stack
任何任务开始前，必须生成 Goal Stack：

- `global_goal`
- `step_goal`
- `task_goal`
- `current_action`
- `done_definition`
- `out_of_scope`

为什么一定要四层目标而不是一句话目标？  
因为小模型最容易犯的错，就是把“当前失败”误认为“当前任务”。

有了 Goal Stack，它才知道：

- 我在整个项目中属于哪一阶段
- 我现在这一步的边界是什么
- 我这一次调用只在做哪个子任务
- 我眼前失败的是动作层问题还是阶段层问题

#### Drift Detector
它负责识别几类典型偏航：

- 连续路径不存在
- 连续 grep/读取失败
- 同一 patch 重复失败
- 进入后续阶段问题讨论
- 超出当前允许读取 / 修改范围

#### Re-anchor Loop
任何连续失败、局部异常、明显偏航之后，都先跑一次固定回正流程：

1. 当前总目标是什么
2. 当前步骤目标是什么
3. 当前子任务目标是什么
4. 当前失败属于哪个层级
5. 是否值得切换任务
6. 若不值得，下一步最小动作是什么

#### Deferred Issue Log
用于记录“当前发现但不该现在解决”的问题。  
它的意义非常大：

> 不让模型因为发现了一个真实问题，就立刻切换任务去修。

#### Micro-Fork Note
用于记录轻量分叉问题，但不在主上下文中真正并行维护多个大分支。  
这比直接照搬某些重型 fork 模式更适合本地 32K 场景。

---

## 6. Wiki 目录结构设计（v2.0）

v2.0 的目录结构在 v1.0 基础上延续，但要补充新 policy 与未来 snapshot / fork 等类型。

建议目录：

```text
.cc-mini/
  wiki/
    index.md
    log.md
    schema/
      AGENTS.md
      conventions.md
      digest_policy.md
      conflict_policy.md
      taskpack_policy.md
      watchdog_policy.md
      context_safeguard_policy.md
      goal_policy.md
      phase_boundary_policy.md
    entities/
      code/
      docs/
      modules/
      papers/
    concepts/
    comparisons/
    reports/
    source_notes/
    taskpacks/
    lint_reports/
    inbox/
      digest_queue.md
      reconcile_queue.md
    archive/
```

### 6.1 为什么 schema 要继续扩展

因为 v1.0 的 schema 已经能管住：

- digest
- conflict
- taskpack
- watchdog

但 v2.0 新增了：

- OOM 预警与快照恢复
- 目标锚定与偏航恢复
- 阶段隔离

如果不把这些继续规则化，就会再次退化回“聊天中临时约定”。

---

## 7. 页面规范扩展（v2.0）

v1.0 已经有一套 frontmatter 体系和状态体系，这些都保留。  
v2.0 只是在其基础上扩展，让页面能和 Goal / Snapshot / Deferred Issue 发生引用关系。

### 7.1 统一字段

在原有字段基础上，建议增加：

- `goal_refs`
- `snapshot_refs`
- `deferred_issue_refs`

示例：

```yaml
---
type: entity
domain: code
status: raw_ast
source_ids:
  - SRC-2026-0411-001
repo: cc-mini
branch: main
commit: abc1234
updated_at: 2026-04-11
validated_at: 2026-04-11
confidence: medium
supersedes: []
superseded_by: []
tags:
  - engine
  - coordinator
goal_refs: []
snapshot_refs: []
deferred_issue_refs: []
---
```

### 7.2 新增页面类型建议

- `context_snapshot`
- `goal_note`
- `deferred_issue`
- `micro_fork`

这些不一定要在 Phase 0 就全部落地，但在总设计上必须先占位。

---

## 8. 统一业务流程（v2.0）

v1.0 的总流程已经很清楚了，v2.0 只是把两个横切子系统插入到真正应该插入的位置。

新版总流程：

```text
User Request
  ↓
Goal Stack Initialization
  ↓
Task Classifier
  ↓
Wiki State Check
  ↓
Task Digest / Task Pack
  ↓
Target Localization
  ↓
Operation Branch
   ├─ Review
   ├─ Modify
   └─ Debug
  ↓
Verify / Re-anchor
  ↓
Context Snapshot (if needed)
  ↓
Wiki Update / Archive
```

这里最关键的变化是前后各多了一个系统级动作：

### 前置新增：Goal Stack Initialization
任何任务开始前先锚定目标，不允许“直接开始 plan”。

### 后置新增：Context Snapshot (if needed)
任何达到 critical / emergency 风险，或经历多轮 debug / retry 的任务，都要能固化状态。

---

## 9. `/plan` 的升级设计（v2.0）

### 9.1 v1.0 的 plan 问题

v1.0 已经提出：`wiki_strict` 下的 `/plan` 不应直接输出整文件代码。这个方向是正确的。  
但 v2.0 进一步要求：

> `/plan` 不只是“不写整文件代码”，还要成为“边界控制器”。

### 9.2 新版 `/plan` 输出

在 `wiki_strict` 模式下，`/plan` 输出：

1. Goal Stack
2. TaskPack
3. EditSpec
4. Patch Plan
5. Deferred Issues（如有）
6. Micro-Fork Notes（如有）

### 9.3 EditSpec 的意义

EditSpec 不只是一个 patch 描述，它是“当前允许改什么、绝对不准改什么”的结构化表达。

示例：

```yaml
---
task: strict_patch_fallback
mode: wiki_strict
target:
  file: src/core/tools/file_edit.py
  symbol: apply_patch
intent:
  - preserve exact-match-first behavior
  - after two failures invoke ask_user
constraints:
  - keep backup logic unchanged
  - no fuzzy auto-replace
verify:
  - exact-match failure path
  - user-approve path
---
```

在 v2.0 里，EditSpec 还应该和 Goal Stack / Snapshot 有正式引用关系。

---

## 10. Watchdog 与状态管理的新版边界

### 10.1 Watchdog 继续只做保守动作

这一点不能放松。  
Watchdog 仍然只负责：

- 监听文件变化
- 发现受影响页面
- 标记页面为 `stale`
- 写入 digest / reconcile queue
- 写 log

### 10.2 Watchdog 不负责

- 自动大规模 digest
- 自动 reconcile 裁决
- 自动覆盖高置信度页面
- 代替人工和更高层策略做决定

### 10.3 v2.0 的升级点

它需要和 Goal / Snapshot 体系共存，但不能越权。  
例如：

- Watchdog 可以让页面变 stale
- 但“这会不会影响当前 TaskPack 的有效性”是 conflict / taskpack / flow state 层要处理的事

---

## 11. 必须新增或改造的模块（v2.0）

### 11.1 新增模块

- `src/core/knowledge/dehydrator.py`
- `src/core/knowledge/context_snapshot.py`
- `src/core/wiki/snapshot_writer.py`

### 11.2 强化模块

- `src/core/token_budget.py`
- `src/core/engine.py`
- `src/core/session.py`
- `src/core/flow_state.py`
- `src/core/plan.py`

### 11.3 保留但角色强化的模块

- `src/core/knowledge/ingester.py`
- `src/core/knowledge/watcher.py`
- `src/core/tools/ast_read.py`
- `src/core/tools/file_edit.py`

v2.0 不是把原模块推翻，而是让它们承担更清晰的角色。

---

## 12. 分阶段开发计划（v2.0）

这里的重点不是再列一遍任务，而是讲清楚：为什么 Phase 0–4 必须重排。

### Phase 0：规则定稿（升级）

在 v2.0 里，Phase 0 不只是原先的 schema 定稿，还必须补进：

- `context_safeguard_policy.md`
- `goal_policy.md`
- `phase_boundary_policy.md`

为什么必须先做这个？  
因为这三者决定了后续 Phase 1–4 的边界。如果不先定，Phase 1 以后又会回到“边写边猜制度”的老路。

### Phase 1：模式接入与结构测绘（升级）

在 v2.0 里，Phase 1 不再只是 `wiki_strict` 模式开关和结构骨架，还要预埋：

- token risk monitor 骨架
- Goal Stack 占位注入
- wiki_strict 初始化时的最小目标锚点

也就是说，Goal Anchoring 的最小骨架不能等到后面再补。

### Phase 2：语义消化层（升级）

在 v2.0 里，Phase 2 要开始支持：

- dehydration 最小版
- snapshot 写入最小闭环
- 最小 drift check

也就是说，语义消化不再只服务 review / modify，还开始服务“恢复执行”。

### Phase 3：任务级消化与 `/plan` 重构（升级）

在 v2.0 里，Phase 3 是第二个重心。

必须新增：

- Goal Stack 正式对象
- Deferred Issue Log
- Micro-Fork Note
- TaskPack / EditSpec 与 Snapshot / Goal 的引用关系

这使得 `/prime` 和 `/plan` 从“任务理解辅助工具”升级为“任务边界与恢复状态管理器”。

### Phase 4：精准修改与 debug 闭环（升级）

在 v2.0 里，Phase 4 不只是 ASTRead / strict patch / debug retry，而是正式加入：

- Re-anchor Loop
- patch/debug 中的 drift detection
- failed attempts 和记忆恢复

换句话说，Phase 4 是第一阶段真正把“改代码”和“防偏航 / 防失忆”结合起来的地方。

### Phase 5：Compounding LLM Wiki（升级）

在 v2.0 里，Phase 5 不再只是 archive / reconcile / query-archive，还要接管：

- context snapshot 的长期管理
- deferred issue / micro-fork 的历史管理

### Phase 6：Obsidian / Git 运维层（升级）

在 v2.0 里，Phase 6 应该让：

- snapshot
- stale
- conflicts
- deferred issues

都可以被长期可视化和运维。

---

## 13. 里程碑（v2.0）

- M1：wiki_strict 可启动，且具备最小 Goal Stack
- M2：digest 页面可操作，且可生成最小 snapshot
- M3：TaskPack / EditSpec / Goal Stack 可跑通
- M4：局部 patch / debug 可跑通，且支持 Re-anchor
- M5：知识复利闭环成立，含 snapshot / deferred issue 管理
- M6：进入长期运维

这些里程碑相比 v1.0 的变化，不是多了更多功能，而是多了“连续性”和“恢复性”的要求。

---

## 14. 风险与规避（v2.0）

### 风险 1：把新能力都做成零散补丁
规避：
- Context Safeguard 与 Goal Anchoring 都必须成为正式 policy / 正式对象 / 正式 phase 要求

### 风险 2：小模型继续在长任务中偏航
规避：
- Goal Stack 必须前置
- Re-anchor Loop 必须固定化
- Deferred Issue 必须强制存在

### 风险 3：OOM 时只删历史，不固化状态
规避：
- Runtime Snapshot + Markdown Snapshot 双轨并存
- snapshot 必须写入 checkpoint + wiki/log

### 风险 4：TaskPack 只是摘要，不能恢复执行
规避：
- TaskPack 必须引用 Goal / Snapshot / Deferred Issues

### 风险 5：阶段隔离被破坏
规避：
- 每个 Phase 必须有 In Scope / Out of Scope
- 后续问题只允许进入 deferred issue

---

## 15. 结语

最终目标不是“再给 cc-mini 加几个模块”，而是把它升级成两套并存的能力：

- `standard`：原有强模型 / 通用模式
- `wiki_strict`：面向本地 32K 小模型的受控工作模式

相比 v1.0，v2.0 的关键跃迁不在于功能数量，而在于：

- 系统不再只是“减少上下文消耗”
- 系统开始正式管理“任务连续性”
- 系统开始正式管理“偏航恢复”
- 系统开始正式管理“失败记忆”

因此，v2.0 的真正主线应该理解为：

**Goal Anchoring → 结构扫描 → 语义消化 → 任务预热 → 精准定位 → 局部 patch → 局部 debug → Re-anchor → Context Snapshot → 持久化 Wiki 运维**

只要始终围绕这条主线开发，系统就不会偏离最初的三个最终目标：

1. 不破坏原框架
2. 避免 32K 小模型 OOM
3. 形成长期知识复利
