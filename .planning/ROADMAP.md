# ROADMAP: cc-mini 32K Context Enhancement

**Version:** v1  
**Granularity:** Coarse (3 phases)  
**Last updated:** 2026-04-20  

---

## Phases

- [ ] **Phase 1: Foundation & Security** — Close security vulnerabilities, fix token counting, repair wiki-strict infrastructure
- [ ] **Phase 2: Context Management Core** — Implement graduated compression pipeline for 32K contexts
- [ ] **Phase 3: Testing & Validation** — Achieve comprehensive test coverage for all new and modified code

---

## Phase Details

### Phase 1: Foundation & Security

**Goal:** The codebase is secure, token counts are accurate, and wiki-strict mode infrastructure is functional.

**Depends on:** Nothing (first phase)

**Requirements:** SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, TOK-01, TOK-02, TOK-03, TOK-04, WIK-01, WIK-02, WIK-03, WIK-04, WIK-05, WIK-06

**Success Criteria** (what must be TRUE):

1. User can run cc-mini without shell injection vulnerabilities — BashTool parses commands into argument lists or enforces sandbox execution
2. User can use file tools safely — all file operations are restricted to the project root directory
3. Token budget reports are accurate within 5% of actual API usage for both OpenAI and Claude models
4. Wiki-strict mode works with configurable workspace paths — no hardcoded `.cc-mini/` paths remain
5. `/dream` and `/plan` commands are exception-safe and type-safe — messages restore on error, types are correct

**Plans:** TBD

---

### Phase 2: Context Management Core

**Goal:** The engine manages 32K context through graduated compression without losing critical information.

**Depends on:** Phase 1

**Requirements:** CTX-01, CTX-02, CTX-03, CTX-04, CTX-05

**Success Criteria** (what must be TRUE):

1. Engine preserves recent conversation history within token budget while keeping tool-use/tool-result pairs atomic — never splits a pair
2. Old tool results are dehydrated (summarized) when context exceeds soft limit (16K), with error messages preserved in full
3. Critical tool results are never dehydrated — the `critical` flag is respected by the dehydration service
4. Compaction triggers automatically at compact limit (20K) with 60-second timeout and fallback to truncation if LLM hangs
5. Budget state machine transitions visibly through defined states: NORMAL → WARNING → COMPACT → CHECKPOINT → HARD_STOP

**Plans:** TBD

---

### Phase 3: Testing & Validation

**Goal:** All new and modified code has comprehensive test coverage.

**Depends on:** Phase 2

**Requirements:** TST-01, TST-02, TST-03, TST-04, TST-05

**Success Criteria** (what must be TRUE):

1. `TokenBudgetManager` has unit tests with mocked tokenizer — all threshold decisions are verified
2. `DehydrationService` has unit tests with synthetic messages — dehydration logic and critical flag handling are verified
3. `SlidingWindowManager` has unit tests covering edge cases: empty history, single message, tool pairs spanning window boundary
4. All wiki subsystems have unit tests: `taskpack`, `reconcile`, `archive`, `post_edit_guard`, `target_identity`
5. `/dream` command has integration test with mock engine — verifies message restoration on error

**Plans:** TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Security | 0/5 | Not started | — |
| 2. Context Management Core | 0/5 | Not started | — |
| 3. Testing & Validation | 0/5 | Not started | — |

---

## Coverage Validation

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | Phase 1 | Pending |
| SEC-02 | Phase 1 | Pending |
| SEC-03 | Phase 1 | Pending |
| SEC-04 | Phase 1 | Pending |
| SEC-05 | Phase 1 | Pending |
| TOK-01 | Phase 1 | Pending |
| TOK-02 | Phase 1 | Pending |
| TOK-03 | Phase 1 | Pending |
| TOK-04 | Phase 1 | Pending |
| CTX-01 | Phase 2 | Pending |
| CTX-02 | Phase 2 | Pending |
| CTX-03 | Phase 2 | Pending |
| CTX-04 | Phase 2 | Pending |
| CTX-05 | Phase 2 | Pending |
| WIK-01 | Phase 1 | Pending |
| WIK-02 | Phase 1 | Pending |
| WIK-03 | Phase 1 | Pending |
| WIK-04 | Phase 1 | Pending |
| WIK-05 | Phase 1 | Pending |
| WIK-06 | Phase 1 | Pending |
| TST-01 | Phase 3 | Pending |
| TST-02 | Phase 3 | Pending |
| TST-03 | Phase 3 | Pending |
| TST-04 | Phase 3 | Pending |
| TST-05 | Phase 3 | Pending |

**Mapped:** 25/25 requirements ✓  
**Orphaned:** None ✓

---

## v2 Deferred Requirements

The following requirements are intentionally deferred to v2 and not included in this roadmap:

- **V2-CTX-01:** Observation masking (zero-cost compression for old tool results)
- **V2-CTX-02:** Auto-compaction trigger at 70% budget (proactive, not reactive)
- **V2-CTX-03:** Anchored iterative summarization (Factory.ai pattern)
- **V2-WIK-01:** Wiki reconciliation dry-run mode
- **V2-WIK-02:** Post-edit guard real implementation (replace stub in `commands.py`)
- **V2-ENG-01:** Dynamic tool loadout (register only relevant tools per task)
- **V2-ENG-02:** Tool result artifact storage (external, with URI reference)
- **V2-RES-01:** Rate limiting and circuit breaker for LLMClient
- **V2-RES-02:** SQLite WAL mode for concurrent session writes
- **V2-RES-03:** Tool input schema validation (`jsonschema`)
- **V2-RES-04:** Async file I/O for tool execution

---

*Last updated: 2026-04-20*
