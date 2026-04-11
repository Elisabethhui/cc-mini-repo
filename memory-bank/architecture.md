# Architecture

## 当前定位
本文件记录项目在“回退到 Step 3 + 升级到 v2.0”后的新架构口径。

## 仍然保留的旧资产
- game-design-document.md
- tech-stack.md
- implementation-plan.md
- 旧 schema 基础规则文件

## v2.0 新增架构元素
### Context Safeguard
负责：
- token 风险监控
- OOM 预警
- 脱水与 snapshot
- 会话恢复

### Goal Anchoring & Drift Recovery
负责：
- Goal Stack
- Drift Detector
- Re-anchor Loop
- Deferred Issue Log
- Micro-Fork Note

## 新建议文件
- system-design-v2.md
- phase-0-4-compact-index.md
- schema/context_safeguard_policy.md
- schema/goal_policy.md
- schema/phase_boundary_policy.md

## 当前架构结论
1. 旧 Step 4 不再作为执行依据
2. 后续阶段以 v2.0 体系为准
3. 应从 Phase 0 重新开始，而不是继续旧 Step 4
