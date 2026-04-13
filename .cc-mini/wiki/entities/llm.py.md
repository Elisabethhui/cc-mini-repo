---
source_hash: 3aa982099a7ec0fb
status: raw_ast
updated_at: 1776054844.6630266
---

# Entity: src/core/llm.py

## Classes
- **class LLMUsage**: 无文档说明
  - Methods: 
- **class LLMMessage**: 无文档说明
  - Methods: 
- **class LLMClient**: 无文档说明
  - Methods: __init__, create_message, stream_messages, is_authentication_error, is_retryable_error, is_api_error, error_message, _anthropic_create_message, _openai_create_message
- **class _AnthropicStream**: 无文档说明
  - Methods: __init__, __enter__, __exit__, close, get_final_message
- **class _OpenAIStream**: 无文档说明
  - Methods: __init__, __enter__, __exit__, close, _iter_text, get_final_message

## Functions
- **def validate_provider()**: 无文档说明
- **def default_model_for_provider()**: 无文档说明
- **def default_companion_model()**: 无文档说明
- **def default_max_tokens_for_provider()**: 无文档说明
- **def supports_reasoning_effort()**: 无文档说明
- **def _normalize_anthropic_content()**: 无文档说明
- **def _normalize_anthropic_block()**: 无文档说明
- **def _normalize_openai_message()**: 无文档说明
- **def _extract_openai_text()**: 无文档说明
- **def _usage_from_anthropic()**: 无文档说明
- **def _usage_from_openai()**: 无文档说明
- **def _build_openai_request()**: 无文档说明
- **def _to_openai_messages()**: 无文档说明
- **def _user_content_blocks_to_openai()**: 无文档说明
- **def _tool_schema_to_openai()**: 无文档说明
- **def _tool_result_to_text()**: 无文档说明
- **def _value()**: 无文档说明