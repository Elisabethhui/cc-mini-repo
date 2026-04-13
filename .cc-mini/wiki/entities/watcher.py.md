---
source_hash: 7db80399450a5e60
status: partially_digested
updated_at: 1776054844.6630266
---

# Entity: src/core/knowledge/watcher.py

## Classes
- **class ChangedFileTracker**: 跟踪变更文件列表，用于 /digest --changed
  - Methods: __init__, _load, _save, add, get_and_clear, peek
- **class WikiDebounceWatcher**: 带有防抖(Debounce)功能的监听器。
  - Methods: __init__, _handle_change, _debounce, on_modified, on_created

## Functions
- **def start_wiki_watcher()**: 在后台线程启动监听
- **def get_changed_tracker()**: 获取变更文件跟踪器实例