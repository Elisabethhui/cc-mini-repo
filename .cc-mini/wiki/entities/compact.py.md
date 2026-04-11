# Entity: src/core/compact.py

## Classes
- **class CompactService**: Compress conversation context via API summarisation.
  - Methods: __init__, compact, compact_messages

## Functions
- **def _context_window_for_model()**: 无文档说明
- **def _auto_compact_threshold()**: context_window - max_output_reserve - buffer (matches official).
- **def _text_of()**: Extract plain text from message content (str, list of blocks, etc.).
- **def estimate_tokens()**: Rough token estimate: total chars / CHARS_PER_TOKEN.
- **def should_compact()**: Return True when the conversation should be auto-compacted.
- **def should_runtime_compact()**: Stricter runtime compact trigger for smaller local models.
- **def _split_recent()**: Split *messages* into (history_to_summarise, recent_to_keep).
- **def _strip_media()**: Return a copy of *messages* with images / documents replaced by text markers.
- **def _fix_alternation()**: Ensure strict user/assistant alternation required by the API.