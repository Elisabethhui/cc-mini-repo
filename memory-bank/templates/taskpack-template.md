---
page_type: taskpack
taskpack_name: string
  required: true
  description: 任务包名称
status: string
  required: true
  enum: [pending, planning, running, completed, archived]
  description: 任务包状态
progress: float
  required: false
  description: 完成进度 (0-1)
tasks:
  - task_name: string
    required: true
    description: 任务名称
  - status: string
    required: true
    enum: [pending, in_progress, completed, failed]
    description: 任务状态
  - priority: string
    required: true
    enum: [high, medium, low]
    description: 任务优先级
  - target_files:
    - type: string
      required: false
      description: 目标文件相对路径
  - target_actions:
    - type: string
      required: false
      description: 目标动作 (create/edit/move/rename)
  - dependencies:
    - type: string
      required: false
      description: 依赖的任务名
  - estimated_steps: int
    required: false
    description: 预估执行步骤数
operations:
  - operation_name: string
    required: true
    description: 操作名称
  - operation_type: string
    required: true
    enum: [ingest, digest, lint, archive]
    description: 操作类型
  - target_pattern: string
    required: false
    description: 目标匹配模式
  - operation_template: string
    required: false
    description: 操作模板文件路径
  - expected_output: string
    required: false
    description: 预期输出描述
frontmatter_schema:
  page_type:
    - type: string
      required: true
  taskpack_name:
    - type: string
      required: true
  status:
    - type: string
      required: true
      enum: [pending, planning, running, completed, archived]
  tasks:
    - type: array
      items:
        - task_name: string
          required: true
        - status: string
          required: true
        - priority: string
          required: true
  operations:
    - type: array
      items:
        - operation_name: string
          required: true
        - operation_type: string
          required: true
---

# {{taskpack_name}}

## Overview

{{taskpack_name}} contains tasks for {{{target_pattern}}} with {{{operation_type}}} operations.

## Status

- **Overall Status:** {{{status}}}
- **Progress:** {{{progress}}}

## Tasks

### High Priority Tasks

| Name | Status | Priority | Target | Operation |
|------|--------|----------|--------|-----------|
| {{task.task_name}} | {{task.status}} | {{task.priority}} | {{task.target_files[0]}} | {{task.target_actions[0]}} |

## Operations

### Operations List

| Name | Type | Target Pattern | Template |
|------|------|----------------|----------|
| {{op.operation_name}} | {{op.operation_type}} | {{op.target_pattern}} | {{op.operation_template}} |

## Dependencies

{{render_dependencies(tasks.dependencies)}}

## Execution Plan

1. {{{step.description}}}
2. {{{step.description}}}
3. {{{step.description}}}

## Notes

{{taskpack_notes}}
