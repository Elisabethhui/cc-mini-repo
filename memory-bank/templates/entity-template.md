---
page_type: entity
entities:
  - type: string  # 实体类型：file/function/module/class/etc
    required: true
    description: 代码实体类型
  - name: string  # 实体名称
    required: true
    description: 实体唯一标识名
  - path: string  # 实体路径（相对路径）
    required: true
    description: 实体在项目中的位置
  - summary: string  # 实体简要说明
    required: false
    max_length: 500
    description: 实体的功能描述
  - details: string  # 实体详细信息
    required: false
    description: 实体的详细技术说明
  - code_example: string  # 代码示例
    required: false
    description: 相关代码片段
  - dependencies:
    - type: string
      required: false
      description: 依赖的实体名
  - related:
    - type: string
      required: false
      description: 相关的实体名
frontmatter_schema:
  entities:
    - type: object
      properties:
        - type: string
          required: true
        - name: string
          required: true
        - path: string
          required: true
        - summary: string
        - details: string
        - code_example: string
        - dependencies: array[string]
        - related: array[string]
---

# {{entities[0].name}}

## {{entities[0].name}} Overview

{{page_type}} page describing {{entities[0].summary}}.

## {{entities[0].name}} Details

{{entities[0].details}}

## {{entities[0].name}} Code Example

{{entities[0].code_example}}

## {{entities[0].name}} Dependencies

{{render_dependencies(entities[0].dependencies)}}

## {{entities[0].name}} Related Entities

{{render_related(entities[0].related)}}
