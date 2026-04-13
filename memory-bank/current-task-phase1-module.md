# Current Task

## Task ID
phase-1-module-runtime-and-placeholder

## Task Name
Phase 1 加速版模块：运行时固化 + Goal Stack 占位 + mode 传递校验

## Module Goal
在**不破坏当前部分可执行状态**的前提下，一次性完成 Phase 1 中最值得优先补齐的同类缺口，形成一个可验证、可停止、可记录的完整模块闭环。

本模块只处理以下三类能力：
1. Python 运行时规则固化
2. coordinator 中最小 Goal Stack 占位注入
3. wiki_strict mode 传递链和 token risk 显示的最小确认/补齐

## Current Baseline
已确认：
- 项目已经部分可执行
- CLI 入口：`src/core/main.py`
- `RunMode` / `get_run_mode()` 已存在
- `core.config`、`core.token_budget`、`core.flow_state`、`core.knowledge.ingester`、`core.knowledge.watcher`、`core.coordinator`、`core.checkpoint`、`core.dehydration` 已可导入
- `.cc-mini/wiki/index.md` 和 `entities/` 已存在
- 当前 Phase 0 已完成
- 当前应继续 Phase 1，而不是回到旧 Step 4

## Allowed Read
- `memory-bank/system-design-v2.md`
- `memory-bank/progress.md`
- `memory-bank/architecture.md`
- `memory-bank/findings.md`
- `memory-bank/decisions.md`
- `memory-bank/phases/phase-1-exec.md`
- `memory-bank/schema/AGENTS.md`
- `memory-bank/schema/goal_policy.md`
- `memory-bank/schema/context_safeguard_policy.md`
- `memory-bank/schema/phase_boundary_policy.md`
- `src/core/config.py`
- `src/core/main.py`
- `src/core/coordinator.py`
- `src/core/token_budget.py`
- `src/core/engine.py`

## Allowed Modify
- `memory-bank/schema/AGENTS.md`
- `memory-bank/progress.md`
- `memory-bank/architecture.md`
- `memory-bank/findings.md`
- `memory-bank/decisions.md`
- `src/core/coordinator.py`
- `src/core/main.py`
- `src/core/engine.py`
- `src/core/token_budget.py`

## Out of Scope
- 不实现 `/scan`、`/digest`、`/digest --changed`
- 不实现完整 dehydration / Runtime Snapshot 写入闭环
- 不实现 TaskPack / EditSpec / `/prime` / `/plan`
- 不实现 ASTRead / patch / debug / retry
- 不新增 Phase 2+ 文件
- 不做整仓重构
- 不恢复旧 Step 4 内容
- 不在本模块中引入新的持久化对象格式争议

## Runtime Rules (Must Follow)
1. 固定解释器：
   `/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python`
2. 固定工作目录：
   `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo`
3. 导入 `src/core/...` 时必须使用：
   `PYTHONPATH=src`
4. 禁止使用裸 `python` / `python3`

## Execution Strategy
本任务允许一次完成一个模块，但必须按顺序通过门禁：

### Subtask A — 固化运行时规则
目标：
- 将 Python 运行时规则写入 `memory-bank/schema/AGENTS.md`
- 在 `findings.md` 中记录当前项目运行时口径
- 在 `decisions.md` 中记录“禁止依赖外层 shell 已激活虚拟环境”的决定

通过标准：
- `AGENTS.md` 已包含固定解释器、固定工作目录、`PYTHONPATH=src`、任务前验证规则
- `findings.md` 和 `decisions.md` 已同步

### Subtask B — Goal Stack 最小占位注入
目标：
- 在 `src/core/coordinator.py` 中增加最小 Goal Stack 占位函数
- Goal Stack 至少包含：
  - `global_goal`
  - `step_goal`
  - `task_goal`
  - `current_action`
  - `done_definition`
  - `out_of_scope`
- 仅作为 Phase 1 占位对象，不做完整 task orchestration

通过标准：
- 可导入该函数
- 返回对象中包含上述键
- 不破坏现有 mode 逻辑

### Subtask C — mode 传递与 token risk 最小补齐
目标：
- 检查 `main.py -> coordinator.py -> engine.py` 的 mode 传递链是否完整
- 若缺少最小挂点，则补齐，但只做 Phase 1 范围内最小补缺
- 在控制台或日志侧加入 token risk 的最小可见输出（若基线中尚未明显暴露）

通过标准：
- `RunMode` / `wiki_strict` 不被回退或覆盖
- `standard` 逻辑不被破坏
- token risk 至少可被观察到（print/log/hook 任一最小方式均可）

### Subtask D — 文档与状态同步
目标：
- 更新 `progress.md`
- 更新 `architecture.md`
- 记录本模块做了什么、如何验证、仍然延后的问题

通过标准：
- 记录完整
- 未把 Phase 2+ 的内容标为已完成

## Required Tests
### 0. 运行时验证（必须先执行）
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python --version
```

```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.config import RunMode; print('runtime ok')"
```

### 1. Goal Stack 占位验证
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.coordinator import get_minimal_goal_stack; gs=get_minimal_goal_stack(); required=['global_goal','step_goal','task_goal','current_action','done_definition','out_of_scope']; [gs[k] for k in required]; print('Goal Stack placeholder OK')"
```

### 2. mode / token budget 相关导入验证
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.config import RunMode, get_run_mode; from core.token_budget import TokenBudgetManager; print('config/token_budget OK')"
```

### 3. pytest 最小回归
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -m pytest tests/ -q
```

## Pass Criteria
只有同时满足以下条件，整个模块才算完成：
1. 运行时验证通过
2. `AGENTS.md` 已固化 Python 运行时规则
3. `coordinator.py` 已有最小 Goal Stack 占位
4. mode 传递链未被破坏
5. token risk 有最小可见输出或确认已存在且可见
6. pytest 最小回归通过
7. `progress.md` / `architecture.md` / `findings.md` / `decisions.md` 已同步

## If Tests Fail
- 每个失败点最多修复 2 轮
- 任一测试连续失败 2 轮后，立即停止
- 输出阻塞报告，格式必须包括：
  1. 已完成子任务
  2. 失败命令
  3. 错误摘要
  4. 推测原因
  5. 需要人工决策的问题

## On Success
1. 更新：
   - `memory-bank/progress.md`
   - `memory-bank/architecture.md`
   - `memory-bank/findings.md`
   - `memory-bank/decisions.md`
2. 输出：
   - 修改文件列表
   - 测试结果
   - 文档更新摘要
   - 仍延后的问题
3. 停止，不进入下一个模块
