# Exec Packs README（增强版）

## 目录目的
`memory-bank/exec-packs/` 用于存放 **给 Claude Code / Codex / cc-mini 的最小执行包**。

这些文件不是长期规则层，也不是完整设计文档，而是：
- 从长期规则层“编译”出来的当前执行单元
- 用于降低 32K 小模型的上下文压力
- 用于明确当前动作边界，防止跨阶段漂移

## 与其他目录的关系
### 1. `memory-bank/schema/`
职责：长期规则层。
- 定制度
- 定边界
- 定元数据契约
- 不直接作为每次执行的 worker prompt

### 2. `memory-bank/phases/`
职责：阶段级 Runner Brief。
- 用于当前 Phase 的整体执行
- 每次只喂一个 phase 文件
- 用于阶段级校准和阶段级执行

### 3. `memory-bank/exec-packs/`
职责：步骤级 / 动作级最小执行包。
- 比 phase 文件更小
- 比长期规则更窄
- 更适合单个动作、单次 patch、单个文档创建任务

## 推荐使用顺序
### 情况 A：第一次进入一个新 Phase
优先给执行器：
1. 当前 `phases/phase-N-exec.md`
2. `progress.md`
3. `architecture.md`
4. 当前最相关的 1–3 个 schema 文件

### 情况 B：已经进入某个 Phase，要做单个动作
优先给执行器：
1. 当前 `exec-pack` 文件
2. 必要时附加当前 `phases/phase-N-exec.md`
3. 当前要改的目标文件

## 为什么不能直接把整个 memory-bank 喂给 32K 小模型
因为这会导致：
1. 上下文膨胀
2. 跨阶段混用
3. 把 deferred issue 当成当前任务来解决
4. plan 模式自由散开，最后跑偏

## 推荐的最小执行包结构
一个标准 exec-pack 建议包含：
1. Current Step / Action
2. Goal
3. In Scope
4. Out of Scope
5. Files Allowed To Read
6. Files Allowed To Modify
7. Required Rules
8. Expected Output
9. Acceptance Checks
10. Stop And Ask Conditions

## 当前项目特别注意事项
### 1. 当前状态不是旧 Step 4
当前项目已回退到 Step 3，并切换到 v2.0 体系。
旧 Step 4 相关文件只允许保留在 `deprecated/old-step-4/`，不能恢复到主路径。

### 2. 后续执行以哪个为准
- 总设计：`system-design-v2.md`
- 阶段执行：`phases/phase-0-exec.md` ~ `phase-4-exec.md`
- 步骤级动作：`exec-packs/*.md`

### 3. 当前如果是新手操作
最稳的方式是：
- 先给 Claude Code 一个 `phase` 文件做校准
- 再给它一个更小的 `exec-pack` 文件做单动作执行
- 完成后回到 ChatGPT 复核

## 当前目录最少应该具备
- `README.md`
- `step-template-exec-pack.md`
- `step-template-review-checklist.md`
- `phase-template-exec-pack.md`
- `phase-template-review-checklist.md`

如果这些模板尚未存在，建议由长期规则层提供标准版本，不要让 32K 模型自行发明格式。
