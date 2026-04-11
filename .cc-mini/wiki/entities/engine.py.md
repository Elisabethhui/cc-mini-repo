# Entity: src/core/engine.py

## Classes
- **class AbortedError**: Raised when the current turn is aborted by the user (Esc / Ctrl+C).
  - Methods: 
- **class Engine**: 无文档说明
  - Methods: __init__, get_messages, set_messages, get_system_prompt, set_session_store, set_tools, get_model, set_current_skill_name, set_compact_service, _runtime_checkpoint_and_stop, set_model, _persist, messages, messages, system_prompt, system_prompt, last_assistant_text, abort, cancel_turn, submit, _execute_tool

## Functions
- **def _normalize_content_block()**: Convert SDK content blocks into plain API dictionaries.
- **def _normalize_json_value()**: 无文档说明
- **def _normalize_message_content()**: 无文档说明
- **def _block_type()**: 无文档说明
- **def _block_name()**: 无文档说明
- **def _block_id()**: 无文档说明
- **def _block_input()**: 无文档说明