# Progress

## 项目
CC-MINI Wiki-Strict 模式升级项目

## 当前状态
当前项目已**正式回退到 Step 3 完成态**。

这意味着：
- Step 1：memory-bank 基础文件 有效
- Step 2：schema 规则层骨架 有效
- Step 3：frontmatter 规范 有效
- 旧 Step 4：**作废，不再作为后续执行依据**

## 回退原因
1. 旧 Step 4 相关内容主要由本地 32K 小模型参与生成，质量与边界控制不足。
2. 后续新增了两个关键系统能力，会影响整个后续阶段设计：
   - Context Safeguard（OOM 预警 / 上下文脱水 / 快照恢复）
   - Goal Anchoring & Drift Recovery（目标锚定 / 防偏航 / Re-anchor / Micro-Fork）
3. 因此后续不应继续在旧 Step 4 基础上修补，而应先升级总设计，再重新进入执行期。

## 已确认有效的内容
1. `memory-bank/` 目录结构本身有效。
2. 以下文件继续保留：
   - `game-design-document.md`
   - `tech-stack.md`
   - `implementation-plan.md`
3. 以下规则层文件继续保留，并将在后续增量升级：
   - `schema/AGENTS.md`
   - `schema/conventions.md`
   - `schema/digest_policy.md`
   - `schema/conflict_policy.md`
   - `schema/taskpack_policy.md`
   - `schema/watchdog_policy.md`

## 已失效 / 降级为历史草稿的内容
以下内容不再作为后续执行依据：
1. 旧 Step 4 的设计文档
2. 旧 Step 4 的执行包
3. 旧 Step 4 的复核清单
4. 基于旧 Step 4 延伸出的后续执行推演

若这些文件已落盘，应移动到：
- `memory-bank/deprecated/old-step-4/`

## 当前进入的新阶段
当前项目进入：
**v2.0 升级整理期**

当前唯一有效的后续依据应为：
1. `system-design-v2.md`
2. `phase-0-4-compact-index.md`
3. `phases/phase-0-exec.md` ~ `phase-4-exec.md`
4. 新增的三份 schema policy：
   - `context_safeguard_policy.md`
   - `goal_policy.md`
   - `phase_boundary_policy.md`

## 下一步建议

### 先做文档系统升级，不写业务代码
推荐顺序：
1. 新增 `reset-note-v2.md`
2. 新增 `system-design-v2.md`
3. 新增 `phase-0-4-compact-index.md`
4. 新增 `phases/` 目录与 `phase-0-exec.md` ~ `phase-4-exec.md`
5. 新增 `schema/context_safeguard_policy.md`
6. 新增 `schema/goal_policy.md`
7. 新增 `schema/phase_boundary_policy.md`
8. 更新本文件与 `architecture.md`

### 后续重新开始点
后续执行统一**从 Phase 0 重新开始**。

原因：
- 现在要重做的是制度层和阶段边界
- Phase 0 是新规则体系正式落盘的入口
- 不应直接跳回旧 Step 4 或旧执行链

## 当前不应该做的事情
1. 不要继续沿用旧 Step 4 文件
2. 不要直接进入新的代码实现阶段
3. 不要让本地 32K 小模型继续主导制度层裁决
4. 不要把后续 Phase 1–4 的实现与当前 reset 工作混在一起

## 备注
本文件从现在开始，服务于 **v2.0 升级后的项目状态记录**。

