---
page_type: source_note
entities:
  - type: string
    required: true
    description: 来源类型 (file/concept/comparison/etc)
  - name: string
    required: true
    description: 来源名称
  - content: string
    required: true
    description: 笔记内容
  - tag: string
    required: false
    description: 标签
  - status: string
    required: true
    description: 处理状态 (raw/digested/graphify)
  - timestamp: string
    required: true
    description: 创建时间 (YYYYMMDD)
  - confidence: float
    required: false
    description: 置信度 (0-1)
frontmatter_schema:
  entities:
    - type: object
      properties:
        - type: string
          required: true
        - name: string
          required: true
        - content: string
          required: true
        - tag: string
        - status: string
          required: true
        - timestamp: string
          required: true
        - confidence: number
---

# {{entities[0].name}} - Source Note

## Overview

{{render_content(entities[0].content)}}

## Metadata

- **Type:** {{entities[0].type}}
- **Status:** {{entities[0].status}}
- **Created:** {{entities[0].timestamp}}
- **Confidence:** {{entities[0].confidence}}

## Tags

{{render_tags(entities[0].tag)}}

## Content Preview

```
{{entities[0].content[:500]}}
```

## Next Steps

{{render_next_steps(entities[0].status)}}
