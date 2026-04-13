# Phase 0 Exec: 规则与契约定稿

版本：v2.0 Phase 0
日期：2026-04-11
状态：已完成

---

## 本阶段目标

在写任何实现代码之前，先把系统的制度层讲清楚。

---

## 任务清单

### Task 1: 验证 schema 规则层完整性

**目标**：确保所有 v2.0 所需的 policy 文件已就位。

**检查项**：
- [x] `schema/AGENTS.md` — AI 执行者工作纪律
- [x] `schema/conventions.md` — 命名、frontmatter、元数据契约
- [x] `schema/digest_policy.md` — digest 定义与状态转换
- [x] `schema/conflict_policy.md` — 冲突处理与优先级
- [x] `schema/taskpack_policy.md` — TaskPack 定义与内容
- [x] `schema/watchdog_policy.md` — Watchdog 职责边界
- [x] `schema/context_safeguard_policy.md` — Context Safeguard 契约
- [x] `schema/goal_policy.md` — Goal Anchoring 契约
- [x] `schema/phase_boundary_policy.md` — Phase 0-4 边界定义

**完成标准**：所有文件存在且内容符合 v2.0 设计。

---

### Task 2: 补充 conventions.md 的 v2.0 字段

**目标**：确保 frontmatter 契约包含 v2.0 新增字段。

**需要补充的字段**：
- `goal_refs` — Goal Stack 引用
- `snapshot_refs` — Context Snapshot 引用
- `deferred_issue_refs` — Deferred Issue 引用

**完成标准**：conventions.md 中已定义上述字段的用途和格式。

---

### Task 3: 创建 Phase 0 执行记录

**目标**：创建本文件 (phase-0-exec.md)。

**完成标准**：
- [x] phases/ 目录已创建
- [x] phase-0-exec.md 已创建

---

### Task 4: 更新 progress.md

**目标**：记录项目进入 Phase 0 状态。

**需要更新的内容**：
- 当前状态：Phase 0 进行中
- 已完成：Step 1-3, reset-note-v2, system-design-v2-full, phase-0-4-full-guide
- 进行中：Phase 0 规则层定稿
- 下一步：Phase 0 完成后进入 Phase 1

**完成标准**：progress.md 已更新 Phase 0 状态。

---

### Task 5: 更新 architecture.md

**目标**：记录 v2.0 架构元素和新增文件。

**需要记录的内容**：
- v2.0 新增架构元素：Context Safeguard, Goal Anchoring
- phases/ 目录结构
- schema/ 中的新增 policy 文件

**完成标准**：architecture.md 反映当前 v2.0 架构状态。

---

## 本阶段 Out of Scope（明确不做）

根据 phase_boundary_policy.md：

1. 不写业务逻辑代码
2. 不实现 `/scan`、`/digest`、`/prime`
3. 不实现 patch / debug / retry
4. 不实现 archive / reconcile
5. 不实现 frontmatter 解析器、校验器
6. 不决定 Python 类型系统（dataclass vs pydantic）
7. 不决定持久化文件的具体目录组织

---

## 完成验收标准

Phase 0 完成时必须满足：

1. [x] 所有 schema policy 文件就位且一致
2. [x] conventions.md 已包含 v2.0 新增字段
3. [x] phase-0-exec.md 已创建
4. [x] progress.md 已更新 Phase 0 状态
5. [x] architecture.md 已记录 v2.0 架构元素
6. [x] 无后续阶段问题被提前实现（如有，已写入 Deferred Issue）

**状态：Phase 0 已完成**

---

## 风险与 Deferred Issues

**潜在 Deferred Issues**：
- TaskPack 与 EditSpec 是否同文件 → 留到 Phase 3
- 具体 YAML 字段校验器实现 → 留到 Phase 1-2
- archive/reconcile 的精确算法 → 留到 Phase 5

---

## 下一步

Phase 0 完成后，进入 **Phase 1：模式接入与结构骨架**。
