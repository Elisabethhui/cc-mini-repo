---
source_hash: e7195446439d56e7
status: partially_digested
updated_at: 1776054844.6630266
---

# Entity: tests/test_engine.py

## Classes
- **class EchoTool**: 无文档说明
  - Methods: execute

## Functions
- **def _make_engine()**: 无文档说明
- **def _make_text_response()**: Simulate an API response with just text (no tool calls).
- **def _make_tool_then_text_response()**: Simulate: first response has tool_use, second response has text.
- **def test_engine_returns_text_events()**: 无文档说明
- **def test_engine_executes_tool_and_loops()**: 无文档说明
- **def test_engine_denied_tool_returns_error_result()**: 无文档说明
- **def test_engine_unknown_tool_returns_error()**: 无文档说明
- **def test_engine_uses_model_specific_default_max_tokens()**: 无文档说明
- **def test_engine_normalizes_assistant_tool_use_blocks_before_retrying()**: 无文档说明
- **def test_engine_normalizes_tool_result_blocks_before_follow_up_request()**: 无文档说明