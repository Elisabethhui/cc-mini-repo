# Phase 6-A 正式总设计 v2.1

## 1. 阶段定位
Phase 6-A 是在 Phase 1–5 已完成的前提下，补齐最小产品化层：
1. Target Identity & Prime Hardening
2. `/init_build`
3. `post_edit_guard + completion_state`
4. Final Validation

## 2. 新增硬规则：模块完成必须伴随文档落盘
每个 Module 完成后，必须同步更新：
1. `memory-bank/findings.md`
2. `memory-bank/progress.md`
3. `README` 中的 Phase 6-A 状态段落

若以上三处文档未更新，则：
- 当前 Module 不能标记为 pass
- 不能进入下一个 Module

## 3. 用户视角成功标准
Phase 6-A 成功，至少要让用户得到这 5 个变化：
1. `/prime` 不再被路径或歧义 target 轻易搞崩
2. 用户进入仓库后可通过 `/init_build` 自动建立基座
3. patch 成功后系统不会直接宣告完成，而是进入 impact analysis
4. 每个模块的测试和验证都能留痕复跑
5. 最终端到端验证后，报告、归档、README 都自动更新
