# Phase 0 Exec — 规则与契约升级

## 当前定位
- 当前项目状态：**已回退到 Step 3**
- 旧 Step 4：**失效，不再作为执行依据**
- 当前重新开始点：**Phase 0**

## 本阶段目标
把 v2.0 的制度层真正落到 `memory-bank/`：
1. 把新增的两块能力正式写入规则层
   - Context Safeguard
   - Goal Anchoring & Drift Recovery
2. 让后续 Phase 1–4 有统一边界，不再沿用旧 Step 4 思路
3. 只更新文档与规则，不写任何 Python 业务逻辑

## In Scope
只允许处理以下内容：
1. `memory-bank/reset-note-v2.md`
2. `memory-bank/system-design-v2.md`
3. `memory-bank/phase-0-4-compact-index.md`
4. `memory-bank/schema/context_safeguard_policy.md`
5. `memory-bank/schema/goal_policy.md`
6. `memory-bank/schema/phase_boundary_policy.md`
7. 必要时增量更新：
   - `memory-bank/progress.md`
   - `memory-bank/architecture.md`
   - 与新增规则直接冲突的既有 schema 文件

## Out of Scope
本阶段明确不处理：
1. 不写 `src/` 下任何 Python 业务代码
2. 不接入 `--mode wiki_strict`
3. 不实现 `/scan`、`/digest`、`/prime`、`/plan`
4. 不实现 token budget 逻辑、dehydrator、snapshot writer
5. 不实现 ASTRead / strict patch / debug / retry
6. 不修复所有历史规则冲突，只定义制度边界

## 本阶段必须拍板的问题
1. Context Safeguard 的职责边界是什么
2. Goal Stack / Deferred Issue / Micro-Fork / Re-anchor 的正式定义是什么
3. 各 Phase 的边界是什么，哪些问题必须延后
4. 旧 Step 4 为什么失效，后续为什么从 Phase 0 重新开始

## 允许修改的文件
- `memory-bank/reset-note-v2.md`
- `memory-bank/system-design-v2.md`
- `memory-bank/phase-0-4-compact-index.md`
- `memory-bank/schema/context_safeguard_policy.md`
- `memory-bank/schema/goal_policy.md`
- `memory-bank/schema/phase_boundary_policy.md`
- `memory-bank/progress.md`
- `memory-bank/architecture.md`

## 不允许修改的文件
- `src/**`
- `.cc-mini/wiki/**`
- 任何业务代码、测试代码、运行时代码
- 旧 Step 4 的 deprecated 文件（只允许查看，不允许恢复到主路径）

## 验收标准
只有同时满足以下条件，Phase 0 才算完成：
1. 三个新增 policy 文件存在且职责清晰
2. `reset-note-v2.md` 明确声明“回退到 Step 3，旧 Step 4 失效”
3. `system-design-v2.md` 成为后续唯一总设计依据
4. `phase-0-4-compact-index.md` 明确各 Phase 边界
5. `progress.md` 和 `architecture.md` 已反映 Phase 0 完成态
6. 没有改动任何 Python 业务逻辑代码

## Stop Conditions
出现以下情况必须停止：
1. 需要开始写 `src/` 下代码
2. 需要开始定义运行时对象、解析器、校验器
3. 需要推进到 Phase 1 的模式接入
4. 需要恢复旧 Step 4 内容到主路径

## Direct Runner Prompt
请只执行 Phase 0。
只允许修改 memory-bank/ 下的规则和记录文件，不要写任何 Python 业务代码。
若发现后续 Phase 问题，只记录为 deferred issue，不要继续扩写。
完成后只输出：
1. 新增/修改了哪些文件
2. 是否通过本 Phase 验收
3. 哪些问题被刻意延后
