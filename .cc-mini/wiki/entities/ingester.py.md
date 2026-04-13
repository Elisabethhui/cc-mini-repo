---
source_hash: e3e0dfac91d2811f
status: partially_digested
updated_at: 1776054844.6630266
---

# Entity: src/core/knowledge/ingester.py

## Classes
- **class DigestStatus**: Entity 消化状态枚举
  - Methods: 
- **class DriftTracker**: 最小漂移跟踪器 (Phase 2)
  - Methods: __init__, _load, _save, should_stop, record_failure, record_success, _write_deferred_issue
- **class WikiIngester**: 大一统知识基座引擎：将代码和文本降维映射为 Markdown 实体图谱。
  - Methods: __init__, _compute_hash, _parse_entity_frontmatter, _build_frontmatter, _update_entity_status, ingest_all, ingest_file, _parse_python_ast, _parse_markdown, _parse_with_tree_sitter, _build_index

## Functions