# Phase 6-A 执行索引（必须按顺序推进）

## 规则
- **当前模块测试没通过，不得进入下一个模块**
- 不允许跳步
- 不允许把最终验证提前到中间执行

## Step 6A.1 — Module 1
执行文件：
- `module-1-target-identity/current-task.md`
- `module-1-target-identity/claude-prompt.txt`

测试脚本：
- `scripts/validation/phase6/module-1/validate_target_identity.sh`

推进条件：
- `summary.txt` 明确通过
- README 已更新本模块状态

## Step 6A.2 — Module 2
执行文件：
- `module-2-init-build/current-task.md`
- `module-2-init-build/claude-prompt.txt`

测试脚本：
- `scripts/validation/phase6/module-2/validate_init_build.sh`

推进条件：
- `summary.txt` 明确通过
- README 已更新本模块状态

## Step 6A.3 — Module 3
执行文件：
- `module-3-post-edit-guard/current-task.md`
- `module-3-post-edit-guard/claude-prompt.txt`

测试脚本：
- `scripts/validation/phase6/module-3/validate_post_edit_guard.sh`

推进条件：
- `summary.txt` 明确通过
- README 已更新本模块状态

## Step 6A.4 — Final Validation
执行文件：
- `final-validation/current-task.md`
- `final-validation/claude-prompt.txt`

测试脚本：
- `scripts/validation/phase6/final/validate_phase6a_end_to_end.sh`
- `scripts/validation/phase6/final/archive_phase6a_report.sh`

完成条件：
- `phase6a-validation-report.md` 已生成
- `summary.txt` 明确给出：
  - 已通过项
  - 未通过项
  - 阻塞项
  - 是否达到 Phase 6-A 完成标准
- README 最终更新完成
