---
source_hash: 0b5ef8bf91dfd8e1
status: partially_digested
updated_at: 1776054844.6630266
---

# Entity: src/core/dehydration.py

## Classes
- **class DehydrationResult**: 无文档说明
  - Methods: 

## Functions
- **def maybe_dehydrate_messages()**: 对历史消息做原地脱水。
- **def _dehydrate_tool_result_block()**: 这里无法总是拿到 tool name，所以尽量从 content 里提炼。
- **def _cheap_summary()**: 低成本摘要，不再调模型。