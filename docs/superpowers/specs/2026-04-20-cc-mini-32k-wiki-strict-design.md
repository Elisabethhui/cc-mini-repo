# cc-mini 32K 上下文增强与 wiki_strict 第一阶段设计

> 状态：待审阅草稿  
> 目标：把第一阶段收缩为“最小产品启动阶段”，先交付一个能跑、能 init、能 scan、能 plan、能输出结构化结果的第一版产品。

## 1. 文档定位

本文档定义 cc-mini 在 32K 本地模型场景下的第一阶段产品方向。

这次修订后的核心原则是：

- 第一阶段优先做出一个能跑、能 init、能开始用的最小产品；
- 不在第一阶段一次性完成完整的 wiki_strict 终态架构；
- 保留 standard 模式的稳定性与兼容性；
- 为后续 patch、post_edit、maintenance、长任务连续性预留清晰扩展点。

换句话说：

**Phase 1 不是完成整个 32K 架构升级，而是交付一个可以真正启动、初始化、并进入最小 wiki_strict 分析链的产品第一版。**

## 2. 事实依据

本设计基于以下内容：

1. 当前 cc-mini 代码库本身；
2. `.planning/codebase/` 下的代码库分析文档；
3. 已有的 memory-bank 与 schema 草稿；
4. 当前关于 `standard` 与 `wiki_strict` 的设计讨论结果。

说明：

- `.planning/PROJECT.md`、`REQUIREMENTS.md`、`ROADMAP.md`、`phases/` 等内容，如果尚未被人工批准，只能视为参考草稿；
- 最终设计应以现有代码能力 + 已批准方向为准，而不是机械继承自动规划结果。

## 3. 问题定义

当前 cc-mini 虽然已经出现了一些与 wiki 相关的能力雏形，例如：

- 多种运行模式骨架；
- 一些 wiki 生命周期相关命令；
- 一些结构化任务对象；
- token 预算和计划模式的初步支持；

但当前仍存在几个关键问题：

### 3.1 产品入口不清晰

目前更像“正在演进的内部系统”，而不是一个可以清楚启动和初始化的产品。
用户并不清楚：

- 应该怎么启动；
- 应该怎么初始化；
- 第一次成功使用的路径是什么。

### 3.2 `standard` 与 `wiki_strict` 边界不够清楚

如果边界不清楚，就容易出现：

- `standard` 被 wiki 逻辑污染；
- `wiki_strict` 只是 `standard` 的特殊分支；
- 模式间权限、工具、状态混杂。

### 3.3 32K 场景下的真实风险没有被最小闭环解决

在本地 32K 模型场景下，真正的问题不是“单轮上下文不够长”这么简单，而是：

- 任务主线容易丢失；
- 模型容易在多轮里偏离目标；
- 计划和编辑容易混在一起；
- 大任务容易直接退化成全文阅读和失控修改。

### 3.4 第一阶段 scope 容易过大

如果第一阶段同时追求：

- 完整生命周期；
- 完整 patch 链；
- 自动 maintenance；
- 长任务连续性全覆盖；
- 复杂状态机；

那么项目会很快变成“什么都设计了，但还没有一个能启动、能初始化、能让用户开始使用的第一版产品”。

## 4. 第一阶段的核心目标

第一阶段只追求下面四个目标：

### 目标 1：先能跑

项目必须具备清晰的最小运行入口，例如：

- `cc-mini --help`
- `cc-mini doctor`
- `cc-mini run --mode standard`
- `cc-mini run --mode wiki_strict`

### 目标 2：先能初始化

必须有一个明确的初始化入口，例如：

- `cc-mini init`

初始化后，用户应得到一个可工作的最小工作区，而不是一堆零散文档和隐式假设。

### 目标 3：先让 wiki_strict 具备最小可见价值

`wiki_strict` 第一阶段不要求一开始就“全能改代码”，但必须让用户第一次进入时能看到与 `standard` 不同的价值。

这个最小价值建议是：

- 能初始化 workspace；
- 能做最小 scan；
- 能输出结构化任务产物：
  - Goal Stack
  - TaskPack
  - EditSpec

### 目标 4：保住扩展路线

虽然第一阶段不做完所有能力，但架构上必须为后续这些能力留出明确位置：

- ASTRead / strict patch / verify
- reconcile / lint / archive / query-archive
- 长任务连续性
- 自动 maintenance
- 预算状态机与 32K 上下文增强

## 5. 第一阶段非目标

第一阶段明确不追求以下内容全部落地：

- 从零重构整个仓库；
- 一次性做成完整的双 runtime 终态架构；
- 一次性做出完整的 patch / verify / maintenance 闭环；
- 一次性解决所有 token 优化与长任务恢复问题；
- 建立一个适用于所有未来产品的通用工作流引擎。

这意味着：

**Phase 1 的重点是最小产品启动链，不是完整终态闭环。**

## 6. 第一阶段建议形态

第一阶段应被定义为：

**一个“可启动 + 可初始化 + 可进入最小 wiki_strict 分析链”的产品化基础版本。**

换句话说，第一阶段建议切成三段：

### 6.1 产品壳（Bootstrap Layer）

提供统一 CLI 和基础配置入口：

- 启动入口
- 配置加载
- 环境检查
- mode 识别

### 6.2 初始化层（Init Layer）

提供 `cc-mini init`，生成：

- workspace 目录
- memory-bank 基础文件
- schema 基础规则
- index / log / progress / architecture 等初始文档

### 6.3 最小分析层（Minimal wiki_strict Readiness Layer）

让 `wiki_strict` 能完成最小只读链路：

- 进入模式
- 扫描/识别目标
- 输出 Goal Stack
- 输出 TaskPack
- 输出 EditSpec

这三个层面一旦完成，就说明这个项目已经不是纯设计，而是进入了“可用产品第一版”。

## 7. 模式设计原则

### 7.1 `standard` 保持稳定

`standard` 仍然是默认交互模式。

第一阶段的要求是：

- 它不被 `wiki_strict` 约束污染；
- 它依然可以在 wiki 功能缺失时独立使用；
- 老用户不会因为引入 `wiki_strict` 而被迫改变原有使用方式。

### 7.2 `wiki_strict` 是独立模式，但第一阶段先做逻辑隔离

从方向上看，`standard` 和 `wiki_strict` 应该强隔离，这一点是成立的。  
但在第一阶段，不一定必须马上做到：

- 两套完全独立的 engine instance；
- 两套完全独立的底层运行框架；

第一阶段更现实的要求是：

- 先做逻辑隔离；
- 让 mode 之间在：
  - prompt policy
  - tool registry
  - permission policy
  - state gating
  - workspace assumptions
  上明显分开；
- 底层真正通用的基础设施可以暂时共享。

也就是说：

**Phase 1 先保证行为隔离，不强求立刻完成物理隔离。**

后续的 runtime-isolation 阶段会继续沿着这条线推进：先让 `wiki_strict` 的运行时分支更清晰，再逐步收紧共享边界，但仍然不把 `standard` 变成 wiki 流程的附属入口。

## 8. 第一阶段最小用户路径

这是本修订版最关键的内容。

第一阶段必须明确一个真实可跑的最小 Happy Path。

### Step 1：用户初始化项目

```bash
cc-mini init
```

预期结果：

- 工作区被创建；
- memory-bank 基础文件生成；
- schema 规则文件生成；
- 用户看到下一步提示。

### Step 2：用户检查环境

```bash
cc-mini doctor
```

预期结果：

- 当前项目路径可识别；
- 配置可加载；
- 工作区可写；
- 当前模式能力正常。

### Step 3：用户以 standard 模式运行

```bash
cc-mini run --mode standard
```

预期结果：

- 标准模式正常工作；
- 没有被强制拉入 wiki 生命周期。

### Step 4：用户进入 wiki_strict

```bash
cc-mini run --mode wiki_strict
```

预期结果：

- 进入受控分析模式；
- workspace 可识别；
- 能启动最小 wiki 生命周期。

### Step 5：用户执行最小分析任务

例如：

- scan 一个目标文件；
- 针对一个函数生成结构化分析结果。

预期产出：

- Goal Stack
- TaskPack
- EditSpec

这一步完成后，第一阶段的产品已经开始“像一个产品”。

## 9. 第一阶段的最小能力边界

第一阶段最低可接受边界建议收缩为：

1. workspace 初始化
2. mode 启动
3. 最小 scan
4. 最小 task priming
5. 最小结构化 planning 输出

也就是说，Phase 1 最少要做到：

- `init`
- `doctor`
- `run --mode standard`
- `run --mode wiki_strict`
- `scan`
- `Goal Stack / TaskPack / EditSpec`

### 暂时不列为第一阶段硬门槛的能力

这些能力很重要，但建议延后为 Phase 1.5 或 Phase 2：

- ASTRead 真正接线
- strict patch
- post-edit verify
- reconcile / lint / archive / query-archive
- 自动 maintenance
- 完整长任务连续性恢复

这不是说它们不做，而是说：

**不把它们作为第一阶段产品启动的硬门槛。**

## 10. 生命周期切分建议

完整终态生命周期可以很丰富，但第一阶段建议只固化最小版本：

### 10.1 Phase 1：分析链

职责：

- 初始化 workspace
- 识别 mode
- 执行 scan
- 生成最小 TaskPack
- 输出结构化 planning 结果

### 10.2 Phase 1.5：最小 patch 链

职责：

- 在受控状态下允许最小 patch
- 加入最小 post_edit 结果
- 打通最小的“分析 -> 修改”路径

### 10.3 Phase 2：维护链与连续性增强

职责：

- 自动 maintenance
- reconcile / archive / lint
- 长任务连续性恢复
- 更完整的状态机

这样的切分可以避免第一阶段被过多终态能力拖重。

## 11. 状态模型建议（Phase 1 最小版）

第一阶段不要一口气把状态机做得太复杂。  
建议只固化最小状态集。

### 11.1 Workspace 状态

建议第一阶段只保留：

- `uninitialized`
- `initialized`
- `stale`

解释：

- `uninitialized`：尚未执行 init 或 init_build
- `initialized`：工作区可用，具备最小运行条件
- `stale`：已有 workspace 需要重新 scan 或 digest

### 11.2 Task 状态

建议第一阶段只保留：

- `pending`
- `primed`
- `planned`
- `blocked`
- `completed`

解释：

- `pending`：任务刚进入
- `primed`：已形成最小 TaskPack
- `planned`：已形成结构化计划
- `blocked`：因为缺少信息或校验失败被阻塞
- `completed`：本轮分析或规划任务完成

### 11.3 为什么要收缩状态

因为第一阶段最重要的是：

- 状态可读
- 状态可用
- 状态可验证

而不是一开始就做一个过大的状态机。

## 12. 长任务连续性在第一阶段的要求

长任务连续性仍然重要，但第一阶段不需要一次性做成完整恢复系统。

第一阶段只要求保住最小主线对象：

- 全局目标
- 当前步骤目标
- 当前任务目标
- 当前边界（不做什么）
- 当前阻塞点
- 最近一次有效结论

也就是说，第一阶段只需要一个**最小 task spine**。

判断标准很简单：

- 经过一次压缩或重新规划后，系统还能说清楚“现在在干什么”
- 不会因为多轮分析就忘了为什么要做这一步

完整的 continuity 恢复系统可以后移。

## 13. 工具与权限策略（Phase 1 版本）

### 13.1 `standard`

暴露当前通用 CLI 所需的工具集。

### 13.2 `wiki_strict`

第一阶段只开放与最小分析链兼容的工具：

- workspace 识别
- 扫描
- 结构化任务产物生成
- 只读分析辅助工具

### 13.3 第一阶段不要开放的内容

以下能力可保留设计位，但不一定第一阶段默认开放：

- 任意写工具
- 自动 patch 工具
- 高风险 Bash 写操作
- 自动 maintenance 修改操作

这样可以保证：

**第一阶段先是一个受控的分析型产品，再逐步演进成分析 + 修改型产品。**

## 14. 测试策略（Phase 1 版本）

第一阶段测试必须围绕“最小产品路径”展开，而不是一开始就全测终态复杂工作流。

### 必做测试类别

#### 1. 启动测试

验证：

- CLI 可启动
- mode 参数可识别
- doctor 可执行

#### 2. 初始化测试

验证：

- `cc-mini init` 可创建 workspace
- 必要文件和目录生成成功
- 再次 init 时行为可解释（幂等或提示）

#### 3. 模式隔离测试

验证：

- `standard` 不会被强制拉入 wiki 流程
- `wiki_strict` 有独立的行为边界
- 两种模式可用工具和系统约束不同

#### 4. 最小分析链测试

验证：

- `wiki_strict` 能 scan
- 能生成 Goal Stack
- 能生成 TaskPack
- 能生成 EditSpec

#### 5. 回归测试

验证：

- 长任务中间状态不会轻易丢失
- 规划后还能回到主线
- 计划状态不会误用写操作
- 关键文档会随着设计同步更新

## 15. 文档同步规则

文档不是附带产物，而是设计的一部分。

第一阶段落地后，需要同步更新：

- `README.md`
- 命令帮助文本
- `docs/` 下的使用文档
- 与 wiki_strict 相关的模式说明

要求是：

**文档必须描述实际支持的第一阶段产品，而不是尚未完成的终态。**

## 16. 第一阶段验收标准

Phase 1 完成时，至少满足：

- 项目能启动；
- 能执行 `init`；
- 能执行 `doctor`；
- 能进入 `standard`；
- 能进入 `wiki_strict`；
- 能完成最小 `scan`；
- 能输出结构化结果（Goal Stack / TaskPack / EditSpec）；
- `standard` 与 `wiki_strict` 有清晰的逻辑隔离；
- README 和相关文档已更新；
- 测试覆盖最小产品路径与已知风险点。

## 17. 后续阶段建议

为了避免 Phase 1 过重，后续阶段建议这样展开：

- **Phase 1**：分析链
- **Phase 1.5**：最小 patch 链
- **Phase 2**：维护链与连续性增强

这个切分的好处是：

- 第一阶段目标明确，容易验收；
- patch / post_edit / maintenance 不会压垮首版；
- 后续扩展有清晰入口，不会把第一阶段做成“大而全”。

## 18. 结论

这版修订后的方向是：

- 先做最小产品启动阶段；
- 先让用户能跑、能 init、能 scan、能 plan、能看到结构化结果；
- 先做逻辑隔离，不把第一阶段做成重物理隔离；
- 把 patch / post_edit / maintenance 下放到后续阶段；
- 用最小用户路径定义 Phase 1 的成功，而不是用终态架构定义它。

这才是更收敛、更清晰、也更符合当前项目阶段的设计。
