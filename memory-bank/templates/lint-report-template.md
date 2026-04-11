---
page_type: lint_report
report_name: string
  required: true
  description: 报告名称
report_type: string
  required: true
  enum: [code, doc, config]
  description: 报告类型
severity_filter:
  - string
    required: false
    description: 严重程度过滤
generated_at: string
  required: true
  description: 报告生成时间 (YYYYMMDD)
total_issues: int
  required: true
  description: 问题总数
issues:
  - issue_id: string
    required: true
    description: 问题 ID
  - issue_type: string
    required: true
    enum: [error, warning, info]
    description: 问题类型
  - severity: string
    required: true
    enum: [critical, high, medium, low]
    description: 严重程度
  - file: string
    required: true
    description: 问题文件
  - line: int
    required: true
    description: 问题行号
  - column: int
    required: false
    description: 问题列号
  - message: string
    required: true
    description: 问题描述
  - rule_id: string
    required: true
    description: 规则 ID
  - fix_available: bool
    required: false
    description: 是否可修复
  - fix_code: string
    required: false
    description: 修复代码
remediation:
  - issue_pattern: string
    required: true
    description: 问题模式匹配
  - recommended_action: string
    required: true
    description: 推荐修复动作
  - expected_impact: string
    required: false
    description: 预期影响
frontmatter_schema:
  page_type:
    - type: string
      required: true
  report_name:
    - type: string
      required: true
  report_type:
    - type: string
      required: true
  generated_at:
    - type: string
      required: true
  issues:
    - type: array
      items:
        - issue_id: string
          required: true
        - issue_type: string
          required: true
        - severity: string
          required: true
  remediation:
    - type: array
      items:
        - issue_pattern: string
          required: true
        - recommended_action: string
          required: true
---

# {{report_name}} - {{report_type}} Report

## Overview

{{description_of_report}}

## Report Information

- **Type:** {{{report_type}}}
- **Generated:** {{{generated_at}}}
- **Total Issues:** {{{total_issues}}}

## Issues Summary

| Severity | Count | Percentage |
|----------|-------|------------|
| Critical | {{{critical_count}}} | {{{critical_pct}}} |
| High | {{{high_count}}} | {{{high_pct}}} |
| Medium | {{{medium_count}}} | {{{medium_pct}}} |
| Low | {{{low_count}}} | {{{low_pct}}} |

## Issues

### Critical Issues

| ID | Type | File | Line | Rule | Message |
|----|------|------|------|------|---------|
| {{{critical_issue.id}}} | {{{critical_issue.type}}} | {{{critical_issue.file}}} | {{{critical_issue.line}}} | {{{critical_issue.rule}}} | {{{critical_issue.message}}} |

### High Priority Issues

| ID | Type | File | Line | Rule | Message |
|----|------|------|------|------|---------|
| {{{high_issue.id}}} | {{{high_issue.type}}} | {{{high_issue.file}}} | {{{high_issue.line}}} | {{{high_issue.rule}}} | {{{high_issue.message}}} |

### Medium Priority Issues

| ID | Type | File | Line | Rule | Message |
|----|------|------|------|------|---------|
| {{{medium_issue.id}}} | {{{medium_issue.type}}} | {{{medium_issue.file}}} | {{{medium_issue.line}}} | {{{medium_issue.rule}}} | {{{medium_issue.message}}} |

## Remediation Plan

### Pattern-Based Fixes

{{{render_remediation_plans}}}

## Recommendations

{{render_recommendations}}
