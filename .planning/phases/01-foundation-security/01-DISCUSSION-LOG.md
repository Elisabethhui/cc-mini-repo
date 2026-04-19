# Phase 1: Foundation & Security - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-20
**Phase:** 1-foundation-security
**Areas discussed:** Token Counting, Security Hardening, Wiki Infrastructure, Budget State Machine
**Mode:** Auto (all decisions selected from research recommendations)

---

## Token Counting Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Dual-path (tiktoken + Anthropic API) | tiktoken for OpenAI, `count_tokens()` for Claude. Most accurate, handles both providers | ✓ |
| tiktoken only | Simpler but 2-5% error for Claude models. Not recommended for mixed usage | |
| Heuristic with calibration | Keep chars/1.8 but adjust multiplier based on observed error. Still inaccurate | |

**Auto-selected:** Dual-path (recommended by research — only way to achieve <5% error for both providers)
**Notes:** Remove 1.5x safety multiplier simultaneously; it was a band-aid for inaccurate counting.

---

## Security Hardening Priority

| Option | Description | Selected |
|--------|-------------|----------|
| Bash injection first | Fix `shell=True` first — highest CVE-class severity, easiest exploit | ✓ |
| File traversal first | Add PathSandbox first — affects all file operations | |
| All vulnerabilities in parallel | Fix everything at once — higher risk of conflicts | |

**Auto-selected:** Bash injection first, then file tools, then GrepTool regex validation (recommended by research — severity-based ordering)
**Notes:** Sandbox mode should become mandatory, not opt-in.

---

## Wiki Workspace Path

| Option | Description | Selected |
|--------|-------------|----------|
| Configurable via config.py | Add `workspace_dir` to AppConfig, default to `.cc-mini/` | ✓ |
| Restore hardcoded `.cc-mini/` | Simplest fix but inflexible | |
| User home directory | `~/.cc-mini/` — avoids repo pollution | |

**Auto-selected:** Configurable via config.py (recommended — flexible, backward-compatible default)
**Notes:** All wiki modules must read from config instead of hardcoded strings.

---

## FlowState Migration

| Option | Description | Selected |
|--------|-------------|----------|
| All-at-once refactor | Replace all string states with enum in one pass | ✓ |
| Gradual migration | Replace string states as files are touched | |

**Auto-selected:** All-at-once refactor (recommended — string states cause silent failures; partial migration leaves broken transitions)
**Notes:** Add exhaustive transition validation to catch typos at import time.

---

## Budget State Machine Design

| Option | Description | Selected |
|--------|-------------|----------|
| Enum with transitions | `BudgetState` enum with valid transition mapping | ✓ |
| Boolean flags | `is_warning`, `is_compact` flags — simpler but less explicit | |

**Auto-selected:** Enum with transitions (recommended — explicit states prevent invalid transitions)
**Notes:** Model-aware thresholds: 32K uses 16K/20K/24K/26K; 200K uses 100K/120K/150K/180K.

---

## Claude's Discretion

- Error formatting for security violations — use existing `ToolResult(is_error=True)` pattern
- Audit logging — deferred to v2

## Deferred Ideas

- Audit logging for security forensics
- Startup security scan
- Tool result artifact storage
- Observation masking
- Dynamic tool loadout
