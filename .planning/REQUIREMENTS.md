# Requirements: cc-mini 32K Context Enhancement

**Version:** v1  
**Last updated:** 2026-04-20  
**Based on:** Research synthesis + codebase audit

---

## v1 Requirements (Must Deliver)

### Security (SEC)

- [ ] **SEC-01:** BashTool must not use `shell=True` with unsanitized input. Parse commands into argument lists or enforce sandbox.
- [ ] **SEC-02:** File tools (read/edit/write/glob) must validate paths against project root sandbox.
- [ ] **SEC-03:** GrepTool must validate regex and set timeout to prevent ReDoS.
- [ ] **SEC-04:** API key loading must happen at runtime (`main()`), not at module import time.
- [ ] **SEC-05:** Sandbox mode must be mandatory for all write tools and Bash execution.

### Token & Budget (TOK)

- [ ] **TOK-01:** Replace heuristic token counting (`chars/1.8`) with accurate tokenizer (`tiktoken` for OpenAI, `anthropic.beta.messages.count_tokens()` for Claude).
- [ ] **TOK-02:** Remove the 1.5x safety multiplier in engine pre-flight checks; rely on accurate counting.
- [ ] **TOK-03:** Token budget thresholds must be model-aware (32K vs 200K).
- [ ] **TOK-04:** Budget state machine must have explicit states: NORMAL → WARNING → COMPACT → CHECKPOINT → HARD_STOP.

### Context Management (CTX)

- [ ] **CTX-01:** Implement sliding window message management with atomic tool pair preservation.
- [ ] **CTX-02:** Wire dehydration service into engine pre-flight loop at soft_limit (16K).
- [ ] **CTX-03:** Add structured dehydration with `critical` flag and error preservation.
- [ ] **CTX-04:** Fix CompactService for 32K models (adjust thresholds, add 60s timeout, fallback to truncation).
- [ ] **CTX-05:** Wire compaction trigger into engine decision loop at compact_limit (20K).

### Wiki Infrastructure (WIK)

- [ ] **WIK-01:** Replace all hardcoded `.cc-mini/` paths with configurable workspace directory from `config.py`.
- [ ] **WIK-02:** Fix `/dream` command exception safety: use `try/finally` to restore `engine.messages` on error.
- [ ] **WIK-03:** Fix `/plan` type safety: `plan_manager` must be typed as `PlanModeManager`, not `object`.
- [ ] **WIK-04:** Enforce `FlowState` enum for all state transitions; remove string-based state names.
- [ ] **WIK-05:** Fix `PostEditGuard` to handle `ast.AsyncFunctionDef`.
- [ ] **WIK-06:** Fix wiki watcher race conditions with debouncing and exponential backoff.

### Testing (TST)

- [ ] **TST-01:** Unit tests for `TokenBudgetManager` with mocked tokenizer.
- [ ] **TST-02:** Unit tests for `DehydrationService` with synthetic messages.
- [ ] **TST-03:** Unit tests for `SlidingWindowManager` with edge cases (empty, single message, tool pairs).
- [ ] **TST-04:** Unit tests for all wiki subsystems (`taskpack`, `reconcile`, `archive`, `post_edit_guard`, `target_identity`).
- [ ] **TST-05:** Integration test for `/dream` command (mock engine, verify message restoration).

---

## v2 Requirements (Defer)

### Differentiators

- [ ] **V2-CTX-01:** Observation masking (zero-cost compression for old tool results).
- [ ] **V2-CTX-02:** Auto-compaction trigger at 70% budget (proactive, not reactive).
- [ ] **V2-CTX-03:** Anchored iterative summarization (Factory.ai pattern).
- [ ] **V2-WIK-01:** Wiki reconciliation dry-run mode.
- [ ] **V2-WIK-02:** Post-edit guard real implementation (replace stub in `commands.py`).
- [ ] **V2-ENG-01:** Dynamic tool loadout (register only relevant tools per task).
- [ ] **V2-ENG-02:** Tool result artifact storage (external, with URI reference).

### Resilience

- [ ] **V2-RES-01:** Rate limiting and circuit breaker for LLMClient.
- [ ] **V2-RES-02:** SQLite WAL mode for concurrent session writes.
- [ ] **V2-RES-03:** Tool input schema validation (`jsonschema`).
- [ ] **V2-RES-04:** Async file I/O for tool execution.

---

## Out of Scope

| Item | Reason |
|------|--------|
| Companion/pet game rewrite | Terminal manipulation issues; not core to 32K support |
| Multi-repo workspace support | Expands complexity exponentially; 32K is tight for single repos |
| Full tree-sitter for non-Python files | Python `ast` module is sufficient; heavy dependency |
| SQLite to server DB migration | Single-instance use case is sufficient |
| Full RAG/vector search | AST + call graph is cheaper and deterministic for code |
| LLM-based dehydration on every tool result | Prohibitively expensive; observation masking is sufficient |
| Real-time collaborative editing | Outside scope of CLI coding assistant |

---

## Traceability

| Requirement | Phase | Verification |
|-------------|-------|--------------|
| SEC-01..05 | Phase 1 | Security audit + unit tests |
| TOK-01..04 | Phase 1 | Unit tests with known token counts |
| CTX-01..05 | Phase 2 | Integration tests with synthetic sessions |
| WIK-01..06 | Phase 1 + 2 | Wiki workflow integration test |
| TST-01..05 | Phase 3 | pytest coverage report |

---

*Last updated: 2026-04-20 after requirements definition*
