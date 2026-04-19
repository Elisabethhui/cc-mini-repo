# Architecture Patterns: Context Management for AI Coding Assistants

**Domain:** AI coding assistant with 32K token context support
**Researched:** 2026-04-20
**Confidence:** HIGH (based on codebase analysis + industry research)

## Recommended Architecture

Based on analysis of the cc-mini codebase and industry patterns from Claude Code, Sourcegraph, and other production AI coding assistants, context management for 32K token models requires a **graduated compression pipeline** with clear component boundaries and explicit data flow.

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **TokenBudgetManager** | Estimates token usage, defines thresholds, makes budget decisions | Engine (pre-flight + post-flight checks) |
| **DehydrationService** | Lightweight replacement of old tool results with summaries | Engine (triggered by budget decisions) |
| **CompactService** | LLM-based summarization of conversation history | Engine (triggered by budget decisions), LLMClient |
| **CheckpointManager** | Session state persistence for recovery | Engine (triggered by hard stops) |
| **SlidingWindowManager** | Manages which messages stay in active context | Engine (message lifecycle) |
| **ContextAssembler** | Builds the final message list for API calls | Engine (before each API call) |
| **MessageNormalizer** | Normalizes content blocks between SDK formats | Engine, LLMClient |
| **SessionStore** | Persistent JSONL storage of all messages | Engine (append-only) |

### Data Flow

```
User Input → Engine.submit()
                │
                ▼
        ┌───────────────────┐
        │ ContextAssembler  │ ← Builds message list from:
        │                   │   - System prompt (static + dynamic)
        │                   │   - Active messages (sliding window)
        │                   │   - Summarized history (compact)
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ TokenBudgetManager│ ← Estimates tokens, decides state
        │ .estimate_from()  │   (NORMAL → WARNING → COMPACT → CHECKPOINT → HARD_STOP)
        │ .decide()         │
        └─────────┬─────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
   [NORMAL]          [WARNING/COMPACT]
        │                   │
        │         ┌─────────┴─────────┐
        │         │                   │
        │         ▼                   ▼
        │   DehydrationService   CompactService
        │   (cheap, in-place)    (LLM summarization)
        │         │                   │
        │         └─────────┬─────────┘
        │                   │
        │                   ▼
        │         ┌───────────────────┐
        │         │ SlidingWindowMgr  │ ← Ensures recent messages preserved
        │         │ (never splits     │   Keeps MIN_RECENT_MESSAGES + MIN_RECENT_TOKENS
        │         │  tool_use/result) │
        │         └─────────┬─────────┘
        │                   │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ Engine API Loop   │ ← Calls LLMClient.stream_messages()
        │                   │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ Post-Flight Check │ ← TokenBudgetManager.update_from_usage()
        │                   │   If over threshold → checkpoint + halt
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ SessionStore      │ ← Append-only JSONL persistence
        │ .append_message() │
        └───────────────────┘
```

### Build Order (Dependencies)

1. **MessageNormalizer** (no dependencies) — Foundation for all message handling
2. **SessionStore** (no dependencies) — Persistence layer
3. **TokenBudgetManager** (no dependencies) — Decision engine
4. **SlidingWindowManager** (depends on MessageNormalizer) — Message partitioning
5. **DehydrationService** (depends on MessageNormalizer) — Cheap compression
6. **CheckpointManager** (depends on SessionStore) — Recovery state
7. **CompactService** (depends on LLMClient, SlidingWindowManager) — Expensive compression
8. **ContextAssembler** (depends on all above) — Orchestrates final message list
9. **Engine** (depends on all above) — Main integration point

## Patterns to Follow

### Pattern 1: Graduated Compression Pipeline
**What:** Apply the cheapest compression first, escalate only when needed.
**When:** Every API call pre-flight check.
**Why:** Minimizes information loss and API cost. Claude Code uses 5 levels; for 32K contexts, 3-4 levels are sufficient.

**Levels for 32K Context:**

| Level | Name | Mechanism | Trigger | Cost |
|-------|------|-----------|---------|------|
| 1 | **Tool Result Truncation** | Hard cap on tool output size | Always active | Zero |
| 2 | **Dehydration** | Replace old tool results with head/tail summaries | > soft_limit (16K) | Zero |
| 3 | **Compaction** | LLM summarizes old messages | > compact_limit (20K) | 1 API call |
| 4 | **Checkpoint** | Save state, halt session | > checkpoint_limit (24K) | Zero |

**Example:**
```python
# In Engine.submit() pre-flight check
token_count = budget_manager.estimate_from_messages(messages)
decision = budget_manager.decide(token_count)

if decision.should_dehydrate:
    dehydration_result = dehydrator.dehydrate(messages)
    token_count = budget_manager.estimate_from_messages(messages)
    decision = budget_manager.decide(token_count)

if decision.should_compact:
    messages = compact_service.compact(messages, system_prompt)
    token_count = budget_manager.estimate_from_messages(messages)
    decision = budget_manager.decide(token_count)

if decision.should_checkpoint:
    checkpoint_manager.write_checkpoint(...)
    yield ("text", "[checkpoint saved; run /resume-from-checkpoint]")
    return
```

### Pattern 2: Sliding Window with Tool Pair Preservation
**What:** Partition messages into (history_to_summarize, recent_to_keep) while never splitting tool_use from tool_result.
**When:** Before compaction and dehydration.
**Why:** Tool pairs must stay atomic to maintain conversation coherence.

**Example:**
```python
def _split_recent(messages: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split messages into (history, recent).
    
    Walks backwards, accumulating recent messages until we meet both
    MIN_RECENT_MESSAGES and MIN_RECENT_TOKENS. Never splits a
    tool_use / tool_result pair.
    """
    if len(messages) <= MIN_RECENT_MESSAGES:
        return [], list(messages)

    keep_start = len(messages)
    kept_tokens = 0
    kept_msgs = 0

    for i in range(len(messages) - 1, -1, -1):
        kept_tokens += estimate_tokens_single(messages[i])
        kept_msgs += 1
        keep_start = i

        if kept_msgs >= MIN_RECENT_MESSAGES and kept_tokens >= MIN_RECENT_TOKENS:
            break

    # Don't split tool_use from its tool_result
    if keep_start > 0:
        msg = messages[keep_start]
        content = msg.get("content", "")
        if (msg.get("role") == "user"
                and isinstance(content, list)
                and all(isinstance(b, dict) and b.get("type") == "tool_result"
                        for b in content)):
            keep_start -= 1  # Include the preceding assistant tool_use

    return messages[:keep_start], messages[keep_start:]
```

### Pattern 3: Dual-Path Token Estimation
**What:** Use API-reported usage when available, fall back to heuristic estimation.
**When:** Post-flight after every API call; pre-flight before every API call.
**Why:** API usage is exact; heuristic is fast but approximate. Combining both gives <5% error vs 30%+ from pure estimation.

**Example:**
```python
class TokenBudgetManager:
    def update_from_usage(self, usage, fallback_messages):
        """Prefer API-reported usage; fall back to estimation."""
        if usage is not None:
            for attr in ("input_tokens", "prompt_tokens", "total_tokens"):
                val = getattr(usage, attr, None)
                if isinstance(val, int) and val > 0:
                    self._last_token_estimate = val
                    return val
        return self.estimate_from_messages(fallback_messages)
```

### Pattern 4: Append-Only Session Storage
**What:** Never modify previously written transcript lines; only append new events.
**When:** Every message persistence operation.
**Why:** Enables recovery, audit trails, and compaction without data loss. Claude Code's session storage is entirely append-oriented.

**Example:**
```python
class SessionStore:
    def append_message(self, message: dict) -> None:
        """Persist one message (append to JSONL)."""
        safe = _serialize_message(message)
        safe["_ts"] = _now_iso()
        with open(self._jsonl_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(safe, ensure_ascii=False) + "\n")
```

### Pattern 5: Budget State Machine
**What:** Explicit states with clear transitions and actions.
**When:** Pre-flight and post-flight token checks.
**Why:** Prevents ambiguous decision-making; each state has defined mitigations.

```
NORMAL → WARNING → COMPACT → CHECKPOINT → HARD_STOP
         (dehydrate)  (compact)   (checkpoint)  (stop)
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Single-Shot Compression
**What:** Waiting until near the limit, then doing one massive compaction.
**Why bad:** Causes sudden quality degradation, long pauses, and potential failures if compaction itself exceeds budget.
**Instead:** Graduated pipeline with early, cheap interventions.

### Anti-Pattern 2: Blind Truncation
**What:** Simply dropping oldest messages without summarization.
**Why bad:** Loses critical context (user preferences, architectural decisions, error resolutions).
**Instead:** Always summarize before discarding; preserve key facts in structured format.

### Anti-Pattern 3: Splitting Tool Pairs
**What:** Keeping a tool_use but dropping its tool_result, or vice versa.
**Why bad:** Breaks conversation coherence; model expects results for its tool calls.
**Instead:** Treat tool_use + tool_result as atomic units in sliding window logic.

### Anti-Pattern 4: Heuristic-Only Token Counting
**What:** Using character-count heuristics without API usage calibration.
**Why bad:** 30%+ error rates lead to premature or late compression triggers.
**Instead:** Dual-path estimation with API usage as ground truth.

### Anti-Pattern 5: In-Place Message Mutation Without Persistence
**What:** Modifying messages in memory without writing to session store.
**Why bad:** Lost work on crash; no audit trail; recovery impossible.
**Instead:** Append new compacted/summarized messages; keep originals in archive.

## Scalability Considerations

| Concern | At 100 messages | At 1K messages | At 10K messages |
|---------|-----------------|----------------|-----------------|
| Token estimation | Fast heuristic | Cached deltas | Incremental updates |
| Dehydration | Linear scan | Batch processing | Background thread |
| Compaction | Single summary | Hierarchical summaries | Multi-level summaries |
| Session storage | Single JSONL | Sharded by date | Archive old shards |
| Checkpoint | Single file | Differential saves | Incremental snapshots |

## Integration with Existing cc-mini Architecture

### Current State
The cc-mini codebase already has partial implementations of all major components:

| Component | File | Status | Gap |
|-----------|------|--------|-----|
| TokenBudgetManager | `src/core/token_budget.py` | Basic | Needs accurate tokenizer (tiktoken/cl100k_base) |
| DehydrationService | `src/core/dehydration.py` | Basic | Not integrated into engine flow properly |
| CompactService | `src/core/compact.py` | Partial | Hardcoded for 200K models, not 32K |
| CheckpointManager | `src/core/checkpoint.py` | Basic | Hardcoded paths, no resume logic |
| SessionStore | `src/core/session.py` | Complete | Works well |
| Engine | `src/core/engine.py` | Partial | Budget checks duplicated, not unified |

### Recommended Integration Points

1. **Engine.submit() pre-flight:** Replace duplicated budget checks with single `ContextAssembler.build_context()` call.
2. **Engine post-flight:** Unified post-usage check with automatic dehydration/compaction.
3. **Wiki-strict mode:** Add `WikiContextAssembler` that includes wiki entities in system prompt.
4. **Tool result path:** Add size limits in `Tool.execute()` before returning to engine.

## Sources

- [Claude Code Architecture Deep Dive](https://wavespeed.ai/blog/posts/claude-code-architecture-leaked-source-deep-dive/) — HIGH confidence (industry analysis)
- [Claude Code Compaction Explained](https://okhlopkov.com/claude-code-compaction-explained/) — MEDIUM confidence (community analysis)
- [Claude Code Context Engineering Compression Pipeline](https://harrisonsec.com/blog/claude-code-context-engineering-compression-pipeline/) — MEDIUM confidence (community analysis)
- [Anthropic Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — HIGH confidence (official)
- [Optimizing Context Windows for AI Agents](https://medium.com/@catalanogabriele15/optimizing-context-windows-for-effective-ai-agents-1778e8edbbfc) — MEDIUM confidence (community)
- [AI Context Window Management Techniques 2026](https://www.ai-agentsplus.com/blog/ai-context-window-management-techniques-2026) — MEDIUM confidence (community)
- cc-mini codebase analysis (`src/core/engine.py`, `src/core/token_budget.py`, `src/core/compact.py`, `src/core/dehydration.py`) — HIGH confidence (primary source)
