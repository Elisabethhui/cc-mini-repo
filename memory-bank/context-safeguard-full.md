# Context Safeguard Full

版本：v2.0 Full Topic  
日期：2026-04-11  
适用对象：cc-mini 框架升级 / 本地 32K 小模型 / 长会话任务 / Claude Code + ChatGPT 协作开发

---

## 1. 文档目的

这份文档专门讲清楚 v2.0 中新增的第一块核心能力：

**Context Safeguard（上下文保障）**

它不是一个小补丁，也不是“顺手加一个 summary 功能”，而是一个真正影响系统长期可用性的横切能力。

这份文档要回答的问题包括：

1. 为什么本地 32K 小模型在长任务里一定会遇到上下文风险？
2. 为什么原有的 compact / should_compact / checkpoint 思路不够？
3. 为什么“快 OOM 时做一个对话摘要”并不能真正解决问题？
4. 什么叫“上下文脱水（Dehydration）”？
5. 什么叫“Context Snapshot”？
6. Snapshot 应该包含什么内容，为什么不能只保留自然语言摘要？
7. 这个能力应该挂在哪些模块里，而不是变成一个孤零零的新函数？
8. 它和 TaskPack、Goal Stack、patch、debug、retry 的关系是什么？
9. 作为新手，为什么你应该优先理解它，而不是先学更炫的插件和自动化？

---

## 2. 问题背景：为什么 32K 小模型一定会出事

### 2.1 真正的瓶颈不是“模型不会写”，而是“模型记不住”

很多人第一次用本地小模型做编程时，会先觉得问题是：

- 模型推理能力不够
- 模型代码能力不如大模型
- 模型语言风格不稳定

这些都是真的，但对你当前这个项目来说，最致命的问题通常不是这些，而是：

**上下文容量太小，导致它在长任务里无法保持连续性。**

你现在的目标不是让模型写一小段独立函数，而是让它在一个已有仓库中：

- 理解原有结构
- 理解你后加的设计规则
- 保持当前步骤边界
- 做局部修改
- 做局部 debug
- 出现错误时还能继续推进

这就意味着，小模型要在一个会话里同时记住：

- 当前总目标
- 当前阶段目标
- 当前这一步具体在做什么
- 读过哪些文件
- 哪些结论已经确认
- 哪些结论还只是推测
- 哪些 patch 已经失败
- 哪条路不应该再试
- 当前 message 历史里还有哪些工具输出

对 32K 小模型来说，这不是“很难”，而是**必然会顶满**。

---

### 2.2 为什么编程任务比普通聊天更容易 OOM

因为编程任务会产生三类特别耗上下文的内容：

#### A. 大块原始材料
例如：
- 长代码文件
- 多个函数实现
- 长 Markdown 设计文档
- 长 stderr / traceback
- 配置文件、schema 文件

#### B. 工具输出垃圾
例如：
- grep 返回几十行
- bash 报错堆一大段
- 文件读取读太多
- patch preview 过长
- 重试过程中重复输出类似内容

#### C. 隐形状态
最可怕的不是显式文本，而是模型“必须记住但没有正式保存”的状态：

- 当前在改哪个 symbol
- 当前 patch 为什么失败
- 上一轮 debug 猜过什么
- 当前应该往前还是停下来
- 用户已经明确说过哪些边界

这些东西如果没有结构化保存，就只能寄存在上下文里。  
而寄存在上下文里的东西，一旦 compact 或换轮，就很容易丢掉。

---

### 2.3 对你这个项目来说，OOM 不只是“报错”，而是“逻辑断裂”

很多人以为 OOM 的坏处只是：

- 请求失败
- token 超了
- 模型停止响应

但你这个项目更大的问题是：

**逻辑连续性会断。**

例如：
- 它明明已经定位到 `Engine.submit`
- 已经知道 patch 不该整文件改
- 已经知道当前 Step 只允许碰 `memory-bank/templates/`
- 已经知道某个路径不存在，不该继续猜

结果上下文一压缩或一重启，它把这些状态都忘了。  
于是：

- 又去重新读同一个文件
- 又重新踩同一个错误
- 又开始问之前已经回答过的问题
- 又开始发散到别的阶段

所以你要防的不是单纯的“超 token”，而是：

**超 token 导致的任务连续性断裂。**

---

## 3. 为什么原有做法不够

### 3.1 原有思路：被动压缩
在很多系统里，处理上下文过长的做法通常是：

1. 检测当前消息太长
2. 删掉一些旧消息
3. 对中间历史做一段摘要
4. 保留最近几轮
5. 继续往下聊

这在大模型环境下有时还能凑合。  
因为 128K、200K 模型本来就有比较大容错空间。

但在 32K 场景里，这种做法不够。

---

### 3.2 为什么“简单摘要”不够

假设你让模型在 OOM 前总结一句：

> “当前我们在修 engine.py 的 bug，已经做了一些尝试，下一步继续 patch。”

这句话看起来像有用，但真正恢复时你会发现它几乎没法直接工作。

因为你缺失了最关键的东西：

- 到底是哪个函数？
- 当前 symbol 是什么？
- 上一次失败是 exact match 失败还是路径错误？
- 已修改了哪些文件？
- 当前是否已经进入 ask_user fallback？
- 之前哪条路已经证明无效？
- 当前 patch 计划在哪个 anchor 上？

这些东西不是“长摘要”自然能补出来的。  
因为很多时候，模型自己也没有把这些内容结构化保存，它只能凭印象讲个大概。

而对小模型来说，“大概”就意味着：
- 会补
- 会猜
- 会糊
- 会把旧错误再做一遍

---

### 3.3 为什么“删中间，留头尾”不够

这种做法的逻辑是：

- 头部保留 system prompt
- 尾部保留最近几轮
- 中间变成摘要

问题在于，对编程任务来说，最有价值的信息经常不一定在“尾部”，而在：

- 中途某次读文件的定位结论
- 某次 patch 失败的原因
- 某次用户明确给的边界
- 某次已经回答过的 TaskPack 决策
- 某次路径错误后得出的 repo 真实结构

这些如果只是放在“中间历史”里，然后被粗暴压缩掉，逻辑就断了。

所以真正需要保留的，不是按时间位置保留，而是按**任务价值保留**。

---

## 4. Context Safeguard 的真正定义

Context Safeguard 不是“压缩服务”，也不是“总结器”。  
它应该被定义成：

> **在上下文风险升高时，主动提取当前任务的可恢复状态，把它固化到外部记忆层，并用最小消息流恢复继续执行的系统能力。**

这个定义里有 4 个关键词：

### 1. 风险升高时
说明它不是只在崩掉以后救火，而是应该提前预警。

### 2. 可恢复状态
说明它不是随便写点总结，而是要保留“能恢复”的最小必要信息。

### 3. 固化到外部记忆层
说明它不能只存在于当前 messages 里，而必须写到：
- checkpoint
- wiki/log
- snapshot 页面

### 4. 最小消息流恢复继续执行
说明它最终目的是：
- 不让当前任务断掉
- 不让恢复后的 agent 从头猜
- 不让它无限重复旧错误

---

## 5. Context Safeguard 的完整目标

这个子系统至少要达成 6 个目标：

### 目标 1：提前知道“快炸了”
不仅知道已经超了，还要知道“正在接近危险区”。

### 目标 2：在危险区里主动抽取最关键状态
不是被动删历史，而是主动保存“最值钱的信息”。

### 目标 3：保护任务连续性
恢复后仍然知道：
- 当前在做什么
- 已经做到哪
- 下一步应该干什么

### 目标 4：保护失败记忆
恢复后不能再重复试同一条已经失败的路。

### 目标 5：保护目标锚点
恢复后不能忘记：
- 当前总目标
- 当前步骤目标
- 当前子任务目标

### 目标 6：减少未来 token 浪费
恢复后的 agent 不应该重新去全文读一遍项目。

---

## 6. Context Safeguard 不是单一功能，而是 4 个子能力

### 6.1 Token Risk Monitor
负责判断当前离 OOM 还有多远。

### 6.2 Dehydrator
负责从当前运行状态中抽取“可恢复信息”。

### 6.3 Snapshot Writer
负责把快照写到外部状态层。

### 6.4 Resume Builder
负责在消息流被压缩后，重新构造可继续执行的最小上下文。

---

## 7. Token Risk Monitor：为什么不能只做一个阈值

### 7.1 单阈值思路的问题
如果系统只有一个判断：

- 超过 85% 触发 compact

那么它经常已经太晚了。

为什么？因为在编程任务里，token 的增长不是平滑的。  
很多时候是突然暴涨：

- 一次长 stderr
- 一次长代码读取
- 一次 patch preview
- 一次长 traceback
- 一次 plan 输出过长

于是你可能上一刻还在 70%，下一轮回填后直接冲到 95%。

---

### 7.2 建议使用多级风险等级

建议分成 5 档：

#### safe
`< 0.65`
- 不做动作
- 正常运行

#### watch
`0.65 ~ 0.78`
- 控制台提示 usage ratio
- 开始提醒避免大范围读取

#### warning
`0.78 ~ 0.85`
- 禁止长文件全文读取
- 对长 stderr 先清洗
- 计划时提醒收窄目标

#### critical
`0.85 ~ 0.92`
- 必须触发 dehydration
- 生成 snapshot
- 准备重建最小消息流

#### emergency
`> 0.92`
- 停止新增大输入
- 强制 snapshot
- 强制上下文重启

---

### 7.3 风险等级不只是数值，更应该返回“建议动作”
不是只返回一个 ratio，而应该返回：

- 当前等级
- 风险原因
- 建议动作

例如：

```yaml
risk_level: critical
token_ratio: 0.89
causes:
  - long stderr retained
  - repeated file reads
  - pending patch preview
recommended_actions:
  - dehydrate now
  - trim stderr
  - block full file reads
```

这样系统后面才能按策略处理，而不是只会打印数字。

---

## 8. Dehydration：什么叫“上下文脱水”

### 8.1 为什么叫脱水
因为你不是把信息删掉，而是把它从“高体积、低密度、不可恢复”的状态，转成“低体积、高密度、可恢复”的状态。

原始 messages 很像“含水量很高”的文本：
- 很长
- 很重复
- 很多噪声
- 很多工具输出其实价值不高

而脱水后的 snapshot 应该像“浓缩精华”：
- 很短
- 重点清楚
- 任务可恢复
- 不丢关键标识

---

### 8.2 脱水不是摘要
这是最重要的概念区分。

#### 摘要
更像：
- 对话说了什么
- 整体聊到了什么

#### 脱水
更像：
- 当前任务是什么
- 任务做到哪了
- 哪个文件 / symbol 是当前目标
- 哪些改动已经落地
- 当前错误是什么
- 哪些尝试失败过
- 下一步最小动作是什么
- 恢复时该先读什么，别再试什么

也就是说：

**摘要偏“复述内容”**  
**脱水偏“提取任务状态”**

---

## 9. Context Snapshot：为什么必须分成两份

### 9.1 只用自然语言快照不够
自然语言快照的问题是：
- 可读性好
- 但可恢复性不稳定

### 9.2 只用结构化快照也不够
结构化快照的问题是：
- 机器好处理
- 但人类理解成本高
- 后续 agent 也不一定能直接高质量利用

所以建议快照分两份：

---

### A. Runtime Snapshot
这是机器优先的。

至少包含：

- `session_id`
- `task_id`
- `mode`
- `phase`
- `step`
- `active_goal`
- `goal_stack_ref`
- `target_files`
- `primary_symbols`
- `related_symbols`
- `changed_files`
- `last_error`
- `failed_attempts`
- `next_action`
- `risk_level`
- `token_ratio`
- `created_at`

它的价值在于：
- 便于恢复
- 便于做系统判断
- 便于后续写 checkpoint / log / state files

---

### B. Markdown Snapshot
这是人和后续 agent 优先的。

建议固定 8 段：

1. 当前任务目标
2. 已确认事实
3. 当前目标文件 / symbol
4. 已修改内容
5. 最近失败路径
6. 当前阻塞点
7. 下一步最合理动作
8. 恢复提示

它的价值在于：
- 便于阅读
- 便于手工审查
- 便于恢复会话时快速理解

---

## 10. Snapshot 里必须保留哪些信息

这是最关键的部分。

### 10.1 Goal 信息
必须保留：
- global goal
- step goal
- task goal
- current action

为什么？
因为不保留目标锚点，恢复后的 agent 最容易重新发散。

---

### 10.2 Localization 信息
必须保留：
- 当前目标文件
- 当前目标 symbol
- 当前已知 span / anchor

为什么？
因为这决定了 patch/debug 是否还能继续局部化。

---

### 10.3 Change State 信息
必须保留：
- 已改文件
- 已改位置
- 是否已落盘
- 是否已有 rollback 点

为什么？
否则恢复后的 agent 可能以为还没改，或重复改同一位置。

---

### 10.4 Failure Memory
必须保留：
- last_error
- failed_attempts
- 哪些思路已失败
- 哪些 patch 已失败

为什么？
因为这直接决定会不会死循环。

---

### 10.5 Next Action
必须保留：
- 下一步最小动作
- 必须先验证什么
- 当前不能做什么

为什么？
因为恢复时最重要的问题是：“下一步到底该干嘛？”

---

## 11. 写到哪里：外部状态层的落点设计

### 11.1 Checkpoint
用于系统恢复。

特点：
- 面向运行时
- 适合快速 resume
- 不一定人类可读性最强

### 11.2 Wiki Log
用于长期记忆和审计。

建议：
- 追加写入 `.cc-mini/wiki/log.md`

记录：
- 触发时间
- 风险等级
- 快照摘要
- 为什么发生
- 下一步恢复指向

### 11.3 Reports / Context Snapshots
用于高价值归档。

建议目录：
```text
.cc-mini/wiki/reports/context_snapshots/
```

适合：
- 长任务中间态
- 复杂 debug 过程
- 多轮 patch 尝试
- 需要保留失败路径的任务

---

## 12. 恢复时怎么继续，不是怎么“聊天继续”

这是很多系统设计里最容易犯的错。

错误想法是：

> 生成个总结，塞回消息里，继续聊。

但你现在要的是继续执行任务，不是继续聊天。

所以恢复时必须做 3 件事：

### 12.1 只保留最小消息流
恢复后的 messages 应只保留：

- system prompt
- 当前 task identity
- 当前 goal stack
- 最新 snapshot
- 最近一次用户指令

不要把旧历史再整段带回来。

---

### 12.2 先加载 snapshot，再决定下一动作
恢复时不要先继续工具调用。  
第一步应该是：

- 先读 snapshot
- 确认当前 goal
- 确认当前 target
- 确认 last_error / failed_attempts
- 再决定下一动作

---

### 12.3 默认不要重新全文读项目
如果 snapshot 还有效，恢复时应该先从：
- snapshot
- goal stack
- taskpack
- digested entities
出发，而不是重新 file read。

---

## 13. Context Safeguard 应该挂在哪些模块里

它不应该变成单独一个函数，而是横切接入。

### 13.1 `token_budget.py`
负责：
- usage ratio
- risk level
- recommended action

### 13.2 `engine.py`
负责：
- 在关键节点调用 risk check
- critical / emergency 时触发 dehydrator
- 用 snapshot 重建最小消息流

### 13.3 `compact.py`
负责：
- 长 stderr / tool outputs 的机械减肥
- 为 dehydrator 提供更干净输入

它不是最终的智能状态提炼器，而是预处理器。

### 13.4 `knowledge/dehydrator.py`
负责：
- 提取结构化状态
- 调用 LLM 生成高密度 snapshot
- 返回 snapshot 对象

### 13.5 `session.py`
负责：
- 保存 snapshot
- 加载 snapshot
- resume from snapshot

### 13.6 `wiki/logger.py` 或 `wiki/service.py`
负责：
- 写 log
- 写 snapshot reports
- 让 snapshot 成为长期记忆的一部分

---

## 14. 与 TaskPack / Goal Stack 的关系

### 14.1 与 TaskPack 的关系
TaskPack 是“当前任务的局部知识包”，  
Snapshot 是“当前会话的恢复状态包”。

它们不同，但应该相互引用：

- TaskPack 可以引用最近 snapshot
- Snapshot 可以记录当前 taskpack_ref

这样恢复时就知道：
- 当前任务知识包是谁
- 当前执行状态在哪里

---

### 14.2 与 Goal Stack 的关系
Goal Stack 是“为什么做这件事”的锚点，  
Snapshot 是“做到哪了”的状态固化。

所以 Snapshot 里必须带 Goal Stack 引用。  
否则恢复后的 agent 只知道状态，不知道方向。

---

## 15. 与 patch / debug 的关系

### 15.1 patch 场景
在 patch 过程中，最该保留的是：
- 当前目标 symbol
- patch preview
- exact-match 是否失败
- fallback 是否已触发
- 当前 changed_files

### 15.2 debug 场景
在 debug 过程中，最该保留的是：
- last_error
- top frames
- cleaned traceback
- failed_attempts
- last attempted fix
- next_action

因为 debug 任务最容易反复试错，最需要失败记忆。

---

## 16. 新手最容易犯的 5 个错

### 错误 1：把 Context Safeguard 理解成摘要功能
实际上它是：
- 风险监控
- 状态提取
- 外部固化
- 最小恢复

### 错误 2：只做一个 bool 阈值
这样会太晚。

### 错误 3：只把 summary 塞回 messages，不写外部状态
这样一旦再次 compact 或换 agent，又丢了。

### 错误 4：snapshot 过长
如果你把长 stderr、长 traceback 都塞进去，那又回到了大文本垃圾场。

### 错误 5：恢复时重新全文读取
这样 Context Safeguard 就白做了。

---

## 17. 对你当前项目最实用的落地顺序

你现在不用一步做到满。  
最合理的是三层落地。

### 第一步：最小可用版
先做：
- usage ratio
- risk level
- critical 时生成一次最小 snapshot
- 写入 checkpoint + log

### 第二步：任务感知版
再做：
- snapshot 和 TaskPack / Goal Stack 串起来
- debug / retry 中保留 failure memory
- 恢复时先读 snapshot

### 第三步：长期 wiki 融合版
最后做：
- context snapshot archive
- query-archive
- reconcile 时参考旧 snapshot
- 失败路径复用

---

## 18. 你为什么现在应该先理解这个，而不是先折腾插件

因为这直接关系到你之后用 Claude Code / cc-mini 的体验：

- 你会不会总觉得模型“越来越笨”
- 它会不会中途失忆
- 它会不会重复踩坑
- 你会不会不断重述背景
- 你会不会花大量 token 在无意义重复上

所以 Context Safeguard 不是高级优化，而是你这套系统能不能长期稳定工作的底线。

---

## 19. 最后总结

这块能力最核心的一句话是：

**不要等模型炸了再去救，要在它快失忆的时候，先把当前任务的可恢复状态保存下来。**

Context Safeguard 的意义不在于“压缩更多文本”，而在于：

- 把高价值状态留住
- 把低价值噪声丢掉
- 让任务还能继续
- 让后续 agent 接得上
- 让 32K 小模型真正能承担长任务

---

## 20. 下一份应该写什么

按你已经确认的顺序，下一份应该写：

- `goal-anchoring-full.md`

因为现在你已经理解了“怎么防止上下文爆炸”，  
接下来就该理解“怎么防止任务偏航”。 
