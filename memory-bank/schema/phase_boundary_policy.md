# Phase Boundary Policy

## 文档目的
本文件定义 v2.0 中 **Phase 0–Phase 4** 的正式边界。它用于防止：

- 跨阶段提前实现
- 当前步骤把后续 phase 问题提前拉进来
- 小模型在 plan / modify / debug 中混做多个层级任务

本文件回答的是：
- 每个 Phase 解决什么问题
- 每个 Phase 允许做什么
- 每个 Phase 明确不做什么
- 发生跨阶段冲突时如何处理

---

## 一、总原则

### 1. 阶段隔离
每次只允许执行一个 Phase，不允许把多个 Phase 的核心能力揉成一次任务。

### 2. 规则先于实现
Phase 0 未完成前，不允许开始后续业务逻辑实现。

### 3. 骨架先于语义
Phase 1 未完成前，不允许声称 digest/taskpack/patch 已进入可用状态。

### 4. 语义先于任务预热
Phase 2 未完成前，不允许把 TaskPack 当成正式可靠的局部熟知识包。

### 5. 任务预热先于 patch/debug
Phase 3 未完成前，不允许 patch/debug 成为正式主流程。

---

## 二、Phase 0：规则与契约定稿

### 核心任务
确定制度层：
- frontmatter
- 页面状态
- schema 规则层
- Context Safeguard 契约
- Goal Anchoring 契约
- Phase 边界本身

### In Scope
1. 规则文件
2. 模板文件
3. 概念定义
4. 元数据契约
5. 状态解释
6. 阶段边界解释

### Out of Scope
1. 不写业务逻辑代码
2. 不实现 `/scan`、`/digest`、`/prime`
3. 不实现 patch / debug / retry
4. 不实现 archive / reconcile

### 当前阶段可产出
- `schema/*.md`
- 模板文件
- 目录规范文件
- 记录文件更新

---

## 三、Phase 1：模式接入与结构骨架

### 核心任务
让 `wiki_strict` 正式接入系统，并建立运行时 wiki 骨架。

### In Scope
1. `--mode wiki_strict`
2. `RunMode`
3. `.cc-mini/wiki/` 初始化
4. `index.md` / `log.md`
5. raw_ast entities
6. watcher stale 标记骨架
7. token risk monitor 最小版
8. Goal Stack 占位对象

### Out of Scope
1. 不实现真正 digest
2. 不实现正式 TaskPack / EditSpec
3. 不实现 patch / debug
4. 不实现完整 dehydration
5. 不实现 archive / reconcile

### 跨阶段禁止
- 禁止在 Phase 1 中实现真正的语义 digest
- 禁止在 Phase 1 中做 patch / strict apply
- 禁止在 Phase 1 中把 token warning 当作完整 Context Safeguard

---

## 四、Phase 2：语义消化与状态升级

### 核心任务
让 raw_ast 变成可操作知识页，并开始最小上下文保障闭环。

### In Scope
1. `/scan`
2. `/digest`
3. `/digest --changed`
4. raw_ast -> partially_digested / digested
5. 最小 `dehydrator.py`
6. 最小 Runtime Snapshot
7. 最小 drift check

### Out of Scope
1. 不实现正式 TaskPack / EditSpec
2. 不实现 `/prime`
3. 不实现 ASTRead / strict patch
4. 不实现完整 debug / retry
5. 不实现 archive / reconcile

### 跨阶段禁止
- 禁止在 Phase 2 中把 digest 产物直接当完整 TaskPack
- 禁止在 Phase 2 中进入 patch/debug 主流程
- 禁止在 Phase 2 中把 snapshot 扩展成完整长期 archive 系统

---

## 五、Phase 3：任务预热与结构化计划

### 核心任务
让系统围绕“当前任务”形成最小知识包与结构化计划。

### In Scope
1. TaskPack
2. EditSpec
3. `/prime`
4. wiki_strict 下 `/plan`
5. Goal Stack 正式对象
6. Deferred Issue Log
7. Micro-Fork Note
8. flow_state 强化

### Out of Scope
1. 不实现真正 patch apply
2. 不实现 ASTReadTool 正式代码级读取
3. 不实现完整 debug/retry 闭环
4. 不实现 archive / reconcile / query-archive

### 跨阶段禁止
- 禁止在 Phase 3 中把 `/plan` 退化成整文件代码生成器
- 禁止在 Phase 3 中直接执行 patch
- 禁止在 Phase 3 中提前做 archive/reconcile 设计闭环

---

## 六、Phase 4：精准修改与局部 debug 闭环

### 核心任务
让系统进入真正可控的局部执行阶段：
- ASTRead
- strict patch
- ask_user fallback
- traceback 清洗
- verify/retry
- Re-anchor Loop

### In Scope
1. ASTReadTool
2. strict file_edit / patch apply
3. patch preview / rollback
4. ask_user fallback
5. traceback 清洗
6. verify/retry loop
7. Drift Detector + Re-anchor 在 patch/debug 中闭环联动
8. failure memory 与 snapshot 在 debug/retry 中联动

### Out of Scope
1. 不实现 archive / reconcile / query-archive
2. 不实现 Obsidian / Git 深度运维
3. 不做全仓级修改，只做局部 patch

### 跨阶段禁止
- 禁止在 Phase 4 中顺手实现 Phase 5 的知识复利功能
- 禁止把全仓搜索和整文件重写包装成“局部 patch”
- 禁止 patch/debug 在没有 Goal Stack / TaskPack 的情况下自由推进

---

## 七、跨阶段冲突的处理规则

### 1. 当前阶段发现后续阶段问题
处理方式：
- 写入 Deferred Issue
- 不继续在当前阶段扩写

### 2. 当前阶段需要后续阶段能力才能继续
处理方式：
- 立即停止
- 明确说明“当前阻塞源于阶段边界”
- 不得强行提前实现

### 3. 当前阶段发现旧阶段规则不足
处理方式：
- 若属于制度层缺口，回到 Phase 0 / schema 进行补充
- 不允许在执行层临时发明规则替代 schema

---

## 八、执行器使用规则

1. 一次只读取一个 Phase 文件作为主执行依据
2. 当前 Phase 未通过验收前，不得进入下一 Phase
3. 当前 Phase 若出现后续阶段问题，优先 deferred issue，而不是升级实现范围
4. 当前 Phase 的 runner docs 不得替代 Human Docs 作为长期总纲

---

## 九、为什么本文件重要

对于本地 32K 小模型来说，阶段边界不是“文档好看”，而是控制系统不乱的关键机制。

没有 Phase Boundary Policy，会出现：
- 规则层和实现层混做
- patch 与 plan 混做
- 当前任务与未来问题混做
- 小模型把“想到的问题”都当成立刻要解决的问题

本文件的本质作用是：

**让系统在任何时刻都知道：现在该做什么，不该做什么，哪些问题应该留到后面。**

---

## 十、最终原则

**阶段边界不是开发节奏建议，而是防止小模型失控、越界和浪费 token 的正式控制机制。**
