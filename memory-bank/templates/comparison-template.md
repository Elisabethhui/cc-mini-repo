---
page_type: comparison
entities:
  - type: string
    required: true
    description: 参与对比的一方
  - name: string
    required: true
    description: 第一方名称
  - details: string
    required: true
    description: 第一方详细说明
  - second: string
    required: true
    description: 参与对比的双方
  - second_name: string
    required: true
    description: 第二方名称
  - second_details: string
    required: true
    description: 第二方详细说明
  - conclusion: string
    required: false
    description: 对比结论
frontmatter_schema:
  entities:
    - type: object
      properties:
        - type: string
          required: true
        - name: string
          required: true
        - details: string
          required: true
        - second: string
          required: true
        - second_name: string
          required: true
        - second_details: string
          required: true
        - conclusion: string
---

# {{entities[0].name}} vs {{entities[1].name}}

## Overview

{{render_conclusion(entities.conclusion)}}

## {{entities[0].name}} Details

{{entities[0].details}}

## {{entities[1].name}} Details

{{entities[1].details}}

## Comparison Table

| Aspect | {{entities[0].name}} | {{entities[1].name}} | Winner |
|--------|---------------------|---------------------|--------|
| Aspect 1 | Description | Description | Side |
| Aspect 2 | Description | Description | Side |

## Conclusion

{{render_conclusion(entities.conclusion)}}
