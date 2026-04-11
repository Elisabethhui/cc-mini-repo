# Phase 0–Phase 4 Full Guide

版本：v2.0 Full Guide  
日期：2026-04-11  
适用对象：cc-mini 框架升级 / 本地 32K 小模型 / 新手入门者 / Claude Code + ChatGPT 协作开发

---

## 1. 文档目的

这份文档不是给执行器的“施工单”，而是给你看的 **阶段路线图完整版**。

它的任务不是告诉你“下一条命令怎么敲”，而是回答下面这些更重要的问题：

1. 为什么要把整个项目拆成 Phase 0–Phase 4，而不是直接开写？
2. 每个 Phase 到底在解决什么真实问题？
3. 每个 Phase 的输入、输出、边界、风险是什么？
4. 为什么有些事情明明“看起来很简单”，却不能提前做到前一个 Phase？
5. 作为新手，在实际用 Claude Code / cc-mini 的时候，应该如何理解每个阶段的作用？
6. 这条路线和你当前的真实情况如何对应？

如果说 `system-design-v2-full.md` 是总纲，那么这份文档就是“路线图 + 导航图 + 阶段解释手册”。

---

## 2. 为什么一定要分阶段

### 2.1 因为你面对的不是普通脚手架项目，而是“受限小模型下的协作系统”

这个项目和普通的“我写一个小网站”不一样。  
你现在要做的是：

- 在已有 cc-mini 项目基础上继续演化
- 兼容原有 `standard` 模式
- 为本地 32K 小模型增加 `wiki_strict` 风格的受控模式
- 让小模型不 OOM
- 让小模型不偏航
- 让系统能持续沉淀知识，而不是只完成一次对话

这意味着你不是在“写一个功能”，而是在**造一个工作方式**。

如果这种事情不分阶段，就会发生三类典型灾难：

#### 灾难 1：制度层没定，就开始写实现
例如：
- TaskPack 到底是什么还没定
- 页面状态怎么转换还没定
- Snapshot 的定义还没定
- 结果代码先写起来了

这样后面会不断推倒重来。

#### 灾难 2：执行层提前做太多
例如：
- ASTRead 还没定义边界，就开始 patch
- patch 机制还没做好，就开始 debug
- goal stack 还没接上，就让 plan 自由思考

这样小模型会越来越乱。

#### 灾难 3：把“当前步骤问题”和“后续阶段问题”混在一起
这是你已经遇到过的真实问题。  
模型会在当前步骤里突然开始问：
- TaskPack 格式
- Conflict Policy 边界
- Watchdog 是否参与冲突裁决
- TaskPack 和 EditSpec 是不是同文件

这些问题本身都重要，但并不都属于“当前步骤”。  
如果不分阶段，小模型会把未来问题拖进当前上下文，导致不断偏航。

---

### 2.2 阶段拆分的本质：先定制度，再定骨架，再定语义，再定任务，再定执行

Phase 0–4 的关系可以理解为：

- **Phase 0**：先把“法律”写清楚
- **Phase 1**：再把“地基和框架”搭出来
- **Phase 2**：再让系统真正“理解内容”
- **Phase 3**：再让系统围绕“当前任务”形成局部熟知识
- **Phase 4**：最后才允许真正进入定点改代码和局部 debug

也就是说：

**制度层 → 骨架层 → 理解层 → 任务层 → 执行层**

这个顺序不是教条，而是被你的场景逼出来的。

---

## 3. 当前你的真实位置

在你现在的项目里，最早那一轮已经把 Step 1–3 做到了：

- memory-bank 基础文件
- schema 规则骨架
- frontmatter 规范

但是旧 Step 4 的内容你已经明确不信任了。原因也很清楚：

1. 旧 Step 4 主要是本地 32K 小模型产物，质量不稳定
2. 后来你又补充了两个关键问题：
   - Context Safeguard
   - Goal Anchoring & Drift Recovery
3. 这两个问题会直接改变后续 Step 4 乃至整个 Phase 结构
4. 所以旧 Step 4 不能作为新版本的执行依据

因此你现在不是“继续往后走”，而是：

- **回退到 Step 3**
- **升级到 v2.0**
- **从 Phase 0 重新整理制度层**
- 然后才重新进入 Phase 1–4 的执行路线

这也是为什么你现在最需要“完整版路线图”，而不是更多 runner docs。

---

# 4. Phase 0：规则与契约定稿

## 4.1 Phase 0 的核心任务是什么

Phase 0 解决的是：

**在写任何实现代码之前，先把系统的制度层讲清楚。**

这个阶段不是为了让系统“跑起来”，而是为了让系统“以后不会乱”。

它要回答的问题包括：

- Wiki 的页面类型有哪些？
- frontmatter 需要哪些字段？
- 页面状态有哪些？如何解释？
- TaskPack 是正式对象吗？
- EditSpec 的 target 粒度到哪里？
- Watchdog 只做 stale 标记，还是也做冲突判定？
- OOM 预警和 Snapshot 的契约是什么？
- Goal Stack 是正式对象还是只是一段提示词？
- Deferred Issue 和 Micro-Fork 是正式机制还是临时想法？

这些东西如果不先回答，后面所有代码都会漂。

---

## 4.2 为什么 Phase 0 必须单独存在

因为新手最容易犯的错就是：

> “这个东西我大概知道，先写出来再说。”

但你这个项目不能这么做。  
因为你不是在做单机脚本，而是在做“未来还要长期扩展的工作流系统”。

如果 Phase 0 不独立，后面会出现：

- 同一个概念在不同文件里意思不一样
- 32K 小模型在 coding 过程中重新定义规则
- 你今天决定一种格式，明天又推翻
- 旧文件和新文件互相打架

换句话说：

**Phase 0 是整个系统的“概念冻结阶段”。**

---

## 4.3 Phase 0 应该包含什么

### A. 页面与元数据规则
- frontmatter 字段
- `type`
- `status`
- `domain`
- `source_ids`
- `goal_refs`
- `snapshot_refs`
- `deferred_issue_refs`

### B. 规则层文件
- `AGENTS.md`
- `conventions.md`
- `digest_policy.md`
- `conflict_policy.md`
- `taskpack_policy.md`
- `watchdog_policy.md`

### C. 新增 v2.0 规则文件
- `context_safeguard_policy.md`
- `goal_policy.md`
- `phase_boundary_policy.md`

### D. 阶段边界
每个 Phase 允许做什么，不允许做什么。

---

## 4.4 Phase 0 的典型风险

### 风险 1：问题定得太细，提前卷入实现
例如：
- 用 dataclass 还是 pydantic
- JSON 还是 YAML 还是 TOML
- parser 怎么写
- lint 报错格式长什么样

这些很多不是 Phase 0 的核心问题。  
Phase 0 只需要定契约，不需要实现全部技术细节。

### 风险 2：规则文件之间边界不清
例如你之前已经遇到的：
- taskpack_policy 和 conflict_policy 的边界模糊
- watchdog_policy 和 conflict_policy 的协同未明

这类问题在 Phase 0 应该被明确记录：
- 哪些已拍板
- 哪些延后到后续 Phase

### 风险 3：试图在 Phase 0 就写代码
这是绝对要避免的。

---

## 4.5 Phase 0 完成后的标志

当你完成 Phase 0 时，系统应该达到：

1. 所有关键概念都有定义
2. 所有关键边界都有说明
3. 新增的 Context Safeguard 和 Goal Policy 已经正式入法
4. 后续 Phase 不需要再反复问“这个概念到底是什么意思”

也就是说，Phase 0 完成后，项目不会更“能跑”，但会更“不乱”。

---

# 5. Phase 1：模式接入与结构骨架

## 5.1 Phase 1 的核心任务是什么

Phase 1 解决的是：

**把 wiki_strict 这条新工作流，正式接到 cc-mini 上。**

这是第一次进入代码实现阶段，但注意，它仍然不是“让系统真正懂业务”。

Phase 1 更像是：

- 给系统装上新的工作模式
- 建立运行时 wiki 目录
- 打出结构骨架
- 接入最小 token risk 监控
- 接入最小 Goal Stack 占位

所以它是一个“**接线 + 搭壳**”阶段。

---

## 5.2 为什么 Phase 1 不能直接开始 digest / patch / debug

因为你如果没有：
- mode 切换
- wiki 根目录
- index/log
- raw_ast entity 骨架
- watcher stale 标记
- token risk 输出
- goal stack 占位

那后面的 digest、TaskPack、patch 就没有依托。

你可以把它想象成：

- Phase 0：写了建筑法规
- Phase 1：把地基、钢筋和框架搭起来

这时候当然不能直接装修。

---

## 5.3 Phase 1 应该做什么

### A. 模式接入
- `main.py` 增加 `--mode wiki_strict`
- `config.py` 增加 `RunMode`
- `coordinator.py` 开始分流 standard / wiki_strict

### B. Wiki 初始化
在 `.cc-mini/wiki/` 下生成：
- `index.md`
- `log.md`
- `inbox/digest_queue.md`
- `inbox/reconcile_queue.md`

### C. Structural Ingest 骨架
- 读取目录结构
- 建 symbol 清单
- 输出 raw_ast entity 页面

### D. Watcher 骨架
- 监听文件变化
- 标记 `stale`
- 写 queue
- 不做深度总结

### E. 最小 Context Safeguard 接入
- `token_budget.py` 输出 usage ratio
- 输出 risk level
- 先做 warning / critical 提示，不做完整 snapshot 闭环

### F. 最小 Goal Anchoring 接入
- 每个 wiki_strict 会话建立 Goal Stack 占位对象
- 当前 Step / Phase 可被读取

---

## 5.4 Phase 1 最大的误区

### 误区 1：以为“骨架搭起来了”就可以直接 patch
不行。  
你现在只有目录、页面壳子和模式入口，没有“局部熟知识”。

### 误区 2：把 ingest 当成 digest
结构扫描不等于语义理解。  
raw_ast 只是骨架页，不是可操作页。

### 误区 3：把 token risk 输出当成完整 OOM 防护
Phase 1 只做 monitor，不做完整 dehydration。

---

## 5.5 Phase 1 完成后的标志

完成后你应该具备：

1. wiki_strict 能启动
2. standard 模式不受影响
3. `.cc-mini/wiki/` 目录可初始化
4. 至少一个 demo 项目可生成 raw_ast entities
5. 控制台能看到 token risk level
6. 会话里能看到 Goal Stack 占位

---

# 6. Phase 2：语义消化与状态升级

## 6.1 Phase 2 的核心任务是什么

Phase 2 解决的是：

**“系统已经有骨架了，但还不会真正理解内容。”**

这是从“知道文件和 symbol 存在”升级到“知道它们在干什么”的阶段。

如果没有 Phase 2，后面的 TaskPack 只是把一堆标题和路径打包，并不能真正帮助小模型完成修改和 debug。

---

## 6.2 为什么 digest 是单独一个 Phase

很多人会觉得：
- 我已经能读代码了
- 为啥不直接生成 TaskPack 呢？

原因是 TaskPack 本质上依赖于“已经有一定质量的局部熟知识”。

如果你直接跳过 digest，会出现两种坏结果：

### 坏结果 1
TaskPack 只是“路径+文件名+猜测”

### 坏结果 2
为了生成 TaskPack，小模型又被迫重新读原始代码  
这样你本来想省 token，结果反而更费。

所以 Phase 2 的作用就是：

**把原始代码变成可操作知识。**

---

## 6.3 Phase 2 应该做什么

### A. `/scan`
只做结构测绘，不做语义总结。

### B. `/digest`
对指定文件 / symbol 做局部语义消化。

### C. `/digest --changed`
只对最近变更目标做 digest，减少浪费。

### D. 页面状态升级
- `raw_ast`
- `partially_digested`
- `digested`
- `stale`

### E. 最小 Context Safeguard 闭环
这时才开始接入：
- `dehydrator.py`
- 最小 Runtime Snapshot
- log 写入
- checkpoint 写入

### F. 最小 Drift Check
比如：
- 路径不存在反复出现
- 重复 scan / digest 同一无效目标
- 当前范围明显超出本步骤

---

## 6.4 为什么这个阶段对 32K 小模型特别重要

因为 32K 小模型最大的问题不是“不会写代码”，而是：

**它不该每次都重新学习同一段代码。**

Phase 2 的 digest，其实是在帮模型建立“局部熟悉感”。  
这样后面真正进入 TaskPack、plan、patch 时，它就不需要再靠一次性大输入硬扛。

---

## 6.5 Phase 2 完成后的标志

完成后你应该至少有：

1. `/scan` 可用
2. `/digest` 可用
3. `/digest --changed` 可用
4. 至少 5 个核心文件已经 digested
5. digested 页面足够指导后续 review / modify
6. critical risk 时能生成一次最小 snapshot
7. 遇到明显路径偏航会停止并记录

---

# 7. Phase 3：任务预热与结构化计划

## 7.1 Phase 3 的核心任务是什么

Phase 3 解决的是：

**系统虽然已经懂局部内容了，但还不会围绕“这次任务”组织最小知识包。**

也就是说，Phase 2 解决的是“理解代码”，  
而 Phase 3 解决的是“理解当前任务”。

这个差别非常重要。

---

## 7.2 为什么 TaskPack / EditSpec 一定要放在独立阶段

因为它们不是“补充文档”，而是：

- 修改任务的前置条件
- 小模型上下文收缩器
- 防止 plan 发散的约束器

如果这一步没单独做好，小模型就会：

- 一边 plan 一边重新读整个项目
- 一边 patch 一边发散到后续问题
- 看到局部问题就跳出当前任务

这也是你后来为什么会提出 Goal Anchoring 和 Drift Recovery 的根本原因。

---

## 7.3 Phase 3 应该做什么

### A. TaskPack
正式定义与持久化：
- task summary
- target file
- primary symbols
- related symbols
- hotspots
- constraints
- verify checklist
- goal_stack_ref
- snapshot_ref（可选）

### B. EditSpec
正式定义：
- task
- mode
- target
- intent
- constraints
- verify
- goal_guard

target 不应只停留在 file 级，应该到：
- symbol
- span
- anchor

### C. `/prime`
负责生成 TaskPack。

### D. `/plan`
在 wiki_strict 下不再直接生成代码，而是输出：
- Goal Stack
- TaskPack
- EditSpec
- Patch Plan
- Deferred Issues
- Micro-Fork Notes（如有）

### E. Goal Stack 正式接入
这时候不是占位了，而是正式对象。

### F. Deferred Issue Log
把“当前发现但不该现在解决的问题”外部化。

### G. Micro-Fork Note
把轻量分叉问题记录下来，但不污染主线。

---

## 7.4 为什么这一步会极大省 token

因为从这一步开始，系统终于不再靠“全文上下文”工作，而是靠：

- digested 页面
- TaskPack
- Goal Stack
- EditSpec

这就意味着：

**以后真正执行 patch 时，模型的输入会变得非常窄。**

这才是你想要的“省 token + 快速迭代”。

---

## 7.5 Phase 3 最大的风险

### 风险 1：TaskPack 太大
如果 TaskPack 仍然把太多文件和 symbol 都塞进去，那它就退化成“另一种全文”。

### 风险 2：plan 仍然自由散开
如果 `/plan` 没有 Goal Stack / Deferred Issue / Micro-Fork 约束，它还是会发散。

### 风险 3：EditSpec 只写 file，不写 symbol/span
这样 patch 还是不够稳。

---

## 7.6 Phase 3 完成后的标志

完成后应该具备：

1. `/prime` 可用
2. TaskPack 可持久化
3. EditSpec 可生成
4. `wiki_strict` 下 `/plan` 不再自由输出整文件代码
5. Goal Stack 已正式进入任务流
6. Deferred Issue 和 Micro-Fork 可以记录偏航问题

---

# 8. Phase 4：精准修改与局部 debug 闭环

## 8.1 Phase 4 的核心任务是什么

Phase 4 解决的是：

**系统终于开始真正“下手改代码”，并且能在失败时局部调试，而不是全文乱读、整文件重写。**

这是从“有计划”进入“能安全执行”的阶段。

---

## 8.2 为什么 patch / debug 必须放在最后

因为 patch 和 debug 是最容易失控的地方。  
如果你没有前面三阶段：

- Phase 0 的规则
- Phase 1 的骨架
- Phase 2 的 digest
- Phase 3 的 TaskPack / EditSpec / Goal Stack

那么一旦进入 patch / debug，小模型会马上出现：

- 定位不准
- 越界修改
- 反复 patch 同一错误
- 看到错误就重读整个文件
- 没有失败记忆，进入死循环

所以 Phase 4 之所以放最后，是因为它最危险。

---

## 8.3 Phase 4 应该做什么

### A. ASTReadTool
支持：
- file + symbol
- file + span
- file + anchor

这样 patch 不需要读整文件。

### B. strict patch
要求：
- exact-match-first
- backup / rollback
- patch preview
- 影响范围可控

### C. ask_user fallback
如果 patch 多次失败，不要硬改。  
必须进入用户确认或更高层裁决。

### D. traceback / stderr 清洗
只保留：
- exception type
- top frames
- relevant symbol
- last attempted fix

### E. verify / retry loop
每次 retry 前都必须：
- 重新锚定目标
- 检查是否仍在当前任务范围
- 检查是否已经重复失败

### F. Re-anchor Loop
在 patch 失败、路径失败、debug 失败时，把系统拉回：
- total goal
- step goal
- task goal
- current action

### G. Context Snapshot + Failure Memory
把：
- failed_attempts
- last_error
- next_action
- changed_files
- target symbol

写入 snapshot，防止恢复后失忆。

---

## 8.4 为什么这一步和你最初担心的“路径不存在反复思考”直接相关

因为你问的第二个关键问题，就是：

- 模型在 plan / debug 中会因为一个路径错误不断打转
- 中途切换任务
- 开始想别的事情

这恰恰说明：

**执行层不仅要能 patch，还要能在失败时回正。**

所以 Phase 4 不是单纯的 patch 阶段，而是：

**安全执行 + 局部 debug + 偏航恢复** 阶段。

---

## 8.5 Phase 4 完成后的标志

完成后应该具备：

1. ASTReadTool 可用
2. strict patch apply 可用
3. ask_user fallback 可用
4. traceback 清洗可用
5. verify / retry loop 可用
6. 连续路径错误和 patch 失败不会导致无限反复思考
7. 一次小范围修改任务可在不全文读文件的前提下完成

---

# 9. 为什么 Phase 5 和 Phase 6 现在不急

虽然你后面还会做：

- archive
- reconcile
- query-archive
- Obsidian / Git 运维

但对你当前阶段来说，这些都不是最优先。

因为你现在最缺的是：

1. 一套稳定不乱的制度层
2. 一条能真正跑通的执行主线
3. 一种让小模型省 token 还能不中途偏航的工作方式

所以现在把 Phase 0–4 讲透，已经足够让你开始真正迭代。

---

# 10. 从“新手实际操作”角度，该怎么理解这五个 Phase

这是最重要的一段。

如果你是新手，不要把这五个 Phase 看成“官方流程图”，你应该把它们理解成：

## Phase 0
先把规则讲清楚，不要急着写代码。

## Phase 1
先把新模式接进去，让项目知道“以后要怎么跑”。

## Phase 2
先让系统对代码形成局部理解，不要每次重新读整仓。

## Phase 3
先让系统围绕“当前任务”形成局部工作包，不要在 plan 里自由发散。

## Phase 4
最后才让系统真的去修改代码、调试错误，而且要带回正和恢复能力。

---

# 11. 最后总结

这份 Phase 0–4 路线图最想让你明白的一件事是：

**你不是在一步一步给系统加功能，而是在一步一步把它训练成一种适合 32K 小模型的工作方式。**

所以：

- Phase 0 决定它以后会不会乱
- Phase 1 决定它以后有没有骨架
- Phase 2 决定它以后会不会每次都重新学习
- Phase 3 决定它以后会不会围绕当前任务稳定思考
- Phase 4 决定它以后能不能真正安全地改代码和 debug

如果你把这五个 Phase 理解清楚，后面你再去看那些 `phase-*-exec.md`，就不会觉得它们只是“几条命令”，而能知道为什么它们必须这么窄、这么硬、这么分阶段。

---

## 12. 下一份文档应该是什么

按你已经确定的顺序，下一份应该写：

- `context-safeguard-full.md`

因为这是 v2.0 新增的第一块核心能力，而且它会直接影响你最关心的：
- OOM 预警
- 上下文脱水
- 快照恢复
- 省 token
