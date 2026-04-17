# Phase 6-A 测试留痕策略（硬规则）

## 1. 每个 Module 必须产出两类测试资产

### A. 入库测试脚本
必须放到固定目录：
```text
scripts/validation/phase6/
  module-1/validate_target_identity.sh
  module-2/validate_init_build.sh
  module-3/validate_post_edit_guard.sh
  final/validate_phase6a_end_to_end.sh
  final/archive_phase6a_report.sh
```

### B. 出库运行日志
每次运行测试时，必须写入：
```text
validation-runs/
  <timestamp>-phase6-module-1/
  <timestamp>-phase6-module-2/
  <timestamp>-phase6-module-3/
  <timestamp>-phase6-final/
```

日志最少包含：
- `env.snapshot`
- `command.log`
- `summary.txt`

最终验证必须额外生成：
- `phase6a-validation-report.md`
- `archive/README.md`

## 2. 测试必须验证“最小功能完整性”
禁止只测：
- import 成功
- 文件存在
- 命令存在

必须测：
- 行为正确
- 关键失败路径可控
- 最小闭环成立
- 输出语义符合预期

## 3. 自动文档归档
Final Validation 结束后，必须自动：
1. 生成 `phase6a-validation-report.md`
2. 归档到：
   `validation-runs/<timestamp>-phase6-final/archive/`
3. 生成 `archive/README.md`
4. 更新项目 README 中的：
   - Phase 6-A 进度
   - 验证状态
   - 最近一次验证时间
