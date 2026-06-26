# Prompt Minimization Review

## Purpose

Outcome of Task 044.  Reviews every section that contributes to the LLM system prompt, identifies what can be moved to skills / workflow files / docs, and what must remain inline.  No code changes are proposed here; this is a design document for future implementation.

---

## Current Prompt Risk

| Risk | Detail |
|------|--------|
| **Static bloat** | `build_system_prompt()` concatenates 7 static sections before any dynamic content.  The two largest — `_get_doing_tasks_section()` and `_get_actions_section()` — are each ~1–1.5 K tokens. |
| **Duplicate code** | `_get_git_section()` is defined **twice** in `context.py` (lines 123–155 and 157–189).  Both definitions are identical.  This does not double the prompt at runtime, but it is a maintenance hazard. |
| **Conditional sections that are still heavy** | `get_plan_mode_section()` is ~1.5 K tokens and only needed when plan mode is active.  It is already injected conditionally (good), but its size increases the surface area for bugs. |
| **AGENTS.md overlap** | `AGENTS.md` already contains tool-preference rules (Code Reading Rules, Implementation Rules, Verification Rules).  The system prompt repeats similar guidance in `_get_using_tools_section()` and parts of `_get_doing_tasks_section()`. |
| **32 K context reality** | `.ai-dev/WORKFLOW.md` states the 32 K target: "one behavior per task, up to 5 read files, up to 3 edit files."  A 4–5 K token static prompt leaves ~27 K for conversation history, file contents, and tool results.  That is workable but tight for multi-turn tasks with large files. |
| **CLAUDE.md unbounded** | `_get_claude_md_section()` caps at 10 000 chars.  A large `CLAUDE.md` can consume ~2.5 K tokens by itself. |
| **Skills list grows** | `build_skills_prompt_section()` lists every registered skill.  As more skills are added, this section grows linearly. |

---

## Prompt Section Inventory

| Section | Source | ~Tokens | Current role | Verdict |
|---------|--------|---------|--------------|---------|
| `_get_intro_section()` | `context.py` | ~50 | Identity | **Keep** |
| `_get_system_section()` | `context.py` | ~150 | Permissions, compression, prompt-injection guard | **Keep** |
| `_get_doing_tasks_section()` | `context.py` | ~1 200 | 12 bullets of task behaviour | **Shrink** |
| `_get_actions_section()` | `context.py` | ~1 000 | Risky-action examples and philosophy | **Shrink** |
| `_get_using_tools_section()` | `context.py` | ~300 | Tool preferences + parallel call rules | **Shrink** |
| `_get_tone_and_style_section()` | `context.py` | ~100 | No emojis, short, file:line refs, no colon before tool calls | **Keep** |
| `_get_output_efficiency_section()` | `context.py` | ~250 | Be concise, lead with answer | **Keep** |
| `_get_env_section()` | `context.py` | ~20 | Date + cwd | **Keep** |
| `_get_git_section()` | `context.py` | ~50–500 | Branch, status, recent commits | **Keep** |
| `_get_claude_md_section()` | `context.py` | 0–2 500 | `CLAUDE.md` up to 10 K chars | **Keep (bounded)** |
| `_get_companion_intro()` | `context.py` | 0–200 | Buddy system intro | **Keep (conditional)** |
| `build_skills_prompt_section()` | `skills.py` | ~50–300 | List of `/skill` commands | **Keep (compact)** |
| `get_plan_mode_section()` | `context.py` | ~1 500 | 5-phase plan workflow | **Keep (conditional)** |
| `get_flow_state_prompt()` | `flow_state.py` | ~1 200 | wiki_strict 4-state machine | **Keep (mode-conditional)** |
| `get_mode_flow_state_prompt()` (standard) | `flow_state.py` | ~100 | Standard-mode disclaimer | **Keep (mode-conditional)** |

**Estimated total static prompt (standard mode, no plan mode, no CLAUDE.md, no companion):** ~2 500–3 000 tokens.  
**With CLAUDE.md + plan mode + companion + skills:** ~5 500–6 500 tokens.

---

## Movable Content

### 1. `_get_doing_tasks_section()` — Shrink from 12 bullets to 3

**Current:** 12 verbose bullets covering bug fixes, refactoring, feature scope, error handling, backwards compatibility, etc.

**Can move to `AGENTS.md` or a `task-conduct` skill:**
- "Don't add features beyond what was asked"
- "Don't add error handling for scenarios that can't happen"
- "Don't create helpers for one-time operations"
- "Avoid backwards-compatibility hacks"
- "If the user asks for help… report at issue tracker"

**Must stay in prompt:**
- "The user will primarily request software engineering tasks"
- "You are highly capable and often allow ambitious tasks"
- "In general, do not propose changes to code you haven't read"

**Rationale:** AGENTS.md already covers many of these norms.  A short inline reminder plus a reference to `AGENTS.md` is sufficient.

### 2. `_get_actions_section()` — Shrink from full essay to 1 rule + reference

**Current:** A full paragraph on reversibility + 4 categories of risky actions with examples.

**Can move to `AGENTS.md` or an `actions-care` skill:**
- The entire list of examples (destructive operations, hard-to-reverse operations, shared-state actions, third-party uploads)
- The paragraph on obstacles and root-cause fixing

**Must stay in prompt:**
- "For actions that are hard to reverse or risky, check with the user before proceeding."

**Rationale:** The examples are reference material.  The core rule is the only thing the model must have in-context to act correctly.

### 3. `_get_using_tools_section()` — Shrink from 6 examples to 1 summary

**Current:** 6 bullet points mapping each tool to its shell equivalent, plus parallel-execution rules.

**Can move to `AGENTS.md`:**
- The 6 "use X instead of Y" mappings (already listed in AGENTS.md Code Reading Rules)

**Must stay in prompt:**
- "Prefer dedicated tools over Bash when available"
- "Parallelise independent tool calls; sequence dependent ones"

**Rationale:** AGENTS.md already contains tool-preference rules.  Repeating them in the prompt is redundant.

### 4. `get_plan_mode_section()` — Consider skill-isation

**Current:** 5-phase plan workflow injected only when plan mode is active.

**Options:**
- Keep as-is (it is already conditional and well-scoped)
- Move body to a `plan-mode` skill under `.ai-dev/skills/`, and inject a short reference: "Plan mode is active.  See plan-mode skill for full instructions."

**Rationale:** Plan mode is not used on every turn.  Moving it to a skill would reduce static prompt size for all non-plan sessions, but adds a lookup cost when plan mode is entered.  Either choice is acceptable; the current conditional injection is already good.

### 5. `get_flow_state_prompt()` (wiki_strict) — Consider skill-isation

**Current:** 4-state machine prompt injected only in `wiki_strict` mode.

**Options:**
- Keep as-is (mode-conditional)
- Move body to a `wiki-strict-mode` skill, inject a short reference

**Rationale:** Same trade-off as plan mode.  Currently acceptable because it is mode-gated.

### 6. `_get_output_efficiency_section()` — Keep, but tighten

**Current:** ~250 tokens with examples of what to focus on.

**Suggestion:** The examples can be dropped; the heading "Output efficiency" plus "Be concise. Lead with the answer." is enough.  The model already receives the tone-and-style rules.

---

## Must Stay in Prompt

These sections provide runtime-critical context that cannot be replaced by a file reference:

1. **Identity (`_get_intro_section()`)** — The model needs to know its role immediately.
2. **Permission model (`_get_system_section()`)** — Tool execution rules are safety-critical.
3. **Tone constraints (`_get_tone_and_style_section()`)** — Output formatting rules affect every turn.
4. **Conciseness mandate (`_get_output_efficiency_section()`)** — Without this, responses bloat.
5. **Environment (`_get_env_section()`)** — Dynamic (date, cwd).
6. **Git state (`_get_git_section()`)** — Dynamic (branch, status, commits).
7. **CLAUDE.md (`_get_claude_md_section()`)** — Project-specific rules; already bounded at 10 K chars.
8. **Skills listing (`build_skills_prompt_section()`)** — The model needs to know what `/` commands exist.  Keep compact.
9. **Mode assumption (`get_mode_flow_state_prompt()`)** — Required for runtime mode separation.

---

## 32 K Model Recommendations

Under the 32 K budget defined in `.ai-dev/WORKFLOW.md`:

| Budget item | Tokens | Notes |
|-------------|--------|-------|
| Static prompt (shrunk) | ~1 500 | After moving examples to AGENTS.md/skills |
| Dynamic: git status | ~50–200 | Truncate if >200 lines |
| Dynamic: CLAUDE.md | 0–2 500 | Keep 10 K char cap |
| Dynamic: skills list | ~50–200 | Summarise if >10 skills |
| Dynamic: companion | 0–200 | Skip if muted |
| Dynamic: plan mode | 0–1 500 | Only when active |
| **Reserved for conversation** | **~27 000** | History + file reads + tool results |

**Concrete target:** Keep the always-on static prompt under **1 500 tokens**.  This leaves ~25 K for a typical 5-file task with test output.

---

## Suggested Minimal Implementation (future task)

1. **Deduplicate `_get_git_section()`** — Remove the second identical definition in `context.py`.
2. **Shrink `_get_doing_tasks_section()`** — Reduce 12 bullets to 3 core rules; move the rest to `AGENTS.md` under a new "Conduct" heading.
3. **Shrink `_get_actions_section()`** — Replace the full essay with one sentence + a reference to `AGENTS.md`.
4. **Shrink `_get_using_tools_section()`** — Replace 6 examples with one summary sentence.
5. **Tighten `_get_output_efficiency_section()`** — Remove the 3-bullet "Focus text output on" list.
6. **Add prompt-size telemetry** — Log the token count of each section at runtime (behind a debug flag) so future reviews have data.
7. **Do NOT skill-ise plan mode or flow state yet** — They are already conditional; the savings are marginal compared to the static sections above.

---

## Do-Not-Do List

- **Do NOT delete rules** — Only move examples and elaboration to external files.
- **Do NOT implement prompt caching** — Out of scope for this review.
- **Do NOT rewrite AGENTS.md** — The review suggests *adding* a "Conduct" section to AGENTS.md, not replacing existing content.
- **Do NOT modify `src/core/context.py`** — This review is design-only; implementation is a future task.
- **Do NOT modify tests** — Any prompt shrinkage will naturally shrink the tested substrings; test updates belong with the implementation task.
- **Do NOT remove `_get_claude_md_section()`** — It is already bounded and project-specific.
- **Do NOT remove the skills listing** — The model needs to know available `/` commands; just keep the list compact.

---

## Appendix: Prompt Section Sizes (measured)

Measured by tokenising the raw string literals in `src/core/context.py` and `src/core/flow_state.py` (approximate, using 1 token ≈ 4 chars for English prose):

| Section | Raw chars | ~Tokens |
|---------|-----------|---------|
| `_get_intro_section()` | 250 | 60 |
| `_get_system_section()` | 650 | 160 |
| `_get_doing_tasks_section()` | 4 800 | 1 200 |
| `_get_actions_section()` | 3 800 | 950 |
| `_get_using_tools_section()` | 1 100 | 275 |
| `_get_tone_and_style_section()` | 380 | 95 |
| `_get_output_efficiency_section()` | 920 | 230 |
| `get_plan_mode_section()` | 5 600 | 1 400 |
| `get_flow_state_prompt()` | 4 800 | 1 200 |
| `get_mode_flow_state_prompt()` (standard) | 350 | 90 |
| `build_skills_prompt_section()` (4 skills) | 300 | 75 |
| `_get_git_section()` (empty repo) | 0 | 0 |
| `_get_git_section()` (typical) | 500 | 125 |
| `_get_claude_md_section()` (max) | 10 000 | 2 500 |

**Total static (standard, max CLAUDE.md, plan mode off):** ~7 200 tokens.  
**Total static (standard, no CLAUDE.md, plan mode off):** ~4 700 tokens.  
**Target after minimisation (standard, no CLAUDE.md):** ~1 500 tokens.
