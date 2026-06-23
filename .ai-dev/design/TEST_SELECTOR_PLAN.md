# Test Selector Plan

## Purpose

Plan the product logic for choosing the smallest useful tests after code changes.

## Goal

Use changed files, CodeGraph affected tests, and manual mapping rules to recommend targeted verification.

## Inputs

- changed files
- CodeIntel provider freshness
- CodeGraph affected tests
- `.ai-dev/TESTING.md`
- known test files

## Provider Order

1. CodeGraph affected tests when map is fresh.
2. Manual mapping from `.ai-dev/TESTING.md`.
3. Nearby tests by filename similarity.
4. Smoke command.
5. Broad suite as last resort.

## Proposed Module

```text
src/core/test_selector.py
```

## Acceptance Criteria

- recommends test commands for changed files
- works without CodeGraph
- explains confidence and fallback
- avoids running tests automatically
- has tests

## Risks

- false confidence from empty affected tests
- environment-specific test failures
- over-selecting broad tests
