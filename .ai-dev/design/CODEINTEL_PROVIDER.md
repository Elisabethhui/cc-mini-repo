# CodeIntel Provider Design

## Purpose

Design a provider abstraction for low-token code intelligence.

The goal is to avoid hard-binding cc-mini to one tool while still using CodeGraph first.

## Problem

Small-context models cannot afford repeated full-file exploration.

They need local tools to answer:

- where is this symbol?
- who calls it?
- what does it call?
- what is affected by changing it?
- which tests are affected?
- is the map fresh?

## Provider Interface

Proposed provider methods:

- `available() -> bool`
- `status() -> CodeIntelStatus`
- `sync() -> SyncResult`
- `files(query=None) -> FileListResult`
- `query(keyword) -> SymbolSearchResult`
- `callers(symbol) -> RelationshipResult`
- `callees(symbol) -> RelationshipResult`
- `impact(symbol, depth=2) -> ImpactResult`
- `affected_tests(files) -> AffectedTestsResult`
- `snippet(target) -> SnippetResult`

## Provider Priority

Use providers in this order:

1. CodeGraph provider
2. Codebase-Memory-MCP provider
3. rg fallback provider
4. manual file read fallback

First implementation should support:

- CodeGraph provider
- rg fallback provider

## CodeGraph Provider

Use subprocess calls initially.

Commands:

- `codegraph status`
- `codegraph sync`
- `codegraph files`
- `codegraph query "<keyword>"`
- `codegraph callers "<symbol>"`
- `codegraph callees "<symbol>"`
- `codegraph impact "<symbol>"`
- `git diff --name-only | codegraph affected --stdin --quiet`

Rules:

- keep timeouts short
- trim output
- classify failures
- do not expose raw huge output to the model
- do not require CodeGraph for basic operation

## rg Fallback Provider

Use when CodeGraph is unavailable.

Capabilities:

- keyword search
- file discovery
- simple anchor discovery

Limitations:

- no real call graph
- no reliable impact analysis
- no affected test graph

Fallback output must clearly say:

`impact_analysis: unavailable`

## Result Schema

All providers should return compact structured results.

Suggested fields:

- `provider`
- `status`
- `query`
- `items`
- `warnings`
- `truncated`
- `next_suggested_query`

## Freshness

Provider freshness states:

- `fresh`
- `probably_fresh`
- `stale`
- `unavailable`
- `unknown`

CodeGraph-based affected test selection requires:

- `fresh`
- or `probably_fresh`

## Error Handling

Classify provider errors:

- not installed
- not initialized
- stale index
- command timeout
- invalid query
- empty result
- output too large
- unknown failure

Do not crash the workflow if CodeGraph is unavailable.

Fallback to `rg`.

## Security

Never include:

- secrets
- raw environment variables
- `.codegraph/` database contents
- `.codebase-memory/` database contents

Commands must not modify product code except `sync` updating local ignored indexes.

## First Product Task

First implementation should not build the whole provider system.

Recommended first product task:

- implement `cc-mini workflow status`
- detect whether `codegraph` is installed
- detect whether `.codegraph/` exists
- report status and next steps

## Later Product Tasks

After status:

1. CodeGraph subprocess wrapper.
2. Compact result schema.
3. rg fallback.
4. affected test selector.
5. context pack generator.
6. tests for provider unavailable/stale/success cases.

## Open Questions

- Should provider results be JSON internally?
- Should CodeGraph subprocess calls be async?
- Should provider timeouts be configurable?
- Should users be able to disable CodeGraph?
- Should `.codegraph/` freshness be checked by timestamp or command output?