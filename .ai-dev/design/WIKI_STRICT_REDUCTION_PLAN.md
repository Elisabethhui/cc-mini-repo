# Wiki Strict Reduction Plan

## Purpose

Decide how existing wiki_strict behavior should coexist with CodeIntel and context-bounded workflow.

## Goal

Reduce heavy wiki/document generation while preserving the useful low-context safety ideas.

## Keep

- task boundaries
- patch verification
- target identity checks
- archive/reconcile ideas if still useful
- AST/snippet reading where CodeGraph is unavailable

## Reconsider

- large generated wiki documents
- long system prompt sections
- always-on lifecycle work
- duplicated maps that CodeGraph can answer

## Replace With

- surface-search
- code-intel
- context-pack
- map-sync
- test-gate
- fresh-review

## Open Questions

- Which wiki_strict files are still product-critical?
- Which can become optional workflow helpers?
- Which are obsolete after CodeIntel provider exists?
