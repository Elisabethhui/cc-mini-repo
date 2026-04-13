# Current Task — Phase 5 Accelerated Module

## Task ID
phase-5-accelerated-reconcile-archive-ops

## Task Name
实现 reconcile / archive / query-archive / stale recovery / lint 最小闭环

## Goal
在 Phase 4 的安全修改与局部 debug 闭环基础上，一次性完成 Phase 5 的最小可用模块：
1. reconcile
2. archive
3. query-archive
4. stale recovery
5. lint / health check
6. context snapshot / deferred issue / taskpack 的维护与回收

## Current Baseline
假设前置条件：
- Phase 4 已通过
- 当前已具备 Wiki 语义层、任务层、修改层
- 当前进入 Phase 5，不再重复实现 Phase 2/3/4

## Runtime Rules
### Fixed Python
`/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python`

### Fixed Workdir
`/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo`

### Required Import Prefix
`PYTHONPATH=src`

## Allowed Read
- `memory-bank/system-design-v2.md`
- `memory-bank/progress.md`
- `memory-bank/architecture.md`
- `memory-bank/findings.md`
- `memory-bank/decisions.md`
- `memory-bank/phases/phase-5-exec.md`（若无则按系统设计执行）
- `memory-bank/schema/AGENTS.md`
- `memory-bank/schema/digest_policy.md`
- `memory-bank/schema/conflict_policy.md`
- `memory-bank/schema/context_safeguard_policy.md`
- `memory-bank/schema/goal_policy.md`
- `.cc-mini/wiki/**`
- `src/core/wiki/**`
- `src/core/knowledge/**`
- `src/core/session.py`
- `src/core/flow_state.py`

## Allowed Modify
- `src/core/wiki/reconcile.py`（如不存在可创建）
- `src/core/wiki/archive.py`（如不存在可创建）
- `src/core/wiki/query_archive.py`（如不存在可创建）
- `src/core/wiki/lint.py`（如不存在可创建）
- `src/core/knowledge/watcher.py`
- `src/core/flow_state.py`
- `src/core/session.py`
- `.cc-mini/wiki/archive/**`
- `.cc-mini/wiki/reports/**`
- `.cc-mini/wiki/index.md`
- `.cc-mini/wiki/log.md`
- `memory-bank/progress.md`
- `memory-bank/architecture.md`
- `memory-bank/findings.md`
- `memory-bank/decisions.md`

## Out of Scope
- 不实现 Obsidian 深度联动
- 不实现团队级多 agent 编排
- 不重写已有 digest / taskpack / patch 基础设施
- 不进入额外新 Phase
- 不做与当前最小闭环无关的大规模清理

## Sequential Subtasks

### Subtask A — reconcile
目标：
- 对 stale / drift / digest 过期页面建立最小 reconcile 路径
- 能识别需要重建或延后的对象

完成标准：
- 至少存在一个 reconcile 入口
- stale 页面不会一直悬空无人处理

### Subtask B — archive / query-archive
目标：
- 对旧 snapshot / 旧 taskpacks / 旧 reports 建立归档路径
- 提供 query-archive 的最小查找能力

完成标准：
- archive 目录可写
- 至少能按简单条件读取已归档对象

### Subtask C — lint / health check
目标：
- 对 `.cc-mini/wiki/` 做最小健康检查
- 包括：
  - index / log 是否存在
  - 关键目录是否缺失
  - taskpack / snapshot / report 是否孤儿化

完成标准：
- 至少存在一个 lint / health check 入口
- 输出 agent-readable 结果

### Subtask D — stale recovery / maintenance
目标：
- 将 snapshot / deferred issue / taskpack / digest 页面的生命周期纳入维护逻辑
- 保持索引和日志一致

完成标准：
- 至少存在一条 stale recovery 路径
- 不再只生成，不维护

### Subtask E — 文档同步
目标：
- 更新 `progress.md`
- 更新 `architecture.md`
- 更新 `findings.md`
- 必要时更新 `decisions.md`

完成标准：
- 文档反映实际实现
- 写明 Phase 5 的最小进入/退出条件

## Required Runtime Validation (Before Coding)
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python --version
```

```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.config import RunMode; print('runtime ok')"
```

## Required Tests
### Import / Runtime Tests
至少验证：
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "print('phase5 runtime ok')"
```

### Targeted Behavior Tests
要求 Claude 增加至少以下验证中的一部分：
- reconcile 可触发
- archive 可写入
- query-archive 可返回结果
- lint / health check 可输出结果
- stale recovery 可标记需要处理对象

### pytest
如果已有相关测试：
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -m pytest tests/ -q
```

## Pass Criteria
- reconcile / archive / query-archive / lint 至少有最小可用闭环
- stale recovery 存在
- Required Tests 通过
- 仅修改 Allowed Modify 范围内文件

## If Tests Fail
- 最多修复 2 轮
- 2 轮后仍失败，立即停止
- 输出：
  1. 已完成子任务
  2. 失败命令
  3. 错误摘要
  4. 仍未解决的问题
  5. 是否需要人工裁决

## On Success
1. 更新：
   - `memory-bank/progress.md`
   - `memory-bank/architecture.md`
   - `memory-bank/findings.md`
   - `memory-bank/decisions.md`（如有新增拍板）
2. 输出：
   - 修改文件列表
   - 子任务完成情况
   - 测试结果
   - 当前 Phase 5 是否通过
   - 后续长期运维建议
3. 成功后停止，不自动进入新阶段
