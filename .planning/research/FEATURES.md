# Feature Landscape: AI Coding Assistant for 32K Context Operation

**Domain:** AI coding assistant (cc-mini) with small-context model support
**Researched:** 2026-04-20
**Confidence:** HIGH (based on codebase audit + ecosystem research)

---

## Table Stakes

Features users expect from any production AI coding assistant. Missing these = product feels broken or unsafe.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Accurate token counting** | Heuristic estimates (chars/1.8) are off by 30-50% for code; causes premature or missed compaction | Medium | Use tiktoken (OpenAI) or Anthropic's count_tokens API. cc-mini currently uses heuristic in `token_budget.py` |
| **Sliding window message management** | Without it, every turn resends full history; 32K fills rapidly | Medium | Keep recent N messages raw, summarize older. cc-mini has no sliding window — passes entire history each turn |
| **Context compaction/summarization** | When approaching limits, must preserve critical details (decisions, file paths, errors) while discarding redundant tool outputs | High | cc-mini has `CompactService` but it's not integrated into the engine's decision loop; threshold is 100K (not 32K-aware) |
| **Message dehydration** | Tool results (grep output, file reads) consume massive tokens; must compress older results without losing critical info | Medium | cc-mini has `maybe_dehydrate_messages()` but it's not called by the engine; only head+tail truncation, no semantic summarization |
| **Permission system for write tools** | Users expect confirmation before file edits, shell commands, especially in agentic mode | Low | cc-mini has `PermissionChecker` with y/n/always prompts; covers read-only auto-approval and write tool gating |
| **Session persistence** | Conversations must survive crashes and be resumable | Low | cc-mini has `SessionStore` (JSONL + metadata files) |
| **Checkpointing on context overflow** | When hard limit reached, save state and halt gracefully rather than crash or truncate silently | Medium | cc-mini has `CheckpointManager` but integration with engine budget decisions is fragile |
| **Sandboxed command execution** | Shell commands from LLM must be isolated to prevent host damage | Medium | cc-mini has `SandboxManager` with bubblewrap; opt-in, not mandatory |
| **Tool result error handling** | Failed tools must report errors clearly without breaking the conversation loop | Low | cc-mini's `ToolResult(is_error=True)` pattern handles this |
| **Flow state enforcement** | In structured mode (wiki_strict), the agent must follow defined phases (PLAN→LOCATE→IMPLEMENT→VERIFY) | Medium | cc-mini has `FlowState` enum but transitions are string-based and scattered across files |

## Differentiators

Features that set a 32K-context coding assistant apart from generic large-context tools.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **AST-based code reading** | Instead of dumping entire files, extract only relevant classes/functions. Massive token savings for large files | Medium | cc-mini has `ASTRead` tool and `ast_read.py`; core to wiki_strict mode but needs broader language support |
| **Structured task packs (EditSpec)** | Pre-define modification intent with target file, symbol, span, anchor text. Reduces trial-and-error edits | Medium | cc-mini has `TaskPack`/`EditSpec` in `taskpack.py`; not fully integrated with engine |
| **Post-edit guard** | After edits, analyze AST impact to detect broken references, missing imports, signature changes | High | cc-mini has `PostEditGuard` but it's stubbed in commands.py (returns mock data) |
| **Wiki-first knowledge system** | Maintain structured project knowledge outside context window (architecture, decisions, status). Load only relevant sections | High | cc-mini has wiki subsystem (`wiki/`, `knowledge/`) but hardcoded `.cc-mini/` paths are broken |
| **Incremental file watching** | Auto-update wiki entities when source files change; prevents stale context | Medium | cc-mini has `watcher.py` but race conditions exist |
| **Observation masking (zero-cost compression)** | Replace old tool outputs with lightweight placeholders rather than LLM summarization. 52%+ cheaper, +2.6% accuracy per JetBrains Research | Low | **Not implemented in cc-mini**. Much cheaper than LLM-based compaction |
| **Anchored iterative summarization** | Maintain persistent structured summary (intent, files, decisions, next steps) and merge incrementally. Better continuity than full regeneration | High | **Not implemented**. Factory.ai showed this outperforms full-reconstruction across 36K sessions |
| **Token budget governor with model-aware thresholds** | Different limits for different models (32K vs 200K). Pre-flight checks with safety buffers | Medium | cc-mini has `BudgetThresholds` for 32K but thresholds are hardcoded, not model-aware |
| **Tool result artifact storage** | Store full tool outputs externally, keep only summaries + URI in context. Prevents repeated large outputs | Medium | **Not implemented**. Google ADK pattern |
| **Reconciliation (stale entity detection)** | Detect when wiki entities are out of sync with source and auto-recover | Medium | cc-mini has `reconcile.py` but relies on timestamps/hashes; no dry-run mode |
| **Auto-compaction trigger at 70% budget** | Proactive compression before crisis, not reactive truncation at 90% | Low | cc-mini's `TokenBudgetManager.decide()` has 4 thresholds but trigger logic is not wired to engine pre-flight |
| **Dynamic tool loadout** | Only register relevant tools per task to reduce context consumption from tool schemas | Medium | **Not implemented**. Research shows +44% function-calling accuracy with <30 tools |
| **Context quarantine / sub-agents** | Spawn focused subagents with isolated contexts for parallel tasks | High | **Not implemented**. Cline added native subagents in v3.58 (Feb 2026) |

## Anti-Features

Features to explicitly NOT build — they add complexity without value for 32K context operation.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Full RAG/vector search for codebase** | Adds embedding model dependency, indexing latency, and storage overhead. AST-based static analysis is deterministic and cheaper for code structure | Use AST + call graph (repo-map pattern like Aider) |
| **Automatic multi-file editing without verification** | In 32K contexts, mistakes compound quickly. Every edit must be verifiable | Enforce single-file EditSpec with post-edit guard |
| **Companion/pet game system** | Terminal manipulation, daemon threads, and ANSI sequences cause state corruption and consume context budget | Keep companion as optional, strictly outside core workflow |
| **Opaque compression (OpenAI style)** | 99.3% compression but sacrifices interpretability; debugging context issues becomes impossible | Use structured, human-readable summaries |
| **Tree-sitter for all languages** | Heavy dependency; Python's built-in `ast` module is sufficient for Python-first workflows | Use `ast` for Python; text fallback for other files |
| **Multi-repo workspace support** | Expands context management complexity exponentially; 32K is already tight for single repos | Explicit single-repo focus with manual context control |
| **Real-time collaborative editing** | Outside scope of a CLI coding assistant; adds CRDT/OT complexity | Session-based with explicit handoffs |
| **Full conversation history in context** | Never send complete history on every turn; this is the primary cause of context exhaustion | Sliding window + summarization always |
| **LLM-based dehydration on every tool result** | Calling LLM to summarize every tool output is prohibitively expensive | Use observation masking (placeholders) for old results; LLM summarization only at compaction boundaries |
| **Automatic context expansion (e.g., to 128K)** | Defeats the purpose of 32K optimization; masks underlying inefficiency | Build efficient context management that works at 32K |

## Feature Dependencies

```
Accurate token counting
    → Token budget governor
        → Sliding window management
        → Message dehydration
        → Context compaction
            → Checkpointing on overflow

AST-based code reading
    → Wiki-first knowledge system
        → Incremental file watching
        → Reconciliation
    → Structured task packs (EditSpec)
        → Post-edit guard

Permission system
    → Sandboxed command execution
        → Audit logging (not yet implemented)

Flow state enforcement
    → Wiki-strict mode reliability
```

## MVP Recommendation for 32K Production-Ready

### Prioritize (Phase 1-2)

1. **Fix token counting** — Replace heuristic with tiktoken/Anthropic tokenizer. This is foundational; every other feature depends on accurate counts.
2. **Integrate dehydration into engine flow** — Wire `maybe_dehydrate_messages()` into the engine's pre-flight budget check. Zero-cost observation masking for old tool results.
3. **Implement sliding window** — Keep last 4-6 messages raw, summarize older history. Prevents quadratic cost growth.
4. **Fix hardcoded `.cc-mini/` paths** — Centralize workspace config. Without this, wiki-strict mode is completely broken.
5. **Fix `/dream` and `/plan` bugs** — Known broken features block basic usage.

### Defer (Phase 3+)

- **Sub-agent architecture** — Powerful but complex; single-agent with good context management is sufficient for MVP.
- **Dynamic tool loadout** — Nice optimization but requires significant tool system refactoring.
- **Artifact storage for tool results** — Requires external storage layer; dehydration is sufficient initially.
- **Anchored iterative summarization** — Better than full regeneration but incremental improvement over basic compaction.

### Explicitly Skip

- Companion/pet game rewrite (out of scope per PROJECT.md)
- Multi-repo support (out of scope per PROJECT.md)
- Full tree-sitter integration (out of scope per PROJECT.md)
- SQLite-to-server-DB migration (out of scope per PROJECT.md)

## Sources

- [Claude Code Context Window Management](https://www.mindstudio.ai/blog/context-window-claude-code-manage-consistent-results/) — Official compaction behavior
- [Claude Code Token Budget Management](https://www.mindstudio.ai/blog/ai-agent-token-budget-management-claude-code/) — Budget checks and warning system
- [Factory.ai: Evaluating Context Compression](https://factory.ai/news/evaluating-compression) — Anchored iterative summarization research
- [JetBrains Research: Efficient Context Management](https://blog.jetbrains.com/research/2025/12/efficient-context-management/) — Observation masking vs LLM summarization
- [Zylos Research: AI Agent Context Compression](https://zylos.ai/research/2026-02-28-ai-agent-context-compression-strategies) — Trigger-based compaction architecture
- [LogRocket: LLM Context Problem 2026](https://blog.logrocket.com/llm-context-problem-strategies-2026/) — Context rot and multi-agent isolation
- [Aider Review 2026](https://skywork.ai/skypage/en/ultimate-guide-aider-terminal-ai-programming/2044312829596098560/) — Repo-map and explicit file context
- [Cline Guide 2026](https://skywork.ai/skypage/en/ultimate-guide-cline-ai-coding/2044314087895687168/) — Subagents and checkpoints
- [Cursor Context Management](https://datalakehousehub.com/blog/2026-03-context-management-cursor/) — @-mention context system
- [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) — Permission and confirmation patterns
- [Northflank: Sandbox AI Agents 2026](https://northflank.com/blog/how-to-sandbox-ai-agents) — Isolation technology hierarchy
- [AstraAI: AST-Guided Assistance](https://arxiv.org/html/2603.27423v1) — Structured AST workflow for code generation
- [Code Cartographer: AST Knowledge Graph](https://www.linkedin.com/pulse/code-cartographer-iii-i-stopped-asking-ai-read-built-map-andy-spamer-esohc/) — Map-instead-of-read paradigm
- [Pydantic AI ContextManagerCapability](https://github.com/vstorm-co/summarization-pydantic-ai) — Auto-compress at 90% threshold
- [Agno Context Compression](https://docs.agno.com/compression/overview) — Tool result compression patterns
- [Google ADK: Summarize and Save to Artifact](https://notestime.in/artificial-intelligence/google-adk-agent-development-kit) — After-tool callback pattern
- [MCP Memory Keeper](https://github.com/mkreyman/mcp-memory-keeper) — SQLite-based checkpoint snapshots
- [Context Engineering Techniques 2026](https://towardsai.net/p/machine-learning/context-engineering-the-6-techniques-that-actually-matter-in-2026-a-comprehensive-guide) — Six core techniques
- [LLM Context Window Limitations 2026](https://atlan.com/know/llm-context-window-limitations/) — Lost-in-the-middle and attention dilution
- [Smarter Context Management for LLM Agents](https://blog.jetbrains.com/research/2025/12/efficient-context-management/) — Observation masking research paper
- [ClaudeSlim: Token Reduction](https://github.com/apolloraines/claudeslim) — 60-85% reduction via proxy compression
- [Claude Shorthand: LLMLingua-2](https://github.com/gladehq/claude-shorthand) — ~55% prompt compression
- [OpenAgent: Context Versioning](https://github.com/RaheesAhmed/OpenAgent) — SQLite memory with cross-session persistence
- [Tiktoken Production Guide](https://galileo.ai/blog/tiktoken-guide-production-ai) — Version pinning and dependency isolation
- [LLM Token Counting JavaScript 2026](https://www.pkgpulse.com/blog/gpt-tokenizer-vs-js-tiktoken-vs-xenova-transformers-llm-token-counting-javascript-2026) — Cross-model tokenizer comparison
- [AI Agent Memory Patterns 2026](https://crazyrouter.com/en/blog/ai-agent-memory-patterns-stateful-applications-guide-2026) — Five-layer memory architecture
- [Agent Memory Architectures](https://atlan.com/know/agent-memory-architectures/) — Buffer, sliding window, summary, vector, hybrid patterns
- [Implementing Conversation Memory](https://dev.to/whoffagents/implementing-conversation-memory-in-ai-apps-short-term-long-term-and-context-compression-4o94) — Sliding window implementation patterns
- [Context Window Management Implementation](https://oneuptime.com/blog/post/2026-01-30-context-window-management/view) — Production ContextWindowManager design
- [AI Agent Sandbox Security](https://zylos.ai/research/2026-02-21-ai-agent-sandbox-execution-isolation) — Bubblewrap and microVM isolation
- [AI Agent Security Best Practices](https://www.ibm.com/think/tutorials/ai-agent-security) — PermissionManager with approval + audit
- [Building Production-Ready AI Agents Security Guide](https://dev.to/theaniketgiri/building-production-ready-ai-agents-a-complete-security-guide-2026-4d01) — Multi-layer verification architectures
- [AI Agents 2026: Practical Architecture](https://andriifurmanets.com/blogs/ai-agents-2026-practical-architecture-tools-memory-evals-guardrails) — Tool pools, memory, guardrails
- [Context Engineering Toolkit for AI Coding Assistants](https://arxiv.org/html/2604.08290v1) — Academic survey of context techniques for coding
