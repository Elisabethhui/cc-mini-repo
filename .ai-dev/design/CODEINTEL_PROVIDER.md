# CodeIntel Provider Design

## Goal

Avoid binding cc-mini to one code intelligence tool.

## Provider Interface

- available
- status
- sync
- files
- query
- callers
- callees
- impact
- affected_tests
- snippet

## Provider Priority

1. CodeGraph
2. Codebase-Memory-MCP
3. rg fallback
4. manual file read fallback
