---
source_hash: 587908d79d241a96
status: partially_digested
updated_at: 1776054844.6630266
---

# Entity: src/core/knowledge/dehydrator.py

## Classes
- **class RuntimeSnapshot**: Runtime Snapshot 数据结构 - 包含执行状态关键信息
  - Methods: 
- **class RuntimeSnapshotWriter**: Runtime Snapshot 写入器 - 将执行状态写入 wiki/log.md 或 checkpoint
  - Methods: __init__, _now_iso, write_to_wiki_log, write_snapshot_file, create_and_save
- **class MinimalDehydrator**: 最小 dehydrator - 在 token risk 临界时触发
  - Methods: __init__, check_and_dehydrate

## Functions