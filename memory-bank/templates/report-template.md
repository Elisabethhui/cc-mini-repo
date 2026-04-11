---
page_type: report
entities:
  - type: string
    required: true
    description: 报告主体类型
  - title: string
    required: true
    description: 报告标题
  - summary: string
    required: true
    description: 报告摘要
  - content: string
    required: false
    description: 报告详细内容
  - findings:
    - type: object
      properties:
        - type: string
          required: false
          description: 发现项名称
        - severity: string
          required: true
          description: 严重程度 (critical/high/medium/low)
        - description: string
          required: true
          description: 发现项描述
        - recommendation: string
          required: false
          description: 修复建议
  - conclusion: string
    required: false
    description: 报告结论
frontmatter_schema:
  entities:
    - type: object
      properties:
        - type: string
          required: true
        - title: string
          required: true
        - summary: string
          required: true
        - content: string
        - findings: array[object]
        - conclusion: string
---

# {{entities[0].title}}

## Overview

{{entities[0].summary}}

## Report Content

{{render_content(entities[0].content)}}

## Findings

### Critical Issues

{{render_findings(entities.findings[0], severity='critical')}}

### High Priority Issues

{{render_findings(entities.findings[0], severity='high')}}

### Medium Priority Issues

{{render_findings(entities.findings[0], severity='medium')}}

### Low Priority Issues

{{render_findings(entities.findings[0], severity='low')}}

## Conclusion

{{render_conclusion(entities[0].conclusion)}}

## Recommendation

{{render_recommendation(entities[0].recommendation)}}
