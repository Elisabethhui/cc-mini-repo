# Research Synthesis: cc-mini 32K Context Enhancement

**Project:** cc-mini 32K Context Enhancement
**Synthesized:** 2026-04-20
**Scope:** Context compression, token counting, sliding window, security, wiki infrastructure

---

## Executive Summary

The cc-mini 32K Context Enhancement project is a brownfield effort to make an existing AI coding assistant framework production-ready for small-context (32K) models. The codebase already contains partial implementations of all major context management components — token budgeting, message dehydration, conversation compaction, checkpointing, and a wiki-strict mode — but critical gaps exist in integration, accuracy, and security.

The recommended approach is a **graduated compression pipeline** with accurate token counting as the foundation. Every other feature (sliding window, dehydration, compaction) depends on knowing the true token count. The existing heuristic (`chars / 1.8`) is off by 30-50% for code, creating a compounding error that breaks budget decisions. Fix token counting first, then wire the existing dehydration and compaction services into the engine's pre-flight loop, then add sliding window management.

Security hardening must run in parallel with Phase 1. The codebase has active shell injection, path traversal, and ReDoS vulnerabilities that are exploitable today. These are not theoretical — they are production-grade security gaps that must be closed before any wider usage.

The wiki-strict mode, which is the primary value proposition for 32K operation, is currently broken due to hardcoded `.cc-mini/` paths that were deleted during cleanup. This must be fixed immediately to make the mode functional.

---

## Stack Recommendations

### Core Dependencies

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| `tiktoken` | >=0.12.0 | OpenAI token counting | Rust-backed, exact for GPT-4/4o/o1/o3. Official BPE merge tables. |
| `anthropic` SDK | >=0.40.0 | Anthropic token counting | `beta.messages.count_tokens()` is the only exact method for Claude models. |
| `llmlingua` | latest (optional) | RAG prompt compression | For future wiki document ingestion, NOT for conversation history. |
| `respx` | >=0.22.0 | HTTP mocking for tests | Both Anthropic and OpenAI SDKs use `httpx` under the hood. |
| `pytest-mockllm` | >=0.2.1 (optional) | LLM mocking plugin | Chaos testing (rate limits, timeouts) for integration tests. |

### What NOT to Add

- **LangChain memory modules** — Heavy dependency, abstraction mismatch for tool-loop agents.
- **Transformers tokenizers** — PyTorch dependency is overkill for counting only.
- **LLMLingua for conversation compaction** — Designed for documents, not dialogue. Cannot preserve turn structure or decision rationale.
- **Knowledge Graph memory** — Overkill for single-session, single-repo scope.

### Key Version Notes

- `tiktoken` 0.12.0 drops `manylinux2014` wheels; pin to 0.11.0 if using Amazon Linux 2.
- The old `anthropic.count_tokens(text)` is deprecated and inaccurate for Claude 3+; use `beta.messages.count_tokens()` only.
- Do NOT use `tiktoken` with `p50k_base` for Claude — produces 2-5% error vs actual counts.

---

## Feature Priorities

### Table Stakes (Must-Have for Production)

| # | Feature | Current State | Gap |
|---|---------|---------------|-----|
| 1 | **Accurate token counting** | Heuristic (`chars/1.8`) in `token_budget.py` | Replace with tiktoken / Anthropic tokenizer |
| 2 | **Sliding window message management** | None — full history sent every turn | Implement token-based window with atomic pair preservation |
| 3 | **Context compaction/summarization** | `CompactService` exists but hardcoded for 200K | Make 32K-aware, integrate into engine decision loop |
| 4 | **Message dehydration** | `maybe_dehydrate_messages()` exists but not called by engine | Wire into engine pre-flight; add structured dehydration |
| 5 | **Permission system for write tools** | `PermissionChecker` exists with y/n/always | Working; keep as-is |
| 6 | **Session persistence** | `SessionStore` (JSONL + metadata) | Working; keep as-is |
| 7 | **Checkpointing on overflow** | `CheckpointManager` exists | Hardcoded paths, no resume logic |
| 8 | **Sandboxed command execution** | `SandboxManager` with bubblewrap | Opt-in; should be mandatory |
| 9 | **Tool result error handling** | `ToolResult(is_error=True)` pattern | Working; keep as-is |
| 10 | **Flow state enforcement** | `FlowState` enum exists | Transitions are string-based and scattered |

### Differentiators (Should-Have for Competitive Edge)

| # | Feature | Current State | Value |
|---|---------|---------------|-------|
| 1 | **AST-based code reading** | `ASTRead` tool exists | Core to wiki_strict; needs broader language support |
| 2 | **Structured task packs (EditSpec)** | `TaskPack`/`EditSpec` in `taskpack.py` | Not fully integrated with engine |
| 3 | **Post-edit guard** | `PostEditGuard` exists but stubbed in `commands.py` | Real implementation needed |
| 4 | **Wiki-first knowledge system** | `wiki/`, `knowledge/` subsystems exist | Hardcoded `.cc-mini/` paths are broken |
| 5 | **Observation masking (zero-cost compression)** | Not implemented | 52%+ cheaper, +2.6% accuracy per JetBrains Research |
| 6 | **Auto-compaction trigger at 70% budget** | `TokenBudgetManager.decide()` has 4 thresholds | Trigger logic not wired to engine pre-flight |
| 7 | **Reconciliation (stale entity detection)** | `reconcile.py` exists | Relies on timestamps/hashes; no dry-run mode |

### Defer to v2+

- Sub-agent architecture (Cline v3.58 pattern) — powerful but complex
- Dynamic tool loadout (<30 tools for +44% accuracy) — requires significant tool system refactoring
- Tool result artifact storage (Google ADK pattern) — requires external storage layer
- Anchored iterative summarization (Factory.ai pattern) — incremental improvement over basic compaction
- Full tree-sitter integration for non-Python files

### Explicitly Skip

- Companion/pet game rewrite (terminal manipulation issues, out of scope)
- Multi-repo workspace support (expands complexity exponentially)
- SQLite to server DB migration (single-instance use case is sufficient)
- Full RAG/vector search for codebase (AST + call graph is cheaper and deterministic)

---

## Architecture Guidance

### Core Pattern: Graduated Compression Pipeline

Apply the cheapest compression first, escalate only when needed. For 32K contexts, 4 levels are sufficient:

| Level | Name | Mechanism | Trigger | Cost |
|-------|------|-----------|---------|------|
| 1 | Tool Result Truncation | Hard cap on tool output size | Always active | Zero |
| 2 | Dehydration | Replace old tool results with head/tail summaries | > soft_limit (16K) | Zero |
| 3 | Compaction | LLM summarizes old messages | > compact_limit (20K) | 1 API call |
| 4 | Checkpoint | Save state, halt session | > checkpoint_limit (24K) | Zero |

### Component Boundaries

| Component | Responsibility | Status |
|-----------|---------------|--------|
| `TokenBudgetManager` | Estimates tokens, defines thresholds, makes budget decisions | Basic — needs accurate tokenizer |
| `DehydrationService` | Lightweight replacement of old tool results | Basic — not integrated into engine |
| `CompactService` | LLM-based summarization of conversation history | Partial — hardcoded for 200K |
| `SlidingWindowManager` | Manages which messages stay in active context | Missing |
| `ContextAssembler` | Builds final message list for API calls | Missing — duplicated in engine |
| `CheckpointManager` | Session state persistence for recovery | Basic — hardcoded paths |
| `SessionStore` | Persistent JSONL storage | Complete |

### Key Patterns to Follow

1. **Sliding Window with Tool Pair Preservation** — Never split a `tool_use` from its `tool_result`. Walk backwards from the end, accumulating recent messages until both `MIN_RECENT_MESSAGES` and `MIN_RECENT_TOKENS` are met.

2. **Dual-Path Token Estimation** — Use API-reported `usage.input_tokens` as ground truth when available; fall back to `tiktoken` / Anthropic tokenizer for pre-flight estimates. Maintain a running calibration factor.

3. **Append-Only Session Storage** — Never modify previously written transcript lines. Enables recovery, audit trails, and compaction without data loss.

4. **Budget State Machine** — Explicit states with clear transitions: `NORMAL -> WARNING -> COMPACT -> CHECKPOINT -> HARD_STOP`. Each state has defined mitigations.

### Build Order (Dependencies)

1. `MessageNormalizer` (no dependencies) — Foundation
2. `SessionStore` (no dependencies) — Persistence
3. `TokenBudgetManager` (no dependencies) — Decision engine
4. `SlidingWindowManager` (depends on MessageNormalizer)
5. `DehydrationService` (depends on MessageNormalizer)
6. `CheckpointManager` (depends on SessionStore)
7. `CompactService` (depends on LLMClient, SlidingWindowManager)
8. `ContextAssembler` (depends on all above) — Orchestrator
9. `Engine` (depends on all above) — Integration point

---

## Critical Pitfalls

### Pitfall 1: Heuristic Token Counting Without Ground Truth Calibration

- **What:** `total_chars / 1.8` is off by 30-50% for code. The engine multiplies this by 1.5x as a "safety factor," creating compounding error up to 2x.
- **Consequence:** Premature checkpointing (wasting context) or silent overruns (API failures).
- **Prevention:** Integrate `tiktoken` / Anthropic tokenizer. Remove the 1.5x multiplier. Use API-reported usage as ground truth.
- **Phase:** Phase 1 (Token Budget Foundation)

### Pitfall 2: Compaction Hangs and Infinite Loops

- **What:** `CompactService.compact()` calls the LLM without a timeout. If the model hangs, the engine blocks indefinitely.
- **Consequence:** Session freezes (observed in Claude Code: 277% CPU, 11.8GB RAM for 26+ hours).
- **Prevention:** Add 60-second timeout. Implement fallback to truncation. Cap input to 50% of context window. Add circuit breaker after 3 failures.
- **Phase:** Phase 2 (Message Dehydration + Compaction)

### Pitfall 3: Lossy Dehydration Destroys Critical Context

- **What:** `_cheap_summary()` keeps only 250 chars head + 180 chars tail. Error messages, exact file paths, and debugging chains are lost.
- **Consequence:** Model re-reads files, re-attempts failed approaches, generates code with wrong identifiers.
- **Prevention:** Add `critical` flag for tool results that must never be dehydrated. Preserve error messages in full. Use structured dehydration by tool type.
- **Phase:** Phase 2 (Message Dehydration + Compaction)

### Pitfall 4: Shell Injection via Unsanitized Tool Input

- **What:** `BashTool.execute()` passes `command` directly to `subprocess.run(cmd, shell=True, ...)`. `SandboxManager` is opt-in.
- **Consequence:** Arbitrary code execution (CVE-2025-61260, CVE-2025-53773).
- **Prevention:** Disable `shell=True` by default. Parse commands into lists. Make sandbox mandatory. Add audit logging.
- **Phase:** Phase 1 (Security Hardening)

### Pitfall 5: File Path Traversal in File Tools

- **What:** `FileReadTool`, `FileEditTool`, `FileWriteTool`, `GlobTool` accept arbitrary `file_path` without validation.
- **Consequence:** Data exfiltration, supply chain attacks, credential theft.
- **Prevention:** Add `PathSandbox` restricting all file ops to project root. Normalize paths with `Path.resolve()`. Add allowlist for sensitive files.
- **Phase:** Phase 1 (Security Hardening)

### Additional High-Priority Pitfalls

| # | Pitfall | Phase |
|---|---------|-------|
| 6 | Hardcoded `.cc-mini/` paths breaking wiki subsystems | Phase 1 (Wiki Infrastructure Fix) |
| 7 | `/dream` command has zero exception handling | Phase 1 (Bug Fixes) |
| 8 | String-based FlowState transitions (typos cause silent failures) | Phase 1 (Type Safety) |
| 9 | Zero test coverage in wiki subsystems | Phase 3 (Test Coverage) |
| 10 | API key exposure via module-level `load_dotenv()` | Phase 1 (Security Hardening) |

---

## Recommended Phase Order

### Phase 1: Foundation + Security (Weeks 1-2)

**Rationale:** Security vulnerabilities and broken infrastructure block all other work. Token counting is the foundation for every context management feature.

**Deliverables:**
- Fix token counting: integrate `tiktoken` (OpenAI) and `anthropic.beta.messages.count_tokens()` (Claude)
- Fix hardcoded `.cc-mini/` paths: centralize workspace config in `config.py`
- Fix `/dream` exception safety: add try/except + atomic writes
- Fix `/plan` type safety and lifecycle binding
- Enforce `FlowState` enum everywhere (replace string-based transitions)
- Security hardening:
  - BashTool: disable `shell=True`, add command allowlist
  - File tools: add `PathSandbox` with project-root restriction
  - GrepTool: add regex validation and timeout
  - Config: move `load_dotenv()` to explicit call, mask API keys

**Pitfalls addressed:** 1, 4, 5, 7, 8, 10

**Research needed:** LOW — patterns are well-documented, codebase analysis is complete.

### Phase 2: Context Management Core (Weeks 3-4)

**Rationale:** With accurate token counting and fixed infrastructure, implement the graduated compression pipeline.

**Deliverables:**
- Implement `SlidingWindowManager` with tool pair preservation
- Wire `DehydrationService` into engine pre-flight loop
- Add structured dehydration (preserve errors, add critical flag)
- Fix `CompactService` for 32K models (adjust thresholds, add timeout + fallback)
- Wire compaction trigger into engine decision loop
- Fix `CheckpointManager` resume logic
- Fix `PostEditGuard` async function handling (`ast.AsyncFunctionDef`)
- Fix wiki watcher race conditions (debouncing + exponential backoff)

**Pitfalls addressed:** 2, 3, 6, 12, 14

**Research needed:** MEDIUM — sliding window implementation details, compaction timeout tuning.

### Phase 3: Testing + Resilience (Weeks 5-6)

**Rationale:** Achieve comprehensive test coverage and add resilience patterns before production.

**Deliverables:**
- Unit tests for all wiki modules with mocked filesystem
- Integration tests for `/prime -> /plan -> /post_edit` workflow
- Test coverage for token budget manager, dehydration, compaction
- Add rate limiting / circuit breaker to `LLMClient`
- Enable SQLite WAL mode for concurrent writes
- Add tool input schema validation (`jsonschema`)
- Performance: move sync file I/O to thread pool

**Pitfalls addressed:** 9, 11, 13, 15, 16, 19, 20

**Research needed:** LOW — standard testing and resilience patterns.

### Phase 4: Polish + Differentiators (Weeks 7-8)

**Rationale:** Add features that differentiate cc-mini from generic coding assistants.

**Deliverables:**
- Observation masking (zero-cost compression for old tool results)
- Auto-compaction trigger at 70% budget (proactive, not reactive)
- Model-aware token budget thresholds (32K vs 200K)
- Dynamic tool loadout (register only relevant tools per task)
- Wiki reconciliation dry-run mode
- Tool result artifact storage (optional, for large outputs)

**Pitfalls addressed:** None new — incremental improvements.

**Research needed:** MEDIUM — observation masking implementation, dynamic tool registration.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | tiktoken and Anthropic SDK are official, version-verified. No ambiguity. |
| Features | **HIGH** | Based on direct codebase audit + extensive ecosystem research. Gaps are clearly identified. |
| Architecture | **HIGH** | Graduated compression pipeline is the industry standard (Claude Code, Sourcegraph). Component boundaries are clear. |
| Pitfalls | **HIGH** | Many pitfalls are confirmed by official bug reports (Claude Code GitHub issues) and security research (CVEs). |
| Overall | **HIGH** | This is a well-understood domain with clear best practices. The main risk is execution, not research. |

### Gaps to Address

1. **Compaction timeout tuning:** What is the right timeout for 32K models? 60 seconds is a starting guess; may need adjustment based on model latency.
2. **Sliding window parameters:** `MIN_RECENT_MESSAGES` (4-6) and `MIN_RECENT_TOKENS` (e.g., 8K) need empirical tuning.
3. **Observation masking implementation:** JetBrains Research shows 52%+ savings, but the exact placeholder format needs design.
4. **Dynamic tool loadout:** Which tools to register per task? Needs task classification logic.

---

## Sources

### Stack
- [tiktoken GitHub Releases](https://github.com/openai/tiktoken/releases)
- [Anthropic Python SDK CHANGELOG](https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md)
- [Strands Agents SDK: Conversation Management](https://strandsagents.com/docs/user-guide/concepts/agents/conversation-management/)
- [Anthropic Engineering: Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [LLMLingua-2 Paper / Microsoft GitHub](https://github.com/microsoft/LLMLingua)

### Features
- [Factory.ai: Evaluating Context Compression](https://factory.ai/news/evaluating-compression)
- [JetBrains Research: Efficient Context Management](https://blog.jetbrains.com/research/2025/12/efficient-context-management/)
- [Claude Code Context Window Management](https://www.mindstudio.ai/blog/context-window-claude-code-manage-consistent-results/)
- [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)
- [AstraAI: AST-Guided Assistance](https://arxiv.org/html/2603.27423v1)

### Architecture
- [Claude Code Architecture Deep Dive](https://wavespeed.ai/blog/posts/claude-code-architecture-leaked-source-deep-dive/)
- [Claude Code Compaction Explained](https://okhlopkov.com/claude-code-compaction-explained/)
- [Anthropic Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- cc-mini codebase analysis (`src/core/engine.py`, `src/core/token_budget.py`, `src/core/compact.py`, `src/core/dehydration.py`)

### Pitfalls
- [Claude Code Hangs During Compaction](https://github.com/anthropics/claude-code/issues/19567)
- [Context Compaction Loses Critical Knowledge](https://github.com/anthropics/claude-code/issues/29890)
- [Prompt Injection Attacks on Agentic Coding Assistants](https://arxiv.org/html/2601.17548v1)
- [IDEsaster: 30+ Vulnerabilities in AI Coding Tools](https://tigran.tech/securing-ai-coding-agents-idesaster-vulnerabilities/)
- cc-mini codebase analysis (`src/core/engine.py`, `src/core/token_budget.py`, `src/core/compact.py`, `src/core/dehydration.py`, `src/core/commands.py`, `src/core/tools/*.py`)
