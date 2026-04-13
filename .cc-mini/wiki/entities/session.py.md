---
source_hash: 1f7571aa444973b6
status: partially_digested
updated_at: 1776054844.6630266
---

# Entity: src/core/session.py

## Classes
- **class SessionMeta**: 无文档说明
  - Methods: 
- **class SessionStore**: Manages JSONL persistence for a single session.
  - Methods: __init__, append_message, _save_meta, load_messages, list_sessions, load_session

## Functions
- **def _sanitize_cwd()**: Convert an absolute path to a safe directory name.
- **def _now_iso()**: 无文档说明
- **def _serialize_content()**: Recursively convert Anthropic SDK Pydantic objects to plain dicts.
- **def _serialize_message()**: Return a JSON-safe copy of a message dict.
- **def _extract_text()**: Best-effort plain text extraction from message content.
- **def _generate_title()**: Create a short title from the first user message.