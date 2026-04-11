# Goal Policy

## 文档目的
本文件定义 **Goal Anchoring & Drift Recovery（目标锚定与偏航恢复）** 的正式规则边界。它约束系统在长任务、小上下文和多轮工具调用场景下，如何：

- 保持任务锚点
- 检测偏航
- 执行回正（re-anchor）
- 外部化延后问题
- 记录轻量分叉（micro-fork）

本文件解决的是“系统如何不跑偏”，而不是具体 prompt 写法。

---

## 一、适用范围
适用于：
- `/prime`
- `/plan`
- TaskPack
- EditSpec
- patch / debug / retry loop
- Context Snapshot 恢复逻辑
- 任务型工作流中的 ask_user fallback

---

## 二、不适用范围
本文件不负责：
1. 具体 CLI 命令语法
2. 具体 UI 提示文案
3. 具体 LLM prompt 模板的逐字实现
4. 具体 archive / reconcile 算法
5. 多 agent 并行调度

---

## 三、核心定义

### 1. Goal Stack
任务目标的正式层级对象。至少包含：
- `global_goal`
- `step_goal`
- `task_goal`
- `current_action`
- `done_definition`
- `out_of_scope`

### 2. Drift Detector
偏航检测器。用于识别系统是否正在偏离当前主线。

### 3. Re-anchor Loop
回正流程。用于在失败、偏航、恢复或重复试错时，把系统重新拉回任务主线。

### 4. Deferred Issue Log
延后问题记录。用于存放“当前发现但不该现在解决”的问题。

### 5. Micro-Fork Note
轻量分叉记录。用于外部化值得后续处理的支线问题，但不污染当前主线执行上下文。

---

## 四、Goal Stack 的正式规则

### 1. Goal Stack 是正式对象
它不是一句自然语言提示，也不是临时注释，而是当前任务流的正式输入。

### 2. Goal Stack 最小字段不可缺失
必须至少包含：
- `global_goal`
- `step_goal`
- `task_goal`
- `current_action`
- `done_definition`
- `out_of_scope`

### 3. Goal Stack 必须可被引用
至少应允许被以下对象引用：
- TaskPack
- EditSpec
- Context Snapshot
- Retry State

### 4. Goal Stack 必须在关键节点可见
至少在以下节点前可见：
1. `/prime`
2. `/plan`
3. patch 前
4. debug 前
5. retry 前
6. snapshot 恢复后

---

## 五、Drift Detector 的正式规则

系统必须承认“偏航”是正式状态，而不是临时现象。

### 最少应检测 5 类偏航

#### A. Path Drift（路径偏航）
表现：
- 连续读取不存在路径
- 连续在错误目录中搜索
- 围绕同一路径错误反复猜测

#### B. Scope Drift（范围偏航）
表现：
- 当前任务只允许改少量文件，却开始扩大范围
- 当前 Phase 只允许文档/规则操作，却开始写后续运行时代码

#### C. Problem Escalation Drift（问题升级偏航）
表现：
- 局部执行问题被提升为制度重构问题
- 当前是路径/patch 局部错误，却开始重定义后续 policy 或 phase

#### D. Repetition Drift（重复失败偏航）
表现：
- 同一 patch 连续失败
- 同一 grep / read / retry 连续失败
- 已失败路径被重复尝试

#### E. Context Drift（上下文偏航）
表现：
- 输出越来越长，但越来越远离 current action
- 把 deferred issue 当成当前任务处理
- 不断拉回后续阶段问题

---

## 六、Re-anchor Loop 的正式规则

### 1. 检测到偏航时，不能只提示，必须回正
系统必须有正式的回正动作。

### 2. Re-anchor Loop 的固定问题
建议至少包含以下 6 问：
1. 当前总目标是什么？
2. 当前步骤目标是什么？
3. 当前子任务目标是什么？
4. 当前失败属于哪个层级的问题？
5. 这个失败是否值得切换任务？
6. 如果不值得，下一步最小动作是什么？

### 3. 触发场景
至少以下场景允许或要求触发 Re-anchor：
- 路径错误连续出现
- patch 失败连续出现
- debug retry 前
- snapshot 恢复后
- 检测到越界讨论时

---

## 七、Deferred Issue Log 的正式规则

### 1. 延后问题必须外部化
凡是当前发现、但不属于本阶段 / 本步骤 / 本任务立即处理范围的问题，必须进入 Deferred Issue Log。

### 2. 进入 Deferred Issue 后，默认当前不处理
除非用户显式要求或后续 phase 重新激活，否则当前任务流不得继续扩写它。

### 3. Deferred Issue 至少应包含
- `issue_id`
- `source_phase`
- `source_step`
- `source_task`
- `reason`
- `status`
- `next_owner`
- `resume_condition`

### 4. 典型适用场景
- 当前步骤中发现后续阶段的制度问题
- 当前任务中发现应该在后续统一处理的结构问题
- 当前 patch/debug 中发现应回到 ChatGPT 或规则层裁决的内容

---

## 八、Micro-Fork Note 的正式规则

### 1. 为什么需要 Micro-Fork
系统允许“记录后续值得处理的问题”，但不允许在主上下文里真正并行展开多个大分支。

### 2. Micro-Fork 是轻量分叉，不是重会话并行
它应当：
- 外部化
- 可恢复
- 不污染当前主线

### 3. 最小字段
至少包含：
- `fork_id`
- `source_step`
- `source_task`
- `reason`
- `status`
- `next_owner`
- `resume_condition`

### 4. 禁止事项
- 禁止把 Micro-Fork 当成完整并行 agent 分支
- 禁止在 32K 小模型主消息流中同时保留多个重分叉上下文

---

## 九、与 TaskPack / EditSpec 的关系

### 与 TaskPack 的关系
TaskPack 负责“当前任务的最小知识包”，而 Goal Stack 负责“当前任务的方向锚点”。

规则：
1. TaskPack 必须引用 Goal Stack
2. 没有 Goal Stack 的 TaskPack 不能视为完整任务预热结果
3. 当前任务的 `out_of_scope` 应能被执行器读取

### 与 EditSpec 的关系
EditSpec 负责结构化修改意图，Goal Stack 负责限制 EditSpec 不越界。

规则：
1. EditSpec 应支持 `goal_guard`
2. `goal_guard` 至少应引用当前 step goal 和 out_of_scope

---

## 十、与 Context Safeguard 的关系

Goal Anchoring 与 Context Safeguard 必须联动：

1. Snapshot 必须保留 Goal Stack 引用
2. Snapshot 恢复后必须先 Re-anchor，再继续下一动作
3. failure memory 与 next action 不可脱离 goal stack 独立存在

---

## 十一、执行纪律

### 1. 任何任务都必须具备三层以上目标
至少要有：
- 总目标
- 当前步骤目标
- 当前子任务目标

### 2. 当前动作失败，不等于整个任务失败
系统应优先修正 current action，而不是立即切换 task goal 或 step goal。

### 3. 发现后续阶段问题时，优先写入 deferred issue
而不是立刻把当前任务升级成未来问题。

### 4. 重复失败必须熔断
相同失败模式重复 >= 2 次时，必须触发：
- Re-anchor
- ask_user
- deferred issue
三者之一

---

## 十二、禁止事项

1. 禁止把 Goal Anchoring 简化成“一句任务提醒”
2. 禁止把 Drift Detector 仅仅当成人工观察结果
3. 禁止在未记录 deferred issue 的情况下继续扩写后续问题
4. 禁止真正用重上下文并行 fork 替代 Micro-Fork
5. 禁止 patch/debug/retry 在没有 Goal Stack 的情况下自由推进

---

## 十三、分阶段落地建议

### Phase 0
- 确立 Goal Stack / Drift Detector / Re-anchor / Deferred Issue / Micro-Fork 契约

### Phase 1
- 在 wiki_strict 初始化时接入最小 Goal Stack 占位

### Phase 2
- 在 scan/digest 中接入最小 drift check

### Phase 3
- 让 `/prime` 和 `/plan` 输出正式 Goal Stack / Deferred Issue / Micro-Fork

### Phase 4
- 让 patch / debug / retry 与 Goal Stack / Drift Detector / Re-anchor 闭环联动

---

## 十四、最终原则

**不要只让模型知道“它现在在做什么”，还要让它知道“为什么现在只能做这件事”。**
