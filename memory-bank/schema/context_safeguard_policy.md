# Context Safeguard Policy

## 文档目的
本文件定义 **Context Safeguard（上下文保障）** 的正式规则边界。它约束系统在本地 32K 小模型场景下，如何进行：

- token 风险监控
- OOM 预警
- 上下文脱水（dehydration）
- 状态快照（context snapshot）
- 最小消息流恢复（resume）

本文件解决的是“什么时候该保护上下文、保护什么、不能做什么”，而不是具体实现细节。

---

## 一、适用范围
适用于以下模块或能力：
- `token_budget.py`
- `engine.py`
- `compact.py`
- `session.py`
- `knowledge/dehydrator.py`
- `wiki/logger.py` / `wiki/service.py`
- `TaskPack` / `Goal Stack` / `Retry Loop` 相关恢复逻辑

---

## 二、不适用范围
本文件不负责：
1. 具体 tokenizer 实现
2. 具体 LLM prompt 的措辞优化
3. 具体 checkpoint 序列化格式实现
4. 具体 UI 提示样式
5. 具体 archive / reconcile 算法

---

## 三、核心定义

### 1. Token Risk Monitor
用于监控当前上下文 token 使用率，并返回风险等级与建议动作。

### 2. Dehydration
不是普通摘要，而是：
> 将当前任务的高价值状态，从高体积消息流中抽取并压缩成可恢复状态。

### 3. Context Snapshot
上下文快照。必须至少分为两类：
- **Runtime Snapshot**：结构化、面向系统恢复
- **Markdown Snapshot**：高密度、面向人和后续 agent 理解

### 4. Resume
在上下文被压缩或重启后，利用 snapshot 重建最小消息流继续执行。

---

## 四、风险等级（正式规则）

系统必须至少支持以下五级风险：

- `safe`
- `watch`
- `warning`
- `critical`
- `emergency`

建议阈值：
- `safe`: `< 0.65`
- `watch`: `0.65 ~ 0.78`
- `warning`: `0.78 ~ 0.85`
- `critical`: `0.85 ~ 0.92`
- `emergency`: `> 0.92`

> 说明：阈值可在实现层调整，但等级体系本身必须固定。

---

## 五、不同等级必须做什么

### 1. safe
- 不做额外动作
- 正常运行

### 2. watch
- 输出 usage ratio
- 提醒减少大范围读取
- 不触发 snapshot

### 3. warning
- 限制长文件全文读取
- 优先清洗长 stderr / 长工具输出
- 提醒当前任务收窄目标

### 4. critical
必须执行：
1. 启动 dehydration
2. 生成 Runtime Snapshot
3. 生成 Markdown Snapshot
4. 写入 checkpoint 或等价运行时持久层
5. 写入 wiki/log 或等价长期记录层

### 5. emergency
必须执行：
1. 阻止新增大输入
2. 强制 snapshot
3. 强制最小上下文重建
4. 进入恢复模式而非继续追加原始长消息

---

## 六、触发点规则

Context Safeguard 不能只在一次 submit 前检查，至少应允许在以下位置触发：

1. **用户输入后**
2. **模型请求前**
3. **工具输出回填后**
4. **patch / debug retry 回合之间**

> 说明：是否所有触发点都在 MVP 中实现，可延后；但触发点集合本身必须在制度层承认。

---

## 七、Snapshot 最小内容要求

### A. Runtime Snapshot（最小字段）
至少应包含：
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

### B. Markdown Snapshot（最小结构）
至少应包含：
1. 当前任务目标
2. 已确认事实
3. 当前目标文件 / symbol
4. 已修改内容
5. 最近失败路径
6. 当前阻塞点
7. 下一步最合理动作
8. 恢复提示

---

## 八、必须保留的信息

系统在脱水时，必须优先保留以下高价值状态：

### 1. Goal 信息
- global goal
- step goal
- task goal
- current action

### 2. Localization 信息
- 当前目标文件
- 当前目标 symbol
- 当前已知 span / anchor

### 3. Change State
- 已改文件
- 已改位置
- 是否已落盘
- 是否已有 rollback 点

### 4. Failure Memory
- last_error
- failed_attempts
- 已验证无效的尝试路径

### 5. Next Action
- 下一步最小动作
- 必须先验证什么
- 当前明确不能做什么

---

## 九、必须丢弃或压缩的内容

Context Safeguard 的目标不是“全部保留”，而是“保留高价值状态、压缩低价值噪声”。

因此，以下内容必须优先压缩：
- 长 stderr 原文
- 重复 traceback
- 重复 grep 输出
- 大段 file read 原文
- 重复 patch preview
- 重复的自然语言解释

禁止做法：
1. 把长日志原样塞进 snapshot
2. 把全部中间历史强行摘要成大段自然语言
3. 恢复后重新读完整旧历史

---

## 十、持久化要求

### 最低要求
Context Snapshot 必须落到两处中的至少一处：
1. 运行时持久层（checkpoint / session snapshot）
2. 长期记录层（wiki/log）

### 推荐要求
同时写入：
- checkpoint
- `log.md`
- 可选 `reports/context_snapshots/`

---

## 十一、恢复规则

恢复时必须遵循：

1. **先读 snapshot，再决定下一动作**
2. 恢复后的消息流只保留最小必要内容：
   - system prompt
   - task identity
   - latest snapshot
   - latest goal stack
   - latest user instruction
3. 恢复后默认不重新全文读取项目
4. 恢复时优先从：
   - snapshot
   - taskpack
   - goal stack
   - digested pages
   出发

---

## 十二、与其他系统的关系

### 与 TaskPack 的关系
- TaskPack 是任务知识包
- Snapshot 是运行状态包
- 两者可相互引用，但不可互相替代

### 与 Goal Stack 的关系
- Snapshot 必须保留目标锚点引用
- 恢复后必须仍知道“为什么只能做当前动作”

### 与 Debug/Retry 的关系
- failed attempts 必须进入 snapshot
- retry 前可引用 snapshot 防止重复失败

---

## 十三、禁止事项

1. 禁止把 Context Safeguard 简化成“普通摘要功能”
2. 禁止只有单一阈值判断
3. 禁止只写 messages，不写外部状态
4. 禁止恢复时重新全文读旧历史
5. 禁止将长原文日志直接塞入 snapshot

---

## 十四、分阶段落地建议

### Phase 0
- 确立风险等级
- 确立 Snapshot 契约
- 确立恢复原则

### Phase 1
- 接入 usage ratio / risk level monitor
- 先只做 warning / critical 提示

### Phase 2
- 实现最小 dehydration
- 写出最小 Runtime Snapshot
- 写入 log / checkpoint

### Phase 3
- 让 TaskPack / Goal Stack / Snapshot 形成引用关系

### Phase 4
- 让 patch / debug / retry 与 Snapshot 闭环联动

---

## 十五、最终原则

**不要等模型彻底失忆后再去补救；要在它即将丢失任务连续性之前，先把当前任务的可恢复状态固化下来。**
