---
source_hash: 38876db2acc77fdb
status: raw_ast
updated_at: 1776054844.6630266
---

# Entity: tests/conftest.py

## Classes
- **class DummyUsage**: 无文档说明
  - Methods: __init__
- **class DummyTextBlock**: 无文档说明
  - Methods: __init__
- **class DummyToolUseBlock**: 无文档说明
  - Methods: __init__
- **class DummyFinalMessage**: 无文档说明
  - Methods: __init__
- **class DummyStream**: 无文档说明
  - Methods: __init__, __enter__, __exit__, get_final_message, close
- **class DummyClient**: 无文档说明
  - Methods: __init__, stream_messages, create_message, is_authentication_error, is_retryable_error, is_api_error, error_message
- **class DummyPermissionChecker**: 无文档说明
  - Methods: __init__, check
- **class DummyReadOnlyTool**: 无文档说明
  - Methods: to_api_schema, is_read_only, get_activity_description, execute
- **class DummyWriteTool**: 无文档说明
  - Methods: to_api_schema, is_read_only, get_activity_description, execute
- **class DummySessionStore**: 无文档说明
  - Methods: __init__, append_message
- **class DummyCostTracker**: 无文档说明
  - Methods: __init__, add_usage, add_lines_changed

## Functions
- **def tmp_repo()**: 无文档说明