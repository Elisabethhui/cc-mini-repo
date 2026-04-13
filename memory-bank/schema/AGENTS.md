## AGENTS

## 文档目的
本文件定义 **AI 开发执行者** 在本项目中的统一工作纪律。它约束“开始前必须读什么、每一步怎么做、什么事情绝对不能做”，用于减少多轮开发和多执行者切换时的行为漂移。

## 适用范围
- 适用于所有参与本项目实现、审阅、调试、文档维护的 AI 执行者。
- 适用于 `standard` 与 `wiki_strict` 两种模式相关开发，但对 `wiki_strict` 的约束更严格。

## 不适用范围
- 不定义具体代码实现方案。
- 不替代 `implementation-plan.md` 的分步任务说明。
- 不替代 `conventions.md`、`digest_policy.md`、`taskpack_policy.md` 等专题规则文件。

## Always 规则（始终应用）
1. 写任何代码前，必须完整阅读：
   - `memory-bank/game-design-document.md`
   - `memory-bank/tech-stack.md`
   - `memory-bank/implementation-plan.md`
   - `memory-bank/progress.md`
   - `memory-bank/architecture.md`
2. 当步骤涉及规则解释、页面状态、TaskPack、digest、watchdog 等主题时，必须额外阅读对应 `memory-bank/schema/*.md` 文件。
3. 每次只允许执行当前实施步骤；在验证通过前，不得提前开始下一步。
4. 每完成一个重大步骤后，必须更新：
   - `memory-bank/progress.md`
   - `memory-bank/architecture.md`
5. 修改代码时，优先局部 patch；禁止默认整文件重写。
6. 所有新增逻辑必须保持模块化、多文件、单一职责，禁止 monolith。
7. `wiki_strict` 的新增逻辑必须与 `standard` 显式隔离。
8. 信息不足时，先补 digest 或补定位；禁止靠猜测直接改代码。

## 步骤边界规则（新增）
1. 每个实施步骤开始前，必须先区分两类问题：
   - **本步必须拍板的规则级问题**
   - **后续步骤再决定的实现级问题**
2. 规则级问题只回答：
   - 这个概念是否存在
   - 它解决什么问题
   - 它约束什么、不约束什么
   - 它与其他概念的关系是什么
3. 实现级问题通常延后处理，例如：
   - Python 类型使用 `dataclass` 还是 `pydantic`
   - 持久化对象最终放一个文件还是两个文件
   - 目录按 task_id 还是按 symbol 组织
   - 命令具体返回值、模块路径、类名与函数名
4. 不允许把后续实现细节提前塞回当前步骤，除非当前步骤的验证明确依赖该决策。
5. 当出现大量澄清问题时，必须先做“问题分层”，再回答具体选项。

## 工作节奏规则
1. 先规则，后骨架；先骨架，后语义；先语义，后修改。
2. 所有任务都应拆为：
   - 计划
   - 定位
   - 修改/分析
   - 验证
3. 当任务范围超过安全边界时，必须拆分任务，而不是扩大上下文硬做。

## 输出质量规则
1. 任何设计决策都应说明“管什么，不管什么”。
2. 任何新文件都应说明职责、边界、与现有文件的关系。
3. 任何状态都应说明进入条件、退出条件和限制。
4. 任何可执行修改都应有明确验证方式。
5. 每一步交付时都应明确：
   - 本步目标
   - 本步核心边界
   - 本步明确不处理什么
   - 本步影响哪些文件
   - 本步完成后的验证标准

## 风险控制规则
1. 不允许把 Wiki 当成一次性缓存；Wiki 是长期中间层。
2. 不允许在 `raw_ast` 或 `stale` 信息不充分时直接进入 patch。
3. 不允许 Watchdog 越权进行高成本自动总结。
4. 不允许静默覆盖已有高置信度摘要或页面。

## 交接规则
每次完成当前步骤后，必须在 `progress.md` 记录：
- 做了什么
- 如何验证
- 遗留问题
- 下一步建议

并在 `architecture.md` 记录：
- 新增/修改了哪些文件
- 文件职责
- 为什么需要这些文件

## 执行规则
1. 一次只执行 `memory-bank/current-task.md` 中定义的一个链式任务。
2. 链式任务内部允许包含多个顺序子任务。
3. 每个子任务未通过测试，不得进入下一个子任务。
4. 任一子任务失败，最多修复 2 轮。
5. 2 轮后仍失败，停止并输出阻塞报告。
6. 全部子任务通过后，才允许更新 `progress.md` 和 `architecture.md`。
7. 成功后停止，不允许自动进入下一个 phase 或下一个任务。

## Python 运行时规则（新增）
本项目禁止依赖“外层 shell 已激活虚拟环境”的隐式状态。Claude Code 执行 Bash 命令时，必须使用**显式解释器路径**和**显式导入路径**。

### 固定解释器
统一使用以下 Python 解释器：

`/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python`

### 固定工作目录
统一在以下目录执行项目命令：

`/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo`

### 导入规则
凡是需要导入 `src/core/...` 下模块的命令，必须显式添加：

`PYTHONPATH=src`

### 禁止
- 不要使用裸 `python`
- 不要使用裸 `python3`
- 不要假设 `source .venv/bin/activate` 的状态会自动继承到后续 Bash 子进程
- 不要在运行时未验证通过前，继续执行 current-task

### 允许的命令形式
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.config import RunMode; print('runtime ok')"
```

### 任务前必须验证
开始任何 `memory-bank/current-task.md` 前，必须先验证：

```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python --version
```

```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.config import RunMode; print('runtime ok')"
```

若上述验证失败，必须立即停止，并输出：
1. 失败命令
2. 错误摘要
3. 当前缺失条件
4. 需要人工处理的事项

## 当前项目状态约束（建议保留）
1. 当前项目已回退到 Step 3 之后的 v2.0 路线。
2. 旧 Step 4 不再作为后续执行依据。
3. 当前 Phase 0 已完成，后续从 Phase 1 开始。
4. 当前采用“**保护现状 + 增量补缺**”策略，不允许按“从零重建”的假设乱改现有代码。
5. 已完成基线检查后，后续任务应优先补“最小缺口”，而不是重复做全局扫描。
