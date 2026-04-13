---
source_hash: 0faf05ae7602faf5
status: partially_digested
updated_at: 1776054844.6630266
---

# 文献大纲: memory-bank/schema/context_safeguard_policy.md

- Context Safeguard Policy
  - 文档目的
  - 一、适用范围
  - 二、不适用范围
  - 三、核心定义
    - 1. Token Risk Monitor
    - 2. Dehydration
    - 3. Context Snapshot
    - 4. Resume
  - 四、风险等级（正式规则）
  - 五、不同等级必须做什么
    - 1. safe
    - 2. watch
    - 3. warning
    - 4. critical
    - 5. emergency
  - 六、触发点规则
  - 七、Snapshot 最小内容要求
    - A. Runtime Snapshot（最小字段）
    - B. Markdown Snapshot（最小结构）
  - 八、必须保留的信息
    - 1. Goal 信息
    - 2. Localization 信息
    - 3. Change State
    - 4. Failure Memory
    - 5. Next Action
  - 九、必须丢弃或压缩的内容
  - 十、持久化要求
    - 最低要求
    - 推荐要求
  - 十一、恢复规则
  - 十二、与其他系统的关系
    - 与 TaskPack 的关系
    - 与 Goal Stack 的关系
    - 与 Debug/Retry 的关系
  - 十三、禁止事项
  - 十四、分阶段落地建议
    - Phase 0
    - Phase 1
    - Phase 2
    - Phase 3
    - Phase 4
  - 十五、最终原则