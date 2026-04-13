# Phase 1 Exec — 模式接入与结构骨架

## 前置条件
- Phase 0 已通过验收
- `memory-bank/system-design-v2.md` 已存在
- 当前执行依据不再使用旧 Step 4

## 本阶段目标
完成 `wiki_strict` 的最小模式接入和 Wiki 运行时骨架，让系统能：
1. 启动 `wiki_strict`
2. 初始化 `.cc-mini/wiki/` 基础目录
3. 生成结构骨架页
4. 显示最小 token 风险等级
5. 注入 Goal Stack 占位信息

## In Scope
1. `src/core/main.py`：增加 `--mode wiki_strict`
2. `src/core/config.py`：增加 `RunMode`
3. `src/core/coordinator.py`：区分 `standard` 与 `wiki_strict`
4. `.cc-mini/wiki/` 目录初始化
5. `index.md` / `log.md` / `inbox/*.md` 初始化
6. `knowledge/ingester.py` 最小结构扫描骨架
7. `knowledge/watcher.py` 最小 stale 标记骨架
8. `token_budget.py` 的 usage ratio / risk level 显示
9. `engine.py` 中 Goal Stack 的最小注入点

## Out of Scope
1. 不实现 digest 逻辑
2. 不实现 TaskPack / EditSpec
3. 不实现 dehydration / snapshot 正式流程
4. 不实现 ASTRead / patch / debug / retry
5. 不实现 archive / reconcile / lint

## 允许修改的文件
- `src/core/main.py`
- `src/core/config.py`
- `src/core/coordinator.py`
- `src/core/knowledge/ingester.py`
- `src/core/knowledge/watcher.py`
- `src/core/token_budget.py`
- `src/core/engine.py`
- `.cc-mini/wiki/**` 初始化文件
- `memory-bank/progress.md`
- `memory-bank/architecture.md`

## 不允许修改的文件
- 任何 digest / taskpack / patch / debug 实现文件（若尚不存在，不要提前创建完整逻辑）
- 任何 archive / reconcile / Obsidian 运维相关代码

## 验收标准
1. `wiki_strict` 模式可启动
2. `standard` 模式不被破坏
3. `.cc-mini/wiki/` 基础目录和基础文件可创建
4. 能生成 `raw_ast` 骨架页
5. 控制台能显示 token usage ratio / risk level
6. Goal Stack 占位对象已接入，但仍是最小占位版本

## Stop Conditions
1. 如果需要写 digest，停止，留到 Phase 2
2. 如果需要写 TaskPack / EditSpec，停止，留到 Phase 3
3. 如果需要写 patch / debug，停止，留到 Phase 4

## Direct Runner Prompt
请只执行 Phase 1。
只实现模式接入、Wiki 运行时骨架、最小 token 风险监控和 Goal Stack 占位接入。
不要实现 digest、TaskPack、patch、debug。
完成后只输出：
1. 新增/修改了哪些文件
2. 是否通过本 Phase 验收
3. 哪些内容被刻意延后
