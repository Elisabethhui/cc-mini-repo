# Tech Stack Recommendation

> 说明：本项目不是传统游戏，但为了兼容当前工作流，仍沿用 `tech-stack.md` 文件名。本文档实际用于定义 **CC-MINI Wiki-Strict 模式升级项目** 的推荐技术栈与工程约束。

## 1. 技术栈目标

本项目的技术栈选择遵循一个原则：

**最简单但最健壮。**

这里的“简单”不是功能最少，而是：
- 尽量复用 cc-mini 现有技术栈与工程结构
- 尽量减少新增运行时依赖
- 尽量避免引入新的重型基础设施
- 尽量让本地 32K 小模型场景下的实现链路清晰可控

这里的“健壮”是指：
- 能稳定支持 `standard` 与 `wiki_strict` 双模式并存
- 能稳定支撑结构扫描、语义消化、TaskPack、局部 patch 与局部 debug
- 能保证写入行为可验证、可回滚、可审计
- 能在大代码库和碎片化知识源下控制 token 与上下文成本

---

## 2. 总体建议

推荐采用：

**Python + Markdown Wiki + Git + tree-sitter / AST + 现有 cc-mini CLI 工具体系**

也就是：
- 继续以 **Python** 作为主实现语言
- 继续复用 **cc-mini 当前 CLI / 核心调度结构**
- 用 **Markdown 文件系统** 作为 Wiki 中间层存储
- 用 **Git** 作为可回滚、可审计、可对比的底层变更机制
- 用 **AST / tree-sitter** 做结构测绘与局部读取定位
- 用 **模式开关（`standard` / `wiki_strict`）** 做架构隔离

这是当前阶段最合理的方案，因为它：
- 最贴近现有工程
- 最少引入额外部署成本
- 最适合本地模型、小上下文窗口和渐进式升级

---

## 3. 推荐主技术栈

### 3.1 主语言

**Python 3.11+（优先）**

推荐原因：
- cc-mini 当前体系天然更适合沿用 Python 生态
- 适合快速搭建 CLI、流程控制、状态机和文件系统逻辑
- 便于接入 AST、tree-sitter、日志清洗、文件监听和 Markdown 运维
- 便于与后续本地模型调用链、工具层和 patch 系统集成

约束建议：
- 新模块继续放在 `src/core/` 或其子目录中
- 不要把 wiki_strict 的逻辑散落到全项目
- 通过明确模块边界组织功能，而不是堆在单个大文件中

---

### 3.2 数据与中间层存储

**Markdown + Frontmatter + 本地目录结构**

推荐作为：
- Wiki 存储层
- 任务沉淀层
- schema 规则层
- archive / log / reports 层

推荐原因：
- 最轻量，不需要额外数据库
- 与 LLM 最兼容，可直接读写
- 适合版本控制、diff、回滚和人工审阅
- 与 Obsidian、Git、grep、脚本工具天然兼容

为什么不建议第一轮上数据库：
- 当前项目最核心的问题不是高并发查询，而是“小模型如何稳定理解和修改大项目”
- 现阶段需要的是可解释、可审阅、可回滚，不是重型存储系统
- 数据库会增加 schema 迁移、索引维护、同步与调试复杂度

结论：
- **第一轮不引入数据库**
- 先用 Markdown Wiki 跑通全流程
- 后续如有必要，再为索引、检索或统计单独加轻量存储层

---

### 3.3 版本控制与可审计层

**Git（必选）**

职责：
- 跟踪 wiki 页面变更
- 跟踪 patch 与代码修改
- 辅助 watcher / reconcile / diff digest
- 支撑回滚与审计

推荐原因：
- 你当前这个项目对“可回滚”和“修改边界控制”要求非常高
- Git 是最自然、最成熟、最简单的基础设施
- 可直接支持 `/digest --changed`、变更定位、前后 diff 分析

建议：
- 每个阶段性功能完成后提交一次
- wiki 更新和代码更新尽量同批次提交，保持上下文一致性
- 提交信息中体现：模式、目标模块、任务类型

---

### 3.4 结构测绘与代码定位

**tree-sitter + Python AST/语言级解析能力（混合方案）**

推荐策略：
- 对需要跨语言、统一目录扫描、统一 symbol 抽取的部分，用 **tree-sitter**
- 对 Python 自身代码的高可信读取与定位，可辅以 **Python AST**

推荐原因：
- tree-sitter 适合做结构骨架层（Layer 1）
- AST 适合做精确的 symbol/span/anchor 定位
- 二者混合能兼顾可扩展性与实现成本

设计定位：
- **Layer 1 用于搭骨架**
- **Layer 4 用于精确读取与修改定位**
- 不能把 tree-sitter 当成“最终语义理解层”

结论：
- 推荐保留 ASTReadTool 作为核心能力
- 结构层尽量统一，语义层再通过 digest 升级

---

### 3.5 文件监听与状态变更

**Python 文件监听库（优先 watchdog）**

用途：
- 监听代码与 Wiki 页面变化
- 标记受影响页面为 `stale`
- 写入 `digest_queue.md` / `reconcile_queue.md`

推荐原因：
- Python 生态成熟
- 易于接入当前 CLI 生命周期
- 足够满足当前“标 stale + 入队列”的职责

明确边界：
- watcher 只负责检测与标记
- watcher 不负责自动大规模 digest
- watcher 不负责静默重写已有 digested 页面

---

### 3.6 CLI 与交互层

**沿用 cc-mini 现有 CLI 体系**

新增命令建议：
- `/scan`
- `/digest`
- `/digest --changed`
- `/prime`
- `/lint-wiki`
- `/reconcile`
- `/query-archive`

推荐原因：
- 用户当前使用习惯不需要重建
- 直接在现有命令体系中引入 wiki_strict，迁移成本最低
- 最适合逐步接入状态机式流程

设计要求：
- `standard` 和 `wiki_strict` 必须明确分支
- `wiki_strict` 下 `/plan` 输出 TaskPack + EditSpec + Patch Plan
- 禁止 wiki_strict 下退化为整文件代码生成

---

### 3.7 测试与验证层

**pytest + 轻量 CLI 集成测试 + Golden File 测试**

推荐组合：
- 单元测试：校验 status、frontmatter、TaskPack、EditSpec、queue 写入
- 集成测试：校验 `/scan`、`/digest`、`/plan`、watcher、patch apply 的最小闭环
- Golden File 测试：校验生成的 `index.md`、`entity.md`、TaskPack 与 reconcile 输出格式稳定

推荐原因：
- 这个项目的风险主要不是算法误差，而是“流程失控”“状态污染”“写入错误”“模式串线”
- 因此必须重点测试：
  - 模式隔离
  - 状态转换
  - 读取边界
  - patch 边界
  - 输出格式稳定性

建议：
- 每一步实施计划都附带最小验证测试
- 先做小范围 demo 项目验证，再扩展到真实仓库

---

## 4. 推荐目录与模块组织

建议在现有项目内增量组织为：

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

目录设计原则：
- `knowledge/` 更偏输入、监听、原始结构处理
- `wiki/` 更偏规则、状态、沉淀与长期运维
- `tools/` 保持通用工具边界
- `coordinator.py` 只做流程分发，不塞实现细节
- `plan.py` 负责结构化计划，不直接承担 patch 执行

禁止事项：
- 禁止把 wiki_strict 逻辑全部堆进 `main.py`
- 禁止新增一个超大“万能 manager”文件
- 禁止让 watcher、digest、patch、archive 混在同一实现里

---

## 5. 推荐状态与数据表达方式

### 5.1 页面状态

继续使用 Markdown frontmatter 表达页面状态：
- `raw_ast`
- `partially_digested`
- `digested`
- `stale`
- `historical`
- `superseded`

理由：
- 可读性高
- 易于 lint / reconcile / grep
- 易于 Git diff 与人工检查

### 5.2 任务级结构体

推荐用明确的结构化对象表达：
- `TaskPack`
- `EditSpec`
- `LocalizationResult`
- `VerifyChecklist`

实现建议：
- Python `dataclass` 或 `pydantic` 模型都可以

当前阶段推荐：
- **优先 dataclass**

原因：
- 更轻量
- 足够满足当前内部结构表达
- 避免过早引入过多运行时约束和额外复杂度

如果后续需要更强校验，再引入 pydantic

---

## 6. 推荐 LLM 工作方式

### 6.1 主原则

LLM 在 `wiki_strict` 下不直接面对“整个项目”，而是面对：
- digest 过的 Wiki 页面
- TaskPack
- 少量目标 symbol 的源码切片
- 最新清洗后的错误日志

### 6.2 原则约束

- 先结构，再语义
- 先 digest，再修改
- 先定位，再 patch
- 先 verify，再归档
- 失败后返回局部状态，而不是回到全项目级重新理解

### 6.3 推荐原因

这不是单纯为了省 token，而是为了：
- 保证推理纪律性
- 保证 patch 边界可控
- 避免多轮调试时上下文爆炸
- 避免小模型“临场即兴读项目”

---

## 7. 不推荐的技术路径

### 7.1 第一轮不推荐引入重型数据库

例如：
- PostgreSQL
- Neo4j
- Elasticsearch
- Milvus / 大型向量数据库

原因：
- 会显著增加项目复杂度
- 不能直接解决“小模型如何分阶段完成改码”这个核心问题
- 当前阶段最重要的是流程可控，而不是检索基础设施豪华

### 7.2 第一轮不推荐做前后端分离式可视化平台

原因：
- 当前核心问题不是 UI，而是内核工作流
- 先把 CLI、状态机和 Wiki 中间层打通，价值更高

### 7.3 第一轮不推荐整仓全量 embedding 方案当主方案

原因：
- embedding 检索只能解决“找到相关内容”的一部分问题
- 它不能替代 digest、TaskPack、Localization 与 strict patch 的受控过程

### 7.4 第一轮不推荐让 `/plan` 直接产出完整大段代码

原因：
- 会直接破坏 wiki_strict 的目标
- 容易重新引发 OOM、错误扩散和 patch 失控

---

## 8. 环境与工程建议

### 8.1 Python 环境

建议：
- 使用独立虚拟环境
- 明确 requirements / pyproject
- 保持 tree-sitter、watchdog、pytest 等依赖最小化

### 8.2 日志策略

建议：
- 区分运行日志、wiki 变更日志、任务日志、debug 清洗日志
- `log.md` 记录高价值事件
- 程序日志用于排查，不要把所有运行噪声写进 wiki

### 8.3 配置策略

建议：
- 在 `config.py` 中统一管理 `RunMode`
- 控制 TaskPack token 上限、symbol 读取数量上限、日志截断上限
- 把这些限制做成可配置项，而不是写死在流程里

---

## 9. 第一轮推荐依赖清单（MVP 级）

建议保守控制为以下几类：

- Python 3.11+
- pytest
- watchdog
- tree-sitter（或项目已采用的同类解析能力）
- 标准库：`pathlib`、`dataclasses`、`subprocess`、`ast`、`json`、`difflib`、`logging`

如当前项目已有成熟工具链，应优先复用，不为“技术完整性”强行重建。

---

## 10. 最终推荐结论

对于 **CC-MINI Wiki-Strict 模式升级项目**，当前阶段最合适的技术栈是：

**Python + Markdown Wiki + Git + tree-sitter / AST + pytest + watchdog + 现有 cc-mini CLI 框架**

这是当前最符合你目标的方案，因为它同时满足：

- **简单**：复用现有工程，减少新增基础设施
- **健壮**：支持双模式并存、状态机流程和局部 patch
- **可控**：适合 32K 小模型的 token、上下文和写入边界控制
- **可维护**：便于 Git 回滚、Wiki 审阅、规则收敛和后续 Obsidian 集成

如果后续规模进一步增大，再考虑增加：
- 专门的索引层
- 更细的语言级解析器
- 更强的结构化校验层
- 可视化运维界面

但第一轮不要先把系统做重。

---

## 11. 给后续 AI 开发者的强约束

后续所有实现都应默认遵守以下原则：

1. 不破坏 `standard` 模式。
2. 不允许 wiki_strict 退化为整文件重写。
3. 新功能必须按模块落地，禁止单体巨文件。
4. 修改前必须先确认 Wiki 状态、TaskPack 和定位结果。
5. 所有高风险写入必须可验证、可回滚。
6. Watchdog 只负责 stale 标记和入队，不越权做深度 digest。
7. 第一轮优先打通 MVP 八项，不扩写到完整运维平台。

