# CC-MINI Wiki-Strict 使用说明与项目说明

## 一、项目说明（Project Overview）

### 项目名称
CC-MINI Wiki-Strict 增强框架

### 项目目标
在不破坏原有 `standard` 模式的前提下，为 cc-mini 增加一套更适合本地 32K 小模型的 `wiki_strict` 工作模式。

### 解决的问题
这个项目主要解决以下问题：

1. **上下文太短**
   - 小模型容易 OOM
   - 长任务容易失忆
   - 需要把知识持久化到文件，而不是只靠上下文

2. **代码修改容易失控**
   - 模型容易整文件重写
   - 修改前没有先定位目标
   - debug 时容易重复失败、无限重试

3. **任务边界容易漂移**
   - 模型计划时会中途跑偏
   - 会把后续阶段问题提前拉进来
   - 需要 Goal Stack / Re-anchor / Deferred Issue 约束

4. **知识维护能力不足**
   - 只会生成 Wiki，不会维护
   - stale 页面、旧 snapshot、旧 taskpack 无法持续回收
   - 需要 reconcile / archive / query-archive / lint / maintenance

---

## 二、系统核心理念

### 1. 双模式
- `standard`：原有模式
- `wiki_strict`：增强模式，适合本地小模型

### 2. 文件系统是长期记忆
项目不是靠“聊天历史”长期维持状态，而是靠：
- `memory-bank/`
- `.cc-mini/wiki/`

### 3. 任务必须先压缩再执行
不是直接“改代码”，而是：
- 先有 `current-task.md`
- 再执行
- 再验证
- 再更新文档

### 4. 先计划，后定位，后修改，后验证
整个系统的一个基本原则就是：
- 不允许跳过定位直接 patch
- 不允许跳过验证直接标完成

---

## 三、目录说明

### 1. `memory-bank/`
这是项目的长期规则层和任务控制层。

主要文件包括：
- `game-design-document.md`
- `tech-stack.md`
- `implementation-plan.md`
- `reset-note-v2.md`
- `system-design-v2.md`
- `progress.md`
- `architecture.md`
- `findings.md`
- `decisions.md`
- `current-task.md`
- `schema/*.md`
- `phases/*.md`

#### 它的作用
- 定义规则
- 记录进度
- 记录架构
- 记录决定
- 定义当前任务

### 2. `.cc-mini/wiki/`
这是 Wiki 工作区。

常见内容包括：
- `index.md`
- `log.md`
- `entities/**`
- `taskpacks/**`
- `reports/**`
- `archive/**`

#### 它的作用
- 结构测绘
- 语义消化
- 任务预热
- 运行时日志
- 快照与归档
- 长期维护

---

## 四、五个阶段分别做什么

### Phase 1：模式接入与结构骨架
你已经做的核心包括：
- runtime 规则固化
- mode 支持
- Goal Stack 占位
- 基础骨架接入

### Phase 2：scan / digest / snapshot
核心包括：
- `/scan`
- `/digest`
- `/digest --changed`
- entity 状态升级
- dehydration / Runtime Snapshot
- 最小 drift stop

### Phase 3：TaskPack / EditSpec / prime / plan
核心包括：
- TaskPack
- EditSpec
- Goal Stack 正式对象
- `/prime`
- `/plan`
- Deferred Issue / Micro-Fork

### Phase 4：安全 patch 与局部 debug
核心包括：
- ASTRead
- strict patch
- verify / retry
- traceback cleaning
- Re-anchor
- ask_user fallback

### Phase 5：维护、回收、归档
核心包括：
- reconcile
- archive
- query-archive
- lint / health check
- stale recovery
- 维护引擎

---

## 五、你现在怎么实际使用这个项目

### 使用前提
统一使用以下 Python 解释器：

`/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python`

统一工作目录：

`/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo`

需要导入 `src/core/...` 时统一加：

`PYTHONPATH=src`

---

## 六、推荐的日常工作流

### Step 1：准备 current-task
每次只维护一个：

`memory-bank/current-task.md`

里面写清楚：
- 当前目标
- Allowed Read
- Allowed Modify
- Out of Scope
- Required Tests
- Pass Criteria
- If Tests Fail
- On Success

### Step 2：把 current-task 交给 Claude Code
Claude 只执行当前任务，不进入下一阶段。

### Step 3：Claude 跑测试
必须先过测试，才能更新文档。

### Step 4：Claude 更新文档
成功后更新：
- `progress.md`
- `architecture.md`
- `findings.md`
- `decisions.md`

### Step 5：停止
成功后停止，不自动进入下一个阶段。

---

## 七、推荐的启动方式

### 运行时验证
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python --version
```

```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -c "from core.config import RunMode; print('runtime ok')"
```

### pytest
```bash
cd /Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo && \
PYTHONPATH=src /Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python -m pytest tests/ -v
```

---

## 八、如何做一个真实任务

以一个最小任务为例：

### 示例任务
“让 wiki_strict 模式下的计划输出支持最新 TaskPack 字段”

### 标准流程
1. 写 `memory-bank/current-task.md`
2. 限定只读哪些文件、只改哪些文件
3. 让 Claude 执行
4. 跑 Required Tests
5. 更新 progress / architecture / findings / decisions
6. 停止

---

## 九、什么时候要停下来人工介入

以下情况必须人工介入，不要继续让 Claude 自由推进：

1. 运行时验证失败
2. 同一个子任务修复 2 轮后仍失败
3. 需要跨阶段决策
4. 需要修改 Out of Scope 文件
5. 不确定当前结果是否会破坏 standard 模式
6. 需要改动接口、目录组织、关键数据结构等重大设计

---

## 十、项目当前能力说明（基于你已经完成的状态）

你已经验证通过的结果包括：
- Runtime check：通过
- Module imports：5/5 通过
- Reconcile behavior：通过
- Archive / Query behavior：通过
- Lint behavior：通过
- Maintenance behavior：通过
- pytest regression：277 passed

你新增的 Phase 5 核心模块有：
- `src/core/wiki/reconcile.py`
- `src/core/wiki/archive.py`
- `src/core/wiki/query_archive.py`
- `src/core/wiki/lint.py`
- `src/core/wiki/maintenance.py`

当前归档年龄阈值是：
- snapshot：7 天
- report：14 天
- taskpack：30 天
- entity：90 天

这说明项目已经从“只会生成知识”进入到“会维护、会归档、会恢复”的阶段。

---

## 十一、如何向别人介绍这个项目

你可以用下面这段：

> 这是一个给 cc-mini 增加 `wiki_strict` 模式的增强框架，核心目标是让本地 32K 小模型也能进行中长程、可恢复、可维护的代码任务执行。系统通过 `memory-bank` 和 `.cc-mini/wiki` 把规则、计划、知识、任务、快照和归档都持久化到文件系统里，再通过 `current-task.md` 驱动 Claude Code 做受控执行。项目现在已经具备从 scan/digest、TaskPack/plan，到安全 patch、retry、Re-anchor、reconcile、archive、lint、maintenance 的完整链路。
