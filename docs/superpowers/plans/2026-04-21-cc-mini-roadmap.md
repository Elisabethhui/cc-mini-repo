# cc-mini Long-Term Roadmap

> **Context:** This roadmap is a continuation of the approved Phase 1 minimal startup direction. It does not rely on the unapproved `.planning/` drafts as source of truth.

**Goal:** Turn cc-mini into a local 32K coding workflow product first, then expand it toward a broader general agent without breaking the stable `standard` path.

**Roadmap Principle:** Phase boundaries matter more than feature count. Each phase must be useful on its own, with a clean exit criterion and a plan that can be executed task-by-task.

---

## Product Direction

The long-term product shape is:

1. Keep `standard` stable and backward-compatible.
2. Grow `wiki_strict` into the primary coding workflow for local 32K tasks.
3. Add lifecycle depth in phases: patch, verification, continuity, maintenance, and recovery.
4. Only after the coding workflow is robust, widen the system toward a general agent.

This means the project is **not** trying to become a generic agent first. It is trying to become a strong local coding workflow product first.

---

## Phase Map

### Phase 1: Minimal Startup

Status: already approved and implemented as the first usable product slice.

Primary outcome:
- `init`
- `doctor`
- `run --mode standard`
- `run --mode wiki_strict`
- `scan` / `prime` / `plan`

Exit criterion:
- A user can initialize, inspect, run, and produce structured analysis output without being forced into patch / maintenance surfaces.

### Phase 2: Coding Workflow Productization

Primary outcome:
- explicit patch entrypoint
- rollback-aware multi-file edits
- confirmation-based convergence record
- human-approved convergence summary for the patch transaction

Exit criterion:
- A user can move from analysis to a controlled code change loop, confirm the result, and roll back safely if patch or convergence goes wrong.

### Phase 3: Continuity and Maintenance

Primary outcome:
- workspace semantic artifact store
- long-task spine preservation
- drift recovery suggestions
- manual-first reconcile / maintenance surfaces

Exit criterion:
- cc-mini can survive repeated turn-taking and workspace drift while keeping source files untouched unless the user explicitly approves a write.

### Phase 4: Runtime Isolation and Stability

Primary outcome:
- stronger separation between `standard` and `wiki_strict`
- cleaner tool/prompt/state partitioning
- reduced cross-mode leakage

Exit criterion:
- `standard` stays stable as a general interaction mode, while `wiki_strict` remains a bounded workflow mode with its own assumptions and guards.

### Phase 5: General Agent Expansion

Primary outcome:
- broader task intake
- more general agent surfaces
- multi-step work beyond coding while preserving the coding workflow

Exit criterion:
- cc-mini can handle non-coding workflows without collapsing the carefully built coding path or the `standard` compatibility story.

---

## Cross-Cutting Guardrails

- `standard` must remain stable across all later phases.
- `wiki_strict` should grow by adding explicit boundaries, not by silently changing startup behavior.
- Lifecycle features should only graduate into a phase when the previous phase can already stand on its own.
- Documentation and tests are part of the product boundary, not afterthoughts.
- When a future phase starts to absorb too many concerns, split it before implementation.

---

## Deliverable Set

The roadmap is accompanied by separate phase plans:

- [Phase 2 Coding Workflow Plan](./2026-04-21-cc-mini-phase2-coding-workflow.md)
- [Phase 3 Continuity and Maintenance Plan](./2026-04-21-cc-mini-phase3-continuity-maintenance.md)
- [Phase 4 Runtime Isolation Plan](./2026-04-21-cc-mini-phase4-runtime-isolation.md)
- [Phase 5 General Agent Expansion Plan](./2026-04-21-cc-mini-phase5-general-agent-expansion.md)
