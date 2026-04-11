# Entity: src/core/memory.py

## Classes


## Functions
- **def ensure_memory_dir()**: Create memory_dir and memory_dir/logs if they don't exist.
- **def daily_log_path()**: Return memory_dir/logs/YYYY/MM/YYYY-MM-DD.md, creating parents.
- **def append_to_daily_log()**: Append a timestamped entry to today's daily log.
- **def load_memory_index()**: Read MEMORY.md, truncate to MAX_MEMORY_INDEX_CHARS. Returns '' if missing.
- **def _lock_path()**: 无文档说明
- **def read_last_consolidated_at()**: Return epoch seconds of last consolidation (0 if never).
- **def try_acquire_lock()**: Try to acquire consolidation lock. Returns True on success.
- **def release_lock()**: Stamp lock mtime to now (marks consolidation time) but keep the file.
- **def record_consolidation()**: Record that a consolidation just finished (for manual /dream too).
- **def count_sessions_since()**: Count session files with mtime > since_ts.
- **def should_auto_dream()**: Check all gates: time ≥ min_hours AND sessions ≥ min_sessions.
- **def extract_memory_tags()**: Extract all <memory>...</memory> tag contents from text.
- **def build_memory_system_section()**: Return the memory instructions + MEMORY.md content for the system prompt.
- **def build_dream_prompt()**: Build the 4-phase consolidation prompt for the dream agent.
- **def save_session()**: Serialize messages to JSONL and update the last-session symlink.
- **def load_session()**: Load messages from JSONL. If no ID, follow the last-session symlink.
- **def serialize_message()**: Handle both Anthropic SDK objects (.model_dump()) and plain dicts.