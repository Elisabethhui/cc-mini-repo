# Entity: src/core/knowledge/watcher.py

## Classes
- **class WikiDebounceWatcher**: 带有防抖(Debounce)功能的监听器。
  - Methods: __init__, _handle_change, _debounce, on_modified, on_created

## Functions
- **def start_wiki_watcher()**: 在后台线程启动监听