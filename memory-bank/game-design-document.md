# Game Design Document

> 说明：本项目并非传统“游戏”，但为了严格兼容你当前这套工作流与文件命名约定，仍沿用 `game-design-document.md` 作为核心设计文档文件名。其实际内容是 **cc-mini Wiki-Strict 模式升级项目的产品/系统设计文档**。

## 1. 项目名称

**CC-MINI Wiki-Strict 模式升级项目**

## 2. 一句话核心

在不破坏 cc-mini 原有 `standard` 模式的前提下，增量接入一套面向本地 32K 小模型的 `wiki_strict` 模式，使系统能够优先基于 Wiki 中间层完成代码审阅、定点修改、局部 debug 与知识沉淀，从而避免大代码库和长文档任务中的 OOM 与上下文失控问题。

## 3. 项目背景

当前 cc-mini 在强模型场景下可直接工作，但对本地 32K 小模型存在明显瓶颈：

- 大文件、跨模块、多轮任务时容易 OOM。
- 工具调用和临时推理历史会快速撑满上下文，导致“失忆”。
- 单靠实时检索，模型每次都要回到原始材料重新拼装知识，成本高且不稳定。
- 只有 AST 或 tree-sitter 的结构地图仍然不够，真正改代码时仍会被迫重新读大量源码。

因此，需要在 cc-mini 内部增加一条适合小模型的受控工作流：

**结构扫描 → 语义消化 → 任务预热 → 精准定位 → 局部 patch → 局部 debug → Wiki 沉淀与运维**

## 4. 设计目标

### 4.1 核心目标

1. 避免本地 32K 小模型在大代码库/长文档任务中 OOM。
2. 让系统优先基于 Wiki 中间层工作，而不是频繁通读 Raw Sources。
3. 在知识库碎片化的情况下，仍支持代码审阅、定点修改和局部 debug。
4. 将高价值分析结果与任务经验持续沉淀为 Markdown Wiki，形成知识复利。
5. 全部升级逻辑通过 `flag / mode` 方式融入 cc-mini，与原有 `standard` 模式并存。

### 4.2 成功判定

若第一轮 MVP 达成以下结果，则视为阶段成功：

- `wiki_strict` 模式可启动，且不破坏 `standard` 模式。
- 系统能够为 demo 项目生成 Wiki 骨架。
- 系统可基于 digest 后的局部知识完成一次单函数级别的 Review 或 Modify。
- 修改任务不依赖整文件重写，而是通过局部 patch 完成。
- 多轮 debug 过程中，上下文仍保持可控。

## 5. 非目标（当前阶段明确不做）

当前阶段不追求以下内容：

- 不重写 cc-mini 主架构。
- 不做“一口气完整消化整个项目”的全量知识库。
- 不让小模型一开始全文阅读整个仓库。
- 不允许默认整文件重写式代码生成。
- 不让 Watchdog 自动执行高成本、不可控的大规模语义总结。
- 不做无回滚保障的自动写入。
- 第一轮不优先做 Obsidian/Git 的深度美化与高级运维体验。

## 6. 目标用户

### 6.1 主要用户

- 使用 cc-mini 的开发者
- 需要在本地部署 32K 小模型的开发者
- 需要处理中大型代码库但上下文窗口有限的工程用户

### 6.2 典型使用场景

1. **代码审阅**：只围绕目标 symbol 与少量依赖进行局部理解和风险分析。
2. **定点修改**：先做任务级语义消化与定位，再对局部代码生成 patch。
3. **局部调试**：围绕 traceback 清洗后的关键调用栈进行补 digest、定位与修复。
4. **知识沉淀**：把高价值结论回写到 Wiki 页面，减少后续重复阅读成本。

## 7. 核心设计原则

### 7.1 模式隔离

保留两个主模式：

- `standard`：原有流程，尽量不动。
- `wiki_strict`：小模型增强模式，采用严格的分层与状态机流程。

### 7.2 Wiki First

在 `wiki_strict` 模式下，系统应优先读取：

1. `index.md`
2. 已 `digested` 的 entity / concept 页面
3. Task Pack
4. 少量目标 symbol 的源码切片

而不是一开始通读整个文件。

### 7.3 结构与语义分层

必须把工作拆成：

- 结构测绘
- 语义消化
- 任务预热
- 目标定位
- 局部修改
- 局部验证

### 7.4 计划、定位、修改、验证分离

小模型不应在一轮里同时承担：

- 全局理解
- 修改规划
- 代码生成
- 报错分析
- 回归检查

而应通过状态机分阶段执行。

## 8. 核心工作流

### 8.1 统一主流程

```text
User Request
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
Verify / Reconcile
  ↓
Wiki Update / Archive
```

### 8.2 Review 流程

1. 找相关 entity / concept 页面
2. 若页面是 `raw_ast`，先局部 digest
3. 只读目标 symbol 及少量依赖
4. 输出风险点、潜在 bug、重构建议

### 8.3 Modify 流程

1. `/plan` 解析任务
2. 生成 Task Pack
3. Target Localization
4. 生成 EditSpec
5. 局部 patch 生成
6. strict apply
7. verify
8. 失败时返回 task pack / patch，而不是重新读全项目

### 8.4 Debug 流程

1. 捕获并清洗 traceback
2. 定位错误 symbol
3. 若摘要不够，先补 digest
4. 只读出错点周边切片
5. 生成修复 patch
6. 验证并更新 wiki

## 9. 系统分层设计

### Layer 0：Raw Sources

不可变事实层。

包括：
- 项目源码
- Markdown / TXT / 文献资料
- 历史设计文档
- 导出的聊天记录 / 会议纪要

### Layer 1：Structural Ingest

负责结构摄入与骨架建立。

包括：
- AST / tree-sitter 扫描
- 文档标题结构解析
- 目录和 symbol 建模
- 生成 `index.md` 与基础 `entities/*.md`

### Layer 2：Semantic Digest

负责局部语义消化。

包括：
- 按文件、symbol、span 做切片精读
- 提炼角色、流程、边界条件、依赖、风险与修改入口
- 页面状态从 `raw_ast` 逐步升级为 `digested`

### Layer 3：Task Priming / Task Pack

负责压缩“本次任务最小知识包”。

Task Pack 仅包含：
- task summary
- target file
- primary symbols
- related symbols
- hotspots
- constraints
- verify checklist

### Layer 4：Safe Edit / Verify

负责定点修改与验证。

包括：
- ASTRead / Symbol Read
- strict patch apply
- Search/Replace Patch
- ask_user fallback
- lint / test / bash verify

### Layer 5：Compounding LLM Wiki

负责知识复利与长期运维。

包括：
- ingest
- query
- query-archive
- lint
- reconcile
- index / log / schema 维护
- Obsidian / Git 支持

## 10. 页面与状态设计

### 10.1 页面状态

- `raw_ast`：只有结构，没有可靠语义
- `partially_digested`：已有部分语义，可辅助理解
- `digested`：可直接用于任务参考
- `stale`：源码已变化，摘要可能过期
- `historical`：历史设计资料
- `superseded`：已被替代

### 10.2 规则要求

- `raw_ast` 页面不能直接作为修改依据
- `stale` 页面不能直接信任，必须 reconcile / diff digest
- `digested` 页面才允许进入 Task Pack

## 11. MVP 范围（第一轮必须打通）

第一轮只做最小可用闭环，不追求全功能完成。

### 11.1 MVP 八项

1. `--mode wiki_strict`
2. `index.md + log.md + raw_ast entities`
3. watcher stale 标记
4. `/digest`
5. `ASTReadTool`
6. strict patch apply
7. TaskPack + EditSpec
8. wiki_strict 下的 `/plan`

### 11.2 MVP 达成后的能力

只要以上 8 项打通，就已经形成：

- 任务级消化
- 精准定位
- 局部修改
- OOM 控制
- 与 `standard` 模式兼容

## 12. 关键模块范围

当前版本重点影响以下模块：

- `src/core/main.py`
- `src/core/config.py`
- `src/core/knowledge/ingester.py`
- `src/core/knowledge/watcher.py`
- `src/core/tools/ast_read.py`
- `src/core/tools/file_edit.py`
- `src/core/flow_state.py`
- `src/core/coordinator.py`
- `plan_manager` / `src/core/plan.py`
- `src/core/wiki/*`

## 13. 风险与约束

### 13.1 核心风险

1. 试图一次性做完整知识库，导致系统复杂度失控。
2. Watchdog 越权，自动覆盖已有 digested 页面。
3. `/plan` 仍输出整文件代码，违背局部修改原则。
4. Wiki 页面快速膨胀，缺乏 lint / reconcile 约束。
5. 自动写入不可控，难以回滚。
6. 即使有 Wiki，32K 模型仍因读取过多内容而 OOM。

### 13.2 对应约束

- 先 digest 核心文件，其余按需 digest。
- Watchdog 只做 `stale + queue`，不直接做深总结。
- `wiki_strict` 下 `/plan` 只输出结构化计划。
- 限制 Task Pack 大小和 symbol 数量。
- 严格分离 plan / localization / patch / verify。
- 高风险 patch 必须支持 ask_user fallback。

## 14. 版本推进策略

### Phase 0：规则定稿

输出 schema 层规则，统一 frontmatter、模板、digest policy、conflict policy、taskpack policy、watchdog policy。

### Phase 1：模式接入与结构测绘

让 `wiki_strict` 能启动，并可为 demo 项目生成结构骨架。

### Phase 2：语义消化层

实现 `/scan`、`/digest`、`/digest --changed`，把核心文件从 `raw_ast` 升级为 `digested`。

### Phase 3：任务级消化与 `/plan` 重构

引入 TaskPack 与 EditSpec，让系统“先局部熟悉，再精确修改”。

### Phase 4：精准修改与 debug 闭环

支持 ASTRead、strict patch、traceback 清洗、局部 debug、verify / retry。

### Phase 5：Compounding LLM Wiki

支持 `/ingest`、`/query-archive`、`/lint-wiki`、`/reconcile`，建立知识复利闭环。

### Phase 6：Obsidian / Git 运维层

支持长期审计、回滚、可视化浏览与健康检查。

## 15. 验收口径

项目阶段验收使用如下口径：

### M1：模式与骨架可用
- `wiki_strict` 启动成功
- 结构测绘成功
- watcher stale 标记正常

### M2：核心模块可 digest
- 至少 5 个核心文件完成 digest
- 页面可以指导后续 review / modify

### M3：任务级修改可跑通
- `/plan → TaskPack → EditSpec → patch` 成功
- 单函数修改不依赖全文阅读

### M4：局部 debug 可跑通
- traceback 清洗正常
- 局部修复与验证闭环成立

### M5：知识复利闭环成立
- query-archive / lint / reconcile 可用
- index / log 自动维护

## 16. 本文档在 memory-bank 中的作用

该文档的职责不是记录全部技术细节，而是作为整个项目的“产品意图 + 结构边界 + MVP 目标”的统一入口。

后续配套文件的分工如下：

- `game-design-document.md`：说明项目做什么、为什么做、边界是什么
- `tech-stack.md`：说明采用什么技术实现最简单且稳健
- `implementation-plan.md`：把开发拆成小步、可验证、无代码的指令
- `architecture.md`：记录真实落地后的文件职责和架构演进
- `progress.md`：记录每一步做了什么、做到哪里

## 17. 当前版本结论

本项目的本质，不是“给 cc-mini 再加一批功能”，而是把它升级为两套并存能力：

- `standard`：原有强模型 / 通用模式
- `wiki_strict`：面向本地 32K 小模型的受控工作模式

只要后续开发始终围绕以下主线展开，就不会偏离目标：

**结构扫描 → 语义消化 → 任务预热 → 精准定位 → 局部 patch → 局部 debug → 持久化 Wiki 运维**
