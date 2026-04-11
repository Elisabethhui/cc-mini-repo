# TaskPack Policy

## 文档目的
本文件定义什么是 TaskPack、TaskPack 必须包含什么、它如何限制任务范围，以及什么情况下不允许跳过 TaskPack 直接进入 patch。

## TaskPack 管什么
1. 把“当前任务相关的最小知识”压缩成一个稳定工作包。
2. 为 review / modify / debug 提供统一输入。
3. 控制 32K 小模型的上下文规模，减少现场拼知识。
4. 作为 `/prime` 与 `wiki_strict /plan` 的正式输出对象。

## TaskPack 不管什么
1. 不直接生成代码实现。
2. 不替代 EditSpec。
3. 不替代验证结果。
4. 不等于全局项目摘要。
5. 不在本步确定最终 Python 类型、模块路径或序列化实现。

## TaskPack 的制度定义（新增）
### 本步已拍板
1. TaskPack 是**正式概念**，不是一次性聊天草稿。
2. TaskPack 应支持**持久化**，不能只存在于瞬时上下文里。
3. TaskPack 应与 Wiki 体系保持一致，优先采用**Markdown 页面 + YAML frontmatter / structured sections** 的思路落盘。
4. `/prime` 生成 TaskPack；`/plan` 在 `wiki_strict` 下应消费或生成与 TaskPack 一致的结构化信息。

### 本步明确不拍板
以下问题不在本步锁死，留到后续实现步骤决定：
- Python 里用 `dataclass`、`pydantic` 还是普通 `dict`
- TaskPack 与 EditSpec 是一个物理文件还是两个物理文件
- `taskpacks/` 目录最终按 task_id、file、symbol 还是日期组织
- 完整的 YAML 字段校验器与序列化器实现

## 何时必须生成 TaskPack
1. 进入修改任务前。
2. 进入局部 debug 前。
3. 任务涉及多个相关 symbol，但仍希望控制阅读范围时。
4. `/plan` 需要输出结构化修改意图时。

## TaskPack 最小内容（初版）
至少应包含：
- task summary
- target file
- primary symbols
- related symbols
- 当前可用 digest 页面
- 热点/风险点
- 约束条件
- 验证建议

> 说明：这是最小字段集合。后续允许扩展，但不能删除这些核心字段而导致任务边界失控。

## 范围控制规则
1. TaskPack 只应服务“当前这一步任务”。
2. 单个 TaskPack 应尽量限制在少量主 symbol 和少量辅助依赖内。
3. 涉及过多文件、过多核心 symbol 时，必须拆分为多个任务。

## 进入 patch 的门槛
满足以下条件才允许继续：
1. 已有明确 target file。
2. 已定位到 primary symbol 或可控 span / anchor。
3. 已明确约束条件。
4. 已给出验证建议。
5. 不再依赖整文件全文阅读。

## 不允许直接 patch 的情况
1. 页面仍是 `raw_ast` 且无任务级 digest。
2. 关键 symbol 尚未定位。
3. 任务目标描述含糊，无法约束修改边界。
4. 风险点和验证方式尚未明确。

## 与 EditSpec 的关系
- TaskPack 负责“准备工作包”。
- EditSpec 负责“结构化修改意图与边界”。
- EditSpec 的 target 不应只停留在 file 级，应能进一步收缩到 symbol / span / anchor。
- 二者都齐备后，才应进入局部 patch 阶段。
