---
source_hash: d47582bfa79290de
status: partially_digested
updated_at: 1776054844.6630266
---

# 文献大纲: memory-bank/schema/goal_policy.md

- Goal Policy
  - 文档目的
  - 一、适用范围
  - 二、不适用范围
  - 三、核心定义
    - 1. Goal Stack
    - 2. Drift Detector
    - 3. Re-anchor Loop
    - 4. Deferred Issue Log
    - 5. Micro-Fork Note
  - 四、Goal Stack 的正式规则
    - 1. Goal Stack 是正式对象
    - 2. Goal Stack 最小字段不可缺失
    - 3. Goal Stack 必须可被引用
    - 4. Goal Stack 必须在关键节点可见
  - 五、Drift Detector 的正式规则
    - 最少应检测 5 类偏航
  - 六、Re-anchor Loop 的正式规则
    - 1. 检测到偏航时，不能只提示，必须回正
    - 2. Re-anchor Loop 的固定问题
    - 3. 触发场景
  - 七、Deferred Issue Log 的正式规则
    - 1. 延后问题必须外部化
    - 2. 进入 Deferred Issue 后，默认当前不处理
    - 3. Deferred Issue 至少应包含
    - 4. 典型适用场景
  - 八、Micro-Fork Note 的正式规则
    - 1. 为什么需要 Micro-Fork
    - 2. Micro-Fork 是轻量分叉，不是重会话并行
    - 3. 最小字段
    - 4. 禁止事项
  - 九、与 TaskPack / EditSpec 的关系
    - 与 TaskPack 的关系
    - 与 EditSpec 的关系
  - 十、与 Context Safeguard 的关系
  - 十一、执行纪律
    - 1. 任何任务都必须具备三层以上目标
    - 2. 当前动作失败，不等于整个任务失败
    - 3. 发现后续阶段问题时，优先写入 deferred issue
    - 4. 重复失败必须熔断
  - 十二、禁止事项
  - 十三、分阶段落地建议
    - Phase 0
    - Phase 1
    - Phase 2
    - Phase 3
    - Phase 4
  - 十四、最终原则