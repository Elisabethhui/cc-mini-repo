# Technology Stack: 32K Context Enhancement

**Project:** cc-mini 32K Context Enhancement  
**Researched:** 2026-04-20  
**Scope:** Token counting, context compression, sliding window management, testing tools

---

## Recommended Stack

### Token Counting

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `tiktoken` | **0.12.0** | Fast BPE tokenization for OpenAI models | Rust-backed, ~1M tokens/sec, exact for GPT-4/4o/o1/o3. Recognizes `gpt-5` identifier as of 0.12.0. |
| `anthropic` SDK | **>=0.40.0** | Official Python SDK for Anthropic API | Provides `beta.messages.count_tokens()` for billing-grade exact counts on Claude models. |

**Rationale:**

- **For OpenAI models:** `tiktoken` is the only production-grade offline tokenizer. It is exact (not estimated) because OpenAI publishes their BPE merge tables. Version 0.12.0 (Oct 2025) adds Python 3.14 support, free-threaded Python compatibility, and `gpt-5` model recognition. **Caveat:** 0.12.0 drops `manylinux2014` wheels; pin to 0.11.0 if your build environment uses Amazon Linux 2.

- **For Anthropic models:** There is **no offline tokenizer** available. The `anthropic` Python SDK's `client.beta.messages.count_tokens()` is the official, free, exact method. The old `client.count_tokens(text)` is deprecated and inaccurate for Claude 3+. **Confidence: HIGH** — verified via official SDK source and multiple community sources.

- **Cross-provider abstraction:** If you need a single interface for both, wrap `tiktoken` for OpenAI and `anthropic.beta.messages.count_tokens()` for Anthropic behind a provider-aware `TokenCounter` protocol. Do NOT use `tiktoken` to approximate Claude tokens — accuracy drops to ~95-98% vs 99.8% for the official endpoint.

**What NOT to use:**

| Library | Why Avoid |
|---------|-----------|
| `transformers` tokenizers | Heavy dependency (PyTorch), overkill for counting only. Use only if you already depend on `transformers`. |
| Character-count heuristics (e.g. `len(text) / 4`) | Inaccurate for code, CJK text, and tool schemas. The existing `token_budget.py` uses `chars / 1.8` which is a known bug. |
| `tiktoken` with `p50k_base` for Claude | Produces ~2-5% error vs actual Claude counts. Unacceptable for 32K window management where every token matters. |

---

### Context Compression

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `llmlingua` | **latest** (pip install) | Prompt compression via token pruning | Microsoft-backed, 2x-20x compression, preserves key information better than naive truncation. |
| `llmlingua-2` | bundled with `llmlingua` | Faster encoder-based compression | ~0.4s on V100, 2x-5x typical ratio, better for production RAG. |
| Native summarization (existing `CompactService`) | N/A | LLM-based conversation compaction | Already in codebase (`src/core/compact.py`). Keep and enhance rather than replace. |

**Rationale:**

- **For conversation compaction (cc-mini's primary need):** The existing `CompactService` in `src/core/compact.py` follows the Claude Code `autoCompact.ts` pattern and is the right approach. It uses an LLM call to summarize old messages into a structured summary. **Do NOT replace this with LLMLingua** — LLMLingua is designed for compressing long prompts/documents (RAG), not conversational history. Conversational compaction requires semantic understanding of decisions, errors, and pending tasks that token-pruning cannot preserve.

- **For RAG/wiki ingestion (future):** `llmlingua-2` is the 2025 standard for prompt compression when ingesting large documents into context. It uses a lightweight bidirectional transformer (not a decoder LLM) so it's fast and cheap. Install with `pip install llmlingua`.

- **For dehydration (existing):** The existing `dehydration.py` / `MinimalDehydrator` pattern of replacing old tool results with head/tail summaries is correct and lightweight. Enhance it rather than replacing.

**What NOT to use:**

| Approach | Why Avoid |
|----------|-----------|
| Naive truncation (drop oldest messages) | Loses critical context like system instructions, architectural decisions, unresolved errors. |
| LLMLingua for conversation history | Designed for documents, not dialogue. Cannot preserve turn structure or decision rationale. |
| Knowledge Graph memory (LangChain) | Overkill for cc-mini's single-session, single-repo scope. Adds latency and complexity. |

---

### Context Window Management

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Native Python (`collections.deque`, list slicing) | stdlib | Sliding window message buffer | No dependency needed. Simple, fast, predictable. |
| `token_budget.py` (enhanced) | existing | Token budget state machine | Already exists. Replace heuristic counting with accurate tokenizer integration. |

**Rationale:**

- **Sliding window:** For cc-mini's 32K target, a pure-Python implementation is sufficient. The Strands Agents SDK pattern (`SlidingWindowConversationManager`) is a good reference but pulling in their SDK is overkill. Implement:
  1. **Token-based window:** Keep messages until token budget exceeded, then trim oldest.
  2. **Atomic pair preservation:** Never split a `tool_use` / `tool_result` pair.
  3. **Priority tiers:** System prompt (never drop) > current user query > recent assistant replies > old tool results > old user messages.

- **Budget thresholds (existing):** The `BudgetThresholds` dataclass in `token_budget.py` has sensible defaults for 32K (soft 16K, compact 20K, checkpoint 24K, hard stop 26K). Keep these values — they reserve 8K for model output + safety buffer, which is correct for 32K models.

- **Integration point:** The `TokenBudgetManager.estimate_from_messages()` method currently uses `total_chars / 1.8` — this is the critical bug to fix. Replace with:
  - OpenAI models: `tiktoken.encoding_for_model(model).encode()`
  - Anthropic models: `client.beta.messages.count_tokens()` (or cache results to avoid API round-trip on every check)

**What NOT to use:**

| Library | Why Avoid |
|---------|-----------|
| LangChain memory modules | Heavy dependency, abstraction mismatch for tool-loop agents. |
| `litellm` token_counter | Useful for multi-provider, but adds dependency. cc-mini only supports 2 providers; direct SDK calls are cleaner. |
| vLLM truncation | Server-side inference feature, not applicable to client-side API callers. |

---

### Testing Tools

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pytest` | **>=8.0** (existing) | Test runner | Already in `pyproject.toml`. Keep. |
| `pytest-asyncio` | **>=0.23** (existing) | Async test support | Already configured. Keep. |
| `respx` | **>=0.22.0** | Mock `httpx` HTTP calls | Anthropic and OpenAI SDKs both use `httpx` under the hood. `respx` provides clean mock routing for token counting endpoints. |
| `pytest-mockllm` | **>=0.2.1** | Dedicated LLM mocking plugin | Zero-config fixtures, built-in token counting mocks, chaos engineering (rate limits, timeouts). Good for integration tests. |
| `unittest.mock` | stdlib | Simple unit test mocking | For isolating `TokenBudgetManager` without HTTP dependencies. |

**Rationale:**

- **For testing token counting:** Mock the Anthropic `beta.messages.count_tokens()` endpoint with `respx` or `unittest.mock.patch`. Return deterministic `input_tokens` values. For OpenAI/tiktoken, no mocking needed — tiktoken is deterministic and offline.

- **For testing compaction:** Mock `LLMClient.create_message()` to return a fixed summary. Assert on the message list structure (summary + recent messages preserved).

- **For testing sliding window:** Pure unit tests with synthetic message lists. No HTTP mocking needed.

- **pytest-mockllm** is optional but valuable if you want chaos testing (simulate rate limits on token counting API).

---

## Installation

```bash
# Core token counting (OpenAI models)
pip install "tiktoken>=0.12.0"

# Anthropic SDK (already in pyproject.toml as >=0.40.0)
pip install "anthropic>=0.40.0"

# Optional: prompt compression for RAG/wiki ingestion
pip install "llmlingua"

# Dev / testing
pip install "respx>=0.22.0"
pip install "pytest-mockllm>=0.2.1"
```

---

## Version Verification

| Library | Verified Version | Source | Date Verified |
|---------|-----------------|--------|---------------|
| tiktoken | 0.12.0 (Oct 6, 2025) | [GitHub Releases](https://github.com/openai/tiktoken/releases), [CHANGELOG.md](https://github.com/openai/tiktoken/blob/main/CHANGELOG.md), Fedora bugzilla | 2026-04-20 |
| anthropic SDK | 0.40.0 (Nov 28, 2024) — 0.50.0+ (Apr 2025) | [GitHub Releases](https://github.com/anthropics/anthropic-sdk-python/releases), [CHANGELOG.md](https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md) | 2026-04-20 |
| tiktoken 0.11.0 | Aug 8, 2025 | [GitHub Releases](https://github.com/openai/tiktoken/releases) | 2026-04-20 |
| pytest-mockllm | 0.2.1 | [GitHub](https://github.com/godhiraj-code/pytest-mockllm), [Blog](https://www.dhirajdas.dev/blog/pytest-mockllm-true-fidelity) | 2026-04-20 |

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Token counting (OpenAI) | **HIGH** | tiktoken is official, version-verified, exact. |
| Token counting (Anthropic) | **HIGH** | `beta.messages.count_tokens()` is official, free, exact. Old `count_tokens(text)` deprecated. Verified via SDK source and community. |
| Context compression | **HIGH** | Keep existing `CompactService`. LLMLingua is for RAG, not conversations. |
| Sliding window | **HIGH** | Pure Python is correct for this scale. Reference patterns from Strands SDK validated. |
| Testing tools | **MEDIUM** | `respx` and `pytest-mockllm` are well-documented but not yet integrated into cc-mini. |

---

## Sources

- [tiktoken GitHub Releases](https://github.com/openai/tiktoken/releases) — Version 0.12.0 release notes
- [tiktoken CHANGELOG.md](https://github.com/openai/tiktoken/blob/main/CHANGELOG.md) — Detailed version history
- [Anthropic Python SDK CHANGELOG.md](https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md) — Version 0.40.0+ history
- [Anthropic Python SDK GitHub Releases](https://github.com/anthropics/anthropic-sdk-python/releases) — Release notes
- [Context7: tiktoken documentation](https://context7.com/openai/tiktoken/llms.txt) — Python usage patterns, encoding names
- [Stack Overflow: Best way to count tokens for Anthropic Claude](https://stackoverflow.com/questions/78767238/best-way-to-count-tokens-for-anthropic-claude-models-using-the-api) — Community consensus on `beta.messages.count_tokens()`
- [Strands Agents SDK: Conversation Management](https://strandsagents.com/docs/user-guide/concepts/agents/conversation-management/) — Sliding window reference implementation
- [Anthropic Engineering: Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — Official best practices
- [LLMLingua-2 Paper / Microsoft GitHub](https://github.com/microsoft/LLMLingua) — Prompt compression library
- [pytest-mockllm GitHub](https://github.com/godhiraj-code/pytest-mockllm) — LLM mocking plugin
- [respx documentation](https://tonyaldon.com/2026-02-12-mocking-the-openai-api-with-respx-in-python/) — HTTP mocking for OpenAI/Anthropic APIs
