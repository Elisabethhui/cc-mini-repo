# cc-mini 32K Context Enhancement Project

**Project Type:** Brownfield enhancement  
**Last updated:** 2026-04-20 after initialization

## What This Is

This project enhances the existing `cc-mini` AI coding assistant framework to fully support 32K token context small models. cc-mini already has a `wiki_strict` mode designed for this purpose, but critical gaps remain in context compression, token counting accuracy, message dehydration integration, and robustness of core features like `/dream` and `/plan`.

## Core Value

Make cc-mini's `wiki_strict` mode production-ready for 32K context models by fixing known bugs, filling architectural gaps, and achieving comprehensive test coverage.

## Context

cc-mini is a Python-based AI coding assistant with:
- Standard mode: full REPL with tool-use loop
- Wiki-strict mode: structured workflow with AST-based code reading, strict patch verification, and automated lifecycle management

The codebase has 79 Python files across core engine, tools, wiki subsystems, knowledge system, and companion features. A codebase map exists at `.planning/codebase/`.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Focus on wiki_strict mode | User explicitly wants 32K small model support | — Pending |
| Fix /dream and /plan bugs first | These are known broken features blocking usage | — Pending |
| Brownfield approach | Existing codebase with partial implementation | — In Progress |

## Requirements

### Validated

- ✓ Interactive REPL with streaming API loop — existing (`main.py`, `engine.py`)
- ✓ Tool system (read, edit, write, bash, glob, grep, agent) — existing (`tools/`)
- ✓ LLM abstraction (Anthropic/OpenAI) — existing (`llm.py`)
- ✓ Session persistence — existing (`session.py`)
- ✓ Basic wiki_strict mode infrastructure — existing (`wiki/`, `knowledge/`)
- ✓ Token budget estimation (heuristic) — existing (`token_budget.py`)
- ✓ AST-based code reading — existing (`ast_read.py`)
- ✓ Companion/buddy system — existing (`buddy/`)

### Active

- [ ] Fix `/dream` command exception safety (messages lost on error)
- [ ] Fix `/plan` mode type safety and lifecycle binding
- [ ] Integrate message dehydration into engine flow
- [ ] Replace heuristic token counting with accurate tokenizer
- [ ] Implement sliding window context management
- [ ] Fix hardcoded `.cc-mini/` paths in wiki subsystems
- [ ] Add FlowState enum validation (replace string-based states)
- [ ] Achieve test coverage for all wiki subsystems
- [ ] Fix shell injection vulnerabilities in BashTool
- [ ] Fix file path traversal in file tools
- [ ] Add input validation on tool schemas

### Out of Scope

- Companion game rewrite (terminal manipulation issues) — too large, not core to 32K support
- SQLite to server DB migration — single-instance use case is sufficient
- Full tree-sitter integration for non-Python files — Python AST is sufficient for now
- Multi-repo workspace support — single codebase

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-20 after initialization*
