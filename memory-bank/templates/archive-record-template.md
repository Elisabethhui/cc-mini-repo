---
page_type: archive_record
record_name: string
  required: true
  description: 归档记录名称
archive_date: string
  required: true
  description: 归档日期 (YYYYMMDD)
reason: string
  required: true
  description: 归档原因
status: string
  required: true
  enum: [pending, approved, archived]
  description: 归档状态
original_path: string
  required: true
  description: 原始文件路径
original_page_type: string
  required: true
  enum: [entity, concept, comparison, report, source_note, taskpack]
  description: 原始页面类型
retention_period: string
  required: false
  description: 保留期限
linked_pages:
  - page_name: string
    required: true
    description: 关联页面名称
  - relationship_type: string
    required: true
    enum: [dependency, reference, supersede]
    description: 关联类型
replacement_path: string
  required: false
  description: 替换文件路径
notes: string
  required: false
  max_length: 1000
  description: 归档备注
frontmatter_schema:
  page_type:
    - type: string
      required: true
  record_name:
    - type: string
      required: true
  archive_date:
    - type: string
      required: true
  reason:
    - type: string
      required: true
  status:
    - type: string
      required: true
      enum: [pending, approved, archived]
---

# {{record_name}} - Archive Record

## Overview

{{reason}} for archiving {{{original_page_type}}} {{original_path}}.

## Archive Information

- **Date:** {{archive_date}}
- **Status:** {{{status}}}
- **Original Type:** {{original_page_type}}
- **Original Path:** {{{original_path}}}

## Linked Pages

| Page Name | Relationship |
|-----------|--------------|
| {{link.page_name}} | {{link.relationship_type}} |

## Replacement

{{replacement_path}} will replace the original file if status is `approved`.

## Notes

{{notes}}

## Next Steps

{{{status == 'pending' ? 'Awaiting approval.' : status == 'approved' ? 'Schedule archiving.' : 'Already archived.'}}}
