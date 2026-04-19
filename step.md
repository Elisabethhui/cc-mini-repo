# cc-mini 32K Context Enhancement — 执行步骤

## 已完成的工作

### 1. 代码库分析 (`/gsd-map-codebase`)
- 生成了 7 个代码库文档在 `.planning/codebase/`
- 包含：ARCHITECTURE.md, CONCERNS.md, CONVENTIONS.md, INTEGRATIONS.md, STACK.md, STRUCTURE.md, TESTING.md

### 2. 项目初始化 (`/gsd-new-project --auto`)
- 创建了 `.planning/config.json` — 项目配置（yolo 模式、粗粒度、并行执行）
- 创建了 `.planning/PROJECT.md` — 项目定义和范围
- 运行了 4 个并行研究代理（Stack/Features/Architecture/Pitfalls）
- 生成了 `.planning/research/` 下的 5 个研究文档

### 3. 需求定义
- 创建了 `.planning/REQUIREMENTS.md`
- 25 个 v1 需求，覆盖：安全(5)、Token/预算(4)、上下文管理(5)、Wiki 基础设施(6)、测试(5)

### 4. 路线图创建
- 创建了 `.planning/ROADMAP.md`
- **3 个阶段**：
  - Phase 1: Foundation & Security（基础+安全）
  - Phase 2: Context Management Core（上下文管理核心）
  - Phase 3: Testing & Validation（测试与验证）

### 5. Phase 1 讨论 (`/gsd-discuss-phase 1 --auto`)
- 创建了 `.planning/phases/01-foundation-security/01-CONTEXT.md`
- 创建了 `.planning/phases/01-foundation-security/01-DISCUSSION-LOG.md`
- 自动决策了 15 个实现决策（token 计数策略、安全加固优先级、wiki 路径、FlowState 迁移、预算状态机）

## 当前状态

Phase 1 的规划被中断。需要继续完成规划并执行。

## 接下来的步骤

### 步骤 1: 完成 Phase 1 规划 (`/gsd-plan-phase 1 --auto`)

运行命令继续规划 Phase 1。规划器会：
1. 读取已有的 CONTEXT.md 和研究文档
2. 创建详细的执行计划（PLAN.md）
3. 包含具体的任务、接受标准、文件修改清单

```bash
# 在 claude 中运行：
/gsd-plan-phase 1 --auto
```

**预期输出**：`.planning/phases/01-foundation-security/01-PLAN.md`

---

### 步骤 2: 执行 Phase 1 (`/gsd-execute-phase 1 --auto`)

规划完成后，自动执行 Phase 1 的所有任务：

```bash
# 在 claude 中运行：
/gsd-execute-phase 1 --auto
```

**Phase 1 包含的工作内容**：

#### 安全加固（SEC-01~05）
- [ ] BashTool：移除 `shell=True`，改用 `shell=False` + `shlex.split()`
- [ ] 文件工具：添加 `PathSandbox`，限制操作在项目根目录
- [ ] GrepTool：添加正则验证和 5 秒超时
- [ ] Config：将 `load_dotenv()` 从模块导入移至 `main()` 显式调用
- [ ] 沙盒模式：对所有写工具和 Bash 执行强制启用

#### Token 计数修复（TOK-01~04）
- [ ] 集成 `tiktoken`（OpenAI）和 `anthropic.beta.messages.count_tokens()`（Claude）
- [ ] 移除 `engine.py` 中的 1.5x 安全乘数
- [ ] 模型感知的预算阈值（32K vs 200K）
- [ ] 显式预算状态机：NORMAL → WARNING → COMPACT → CHECKPOINT → HARD_STOP

#### Wiki 基础设施修复（WIK-01~06）
- [ ] 将所有硬编码 `.cc-mini/` 路径替换为 `config.py` 中的可配置工作区目录
- [ ] 修复 `/dream` 命令：添加 `try/finally` 确保消息恢复
- [ ] 修复 `/plan` 类型安全：`plan_manager` 类型从 `object` 改为 `PlanModeManager`
- [ ] 强制使用 `FlowState` 枚举，替换字符串状态名
- [ ] 修复 `PostEditGuard` 处理 `ast.AsyncFunctionDef`
- [ ] 修复 wiki watcher：添加防抖和指数退避

---

### 步骤 3: Phase 2 讨论 (`/gsd-discuss-phase 2 --auto`)

Phase 1 完成后，进入 Phase 2（上下文管理核心）：

```bash
/gsd-discuss-phase 2 --auto
```

**Phase 2 范围**：
- 实现滑动窗口消息管理
- 将脱水服务接入引擎预检循环
- 修复 CompactService 适配 32K 模型
- 添加预算状态机转换逻辑

---

### 步骤 4: Phase 2 规划与执行

```bash
/gsd-plan-phase 2 --auto
/gsd-execute-phase 2 --auto
```

---

### 步骤 5: Phase 3 测试与验证

```bash
/gsd-discuss-phase 3 --auto
/gsd-plan-phase 3 --auto
/gsd-execute-phase 3 --auto
```

---

## 快速参考命令

| 阶段 | 命令 |
|------|------|
| 查看项目状态 | `/gsd-progress` |
| 查看当前路线图 | `cat .planning/ROADMAP.md` |
| 查看 Phase 1 上下文 | `cat .planning/phases/01-foundation-security/01-CONTEXT.md` |
| 继续规划 Phase 1 | `/gsd-plan-phase 1 --auto` |
| 执行 Phase 1 | `/gsd-execute-phase 1 --auto` |
| 代码审查 | `/gsd-code-review` |
| 验证工作 | `/gsd-verify-work` |

## 关键文件位置

```
.planning/
├── PROJECT.md              # 项目定义
├── REQUIREMENTS.md         # 需求文档
├── ROADMAP.md              # 路线图
├── STATE.md                # 项目状态
├── config.json             # 配置
├── research/               # 研究文档
│   ├── STACK.md
│   ├── FEATURES.md
│   ├── ARCHITECTURE.md
│   ├── PITFALLS.md
│   └── SUMMARY.md
└── phases/
    └── 01-foundation-security/
        ├── 01-CONTEXT.md           # Phase 1 决策上下文
        ├── 01-DISCUSSION-LOG.md    # 讨论日志
        └── 01-PLAN.md              # [待创建] 执行计划
```

## 当前 Git 状态

分支：`project-cleanup`
最近的提交：
- `5c51db1` docs(01): capture phase 1 context and discussion log
- `eee614f` docs: create roadmap with 3 phases
- `3614795` docs: define v1 requirements
- `4cace4b` docs: complete project research
- `02e4b13` chore: initialize GSD project
