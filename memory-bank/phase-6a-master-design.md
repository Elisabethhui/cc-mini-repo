# Phase 6-A 正式总设计

## 1. 阶段定位
当前项目已完成 Phase 1–5，已具备：
- 分析链
- 计划链
- 修改链
- 保护链
- 维护链

Phase 6-A 的任务不是重做底层能力，而是把系统提升到“**日常可用**”的产品化最小层。

## 2. Phase 6-A 的目标
让当前系统从：
“能力已经存在，但使用上容易踩坑”
提升到：
“有正式入口、目标唯一、完成状态清楚、测试可复用、验证可留痕”。

### 只做 4 件事
1. **Target Identity & Prime Hardening**
2. **/init_build**
3. **post_edit_guard + completion_state**
4. **最终端到端最小模拟事件验证 + 自动文档归档**

## 3. 明确不做的事情
Phase 6-A 明确不做：
- Operational Memory 完整实现
- Token Budget 2.0 完整实现
- Rollback & Recovery 完整实现
- Profiles / Views / Handoffs 完整实现
- 重型多 agent orchestration
- UI 系统

## 4. 成功标准（用户视角）
只有下面 5 条都满足，Phase 6-A 才算成功：
1. `/prime` 不再被路径字符串和同名目标轻易搞崩
2. 用户进入仓库后，可以通过 `/init_build` 自动建立全库基座
3. patch 成功后，系统不会直接宣告完成，而是经过 impact analysis 和 completion state 判定
4. 所有模块都有永久测试脚本和运行留痕
5. 安装完成后，可以通过最小模拟事件完成一次端到端验证

## 5. 三个模块
### Module 1：Target Identity & Prime Hardening
- 解决路径 target 报错
- 建立目标身份
- 处理重名文件 / 重名 symbol / 多定义

### Module 2：`/init_build`
- 一键建立 Wiki 基座
- 全仓 raw_ast
- staged digest
- build state 输出

### Module 3：`post_edit_guard + completion_state`
- patch 后自动 impact analysis
- stale / pending 标记
- `IMPACT_PENDING -> IMPACT_CLEAN -> COMPLETE/BLOCKED`

## 6. 测试与推进门禁
每个模块都必须：
1. 实现代码
2. `.sh` 测试脚本入库
3. 测试脚本真实运行
4. `summary.txt` 明确通过
5. 才允许推进到下一个模块

## 7. 最终验证
在三个模块都完成后，必须执行一次：
**最小模拟事件端到端验证**

建议模拟链：
1. 进入目标仓库
2. `/init_build`
3. `/prime` 一个真实目标
4. `/plan` 一个最小修改任务
5. 做一个最小 patch
6. 自动进入 post_edit_guard
7. 输出最终 completion_state
8. 自动生成验证报告并归档
