# Phase 6-A 模块完成后的强制文档更新规则

## 规则
每个 Module 完成后，Claude 必须自动执行以下三件事：

### 1. 更新 `memory-bank/findings.md`
记录：
- 本模块结论（pass / conditional pass / blocked）
- 已通过项
- 未通过项
- deferred validation
- 风险说明

### 2. 更新 `memory-bank/progress.md`
记录：
- 当前模块状态
- 下一模块是否可启动
- 哪些验证已完成
- 哪些验证暂缓

### 3. 更新 `README`
至少更新：
- Phase 6-A 当前进度
- 当前模块状态
- 最近一次验证时间
- 是否存在 deferred validation

## 门禁
若这三步未完成，则本模块不允许视为完成。
