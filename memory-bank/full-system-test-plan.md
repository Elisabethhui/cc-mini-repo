# CC-MINI Wiki-Strict 全系统验收测试方案

## 文档目的
本方案用于在 Phase 5 完成后，对整个项目进行系统级验收，确认：
1. 功能是否完整
2. 各阶段能力是否真正串起来
3. standard 模式是否未被破坏
4. wiki_strict 模式是否可用、可维护、可恢复

---

## 一、先明确“什么叫做功能完善”

“功能完善”不等于“代码都写完了”，而是至少满足下面 6 个维度：

### 1. 运行维度
- 固定 Python 运行时可用
- CLI 可启动
- 关键模块可导入
- pytest 全绿

### 2. 模式维度
- `standard` 模式可继续工作
- `wiki_strict` 模式可进入完整流程
- 两种模式显式隔离，互不污染

### 3. Phase 链路维度
- Phase 1：模式接入与结构骨架可用
- Phase 2：scan / digest / snapshot 可用
- Phase 3：TaskPack / EditSpec / prime / plan 可用
- Phase 4：ASTRead / strict patch / retry / Re-anchor 可用
- Phase 5：reconcile / archive / query-archive / lint / maintenance 可用

### 4. 失败处理维度
- 运行时错误时不会静默失败
- 重复失败时会停止并提示
- 无法完成时能输出阻塞信息
- OOM / 高 token 风险时有最小保护逻辑

### 5. 文档同步维度
- `progress.md`
- `architecture.md`
- `findings.md`
- `decisions.md`
与当前代码状态一致

### 6. 持续使用维度
- 新任务进入流程清晰
- 当前任务可通过 `memory-bank/current-task.md` 驱动
- Wiki 可持续维护，不是一次性缓存

---

## 二、测试总策略

推荐按 4 层测试：

### Layer A：环境与启动烟雾测试
目标：确认项目“能起得来”。

### Layer B：模块级回归测试
目标：确认核心模块导入与关键行为可用。

### Layer C：端到端流程测试
目标：确认 Phase 1 → Phase 5 串联后可工作。

### Layer D：运维与恢复测试
目标：确认归档、恢复、reconcile、lint、maintenance 真的可用。

---

## 三、测试前准备

### 固定解释器
统一使用：

`/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python`

### 固定工作目录
统一在：

`/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo`

### 固定导入前缀
所有需要导入 `src/core/...` 的测试命令，统一带：

`PYTHONPATH=src`

---

## 四、Layer A：环境与启动烟雾测试

### A1. 解释器与导入
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python --version
```

```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.config import RunMode; print('runtime ok')"
```

### A2. CLI 帮助信息
根据你的实际入口模块调整，目标是至少验证：
```bash
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -m cc_mini --help
```

### A3. 模式帮助
```bash
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -m cc_mini --mode standard --help
```

```bash
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -m cc_mini --mode wiki_strict --help
```

### A 层通过标准
- 解释器正确
- 核心入口可启动
- standard / wiki_strict 两种模式都可识别

---

## 五、Layer B：模块级回归测试

### B1. 核心模块导入
建议验证以下模块：

- `core.config`
- `core.token_budget`
- `core.flow_state`
- `core.coordinator`
- `core.checkpoint`
- `core.dehydration`
- `core.knowledge.ingester`
- `core.knowledge.watcher`

### B2. Phase 4 关键模块
- `core.tools.ast_read`
- `core.tools.file_edit`

### B3. Phase 5 关键模块
- `core.wiki.reconcile`
- `core.wiki.archive`
- `core.wiki.query_archive`
- `core.wiki.lint`
- `core.wiki.maintenance`

### B4. pytest 回归
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -m pytest tests/ -v
```

### B 层通过标准
- 所有关键模块可导入
- pytest 全部通过

---

## 六、Layer C：端到端流程测试（最重要）

这里不是单测，而是“真的按用户视角走一遍”。

### 场景 1：新项目 / 新任务进入
目标：
- 创建或更新 `memory-bank/current-task.md`
- 让 Claude 按 current-task 执行
- current-task 中的限制能被遵守

验证点：
- 只读取允许文件
- 只修改允许文件
- 测试通过后才更新 progress / architecture
- 成功后停止，不自动进入下一阶段

### 场景 2：wiki_strict 下做 scan / digest
目标：
- 对一个目标文件跑 `/scan`
- 再跑 `/digest`
- 检查 `.cc-mini/wiki/entities/**` 是否生成或升级

验证点：
- `raw_ast -> partially_digested / digested`
- `log.md` 有记录
- 不破坏 standard 模式

### 场景 3：prime / plan
目标：
- 对一个实际任务运行 `/prime`
- 再运行 `/plan`

验证点：
- 生成 TaskPack
- 生成 EditSpec
- 生成 Goal Stack
- 生成 Patch Plan（只计划，不执行）

### 场景 4：局部 patch / verify / retry
目标：
- 选一个非常小的真实修改任务
- 通过 ASTRead 找到目标
- 应用 strict patch
- 跑 verify
- 人为制造一次失败，观察 retry / Re-anchor 是否触发

验证点：
- patch 可预览
- patch 可回滚
- 重试不会无限循环
- ask_user fallback 可进入

### 场景 5：reconcile / archive / query-archive
目标：
- 选择一些旧对象执行 archive
- 再 query-archive 查询
- 对 stale 页面执行 reconcile

验证点：
- archive 可写入
- query-archive 能返回结果
- stale 页面不会永远滞留

### C 层通过标准
- 至少跑通 1 个完整“任务进入 → 计划 → 小修改 → 验证 → 归档维护”的闭环

---

## 七、Layer D：运维与恢复测试

### D1. 中断恢复
目标：
- 中途退出会话
- 重新进入后，能通过：
  - `progress.md`
  - `architecture.md`
  - `findings.md`
  - `decisions.md`
  - `.cc-mini/wiki/**`
恢复当前状态

### D2. snapshot / maintenance
目标：
- 制造一次需要 snapshot 的情况
- 检查 snapshot 是否能写入并参与恢复

### D3. lint / health check
目标：
- 故意制造一个小的不一致，例如缺 index 条目
- 看 lint 是否能报告出来

### D 层通过标准
- 中断后可继续
- 健康检查能发现问题
- 维护逻辑不是摆设

---

## 八、建议的最终验收清单

### 必过项
- [ ] 运行时与 CLI 正常
- [ ] pytest 全绿
- [ ] standard 模式正常
- [ ] wiki_strict 模式正常
- [ ] scan / digest / digest-changed 正常
- [ ] TaskPack / EditSpec / prime / plan 正常
- [ ] ASTRead / patch / retry / Re-anchor 正常
- [ ] reconcile / archive / query-archive / lint / maintenance 正常
- [ ] progress / architecture / findings / decisions 已同步

### 建议补充项
- [ ] 做一次“真实任务闭环”录屏或命令日志保存
- [ ] 固化一份 release checklist
- [ ] 固化一份 demo 脚本

---

## 九、如果你想确认“项目是否可交付”
满足下面 3 条，就可以认为已经到“可交付 Beta”：

1. 277 个测试全绿，且关键 CLI/模块入口可跑通
2. 至少 1 条真实任务链路从 current-task 到归档维护跑通
3. 文档与代码同步，别人按说明能复现最小流程
