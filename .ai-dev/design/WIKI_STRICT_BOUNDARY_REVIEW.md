# Wiki-Strict Boundary Review

## Purpose

This document is the outcome of Task 043. It reviews the boundary between the legacy wiki_strict subsystem (`src/core/wiki/`, `src/core/knowledge/`) and the new context-bounded workflow core (Tasks 031–042).  It does **not** propose code changes; it classifies existing surfaces so future tasks can make informed deprecation, consolidation, or preservation decisions.

---

## Current wiki_strict Capability Inventory

| Module | Responsibility | Phase | Mutable? |
|--------|---------------|-------|----------|
| `flow_state.py` | 4-step state machine prompt injection (PLAN→LOCATE→IMPLEMENT→VERIFY) | Phase 1 | Prompt only |
| `knowledge/ingester.py` | AST-based entity ingestion, drift tracker, frontmatter hash management | Phase 1–2 | Writes `.cc-mini/wiki/entities/` |
| `knowledge/watcher.py` | File-system watcher with debounce, `ChangedFileTracker` | Phase 2 | Background thread |
| `knowledge/dehydrator.py` | `RuntimeSnapshot` writer + `MinimalDehydrator` bridge to `core.dehydration` | Phase 2 | Writes `.cc-mini/wiki/snapshots/` |
| `wiki/taskpack.py` | `TaskPack`, `EditSpec`, `GoalStack`, `TaskPackManager` persistence | Phase 3 | Writes `.cc-mini/wiki/taskpacks/` |
| `wiki/closeout.py` | `CloseoutRecord` / `CloseoutStore` for milestone closeout | Phase 6 | Writes `.cc-mini/wiki/reports/closeout/` |
| `wiki/reconcile.py` | Stale/drift detection, source-hash mismatch, `apply_action` | Phase 3 | Reads entities; `apply_action` moves files |
| `wiki/maintenance.py` | Lifecycle maintenance (old snapshots, taskpacks, deferred issues) | Phase 5 | `dry_run` by default; can delete/archive |
| `wiki/archive.py` | `ArchiveEngine` for snapshots, taskpacks, reports | Phase 5 | Moves/copies files |
| `wiki/lint.py` | Wiki structure health check (orphans, consistency, frontmatter) | Phase 5 | Read-only |
| `wiki/semantic_artifacts.py` | `SemanticArtifactStore` with derived/manual layers | Phase 3 | Writes `.cc-mini/wiki/artifacts/` |
| `wiki/post_edit_guard.py` | Patch impact analysis via AST diff, completion-state machine | Phase 6 | Writes impact summaries |
| `wiki/target_identity.py` | Target symbol resolution for `/prime` | Phase 1 | Read-only |
| `wiki/query_archive.py` | Archive query utilities | Phase 5 | Read-only |

---

## Overlap with New Workflow Core (Tasks 031–042)

### 1. Scan / Ingestion ↔ CodeIntel Provider

- **wiki**: `WikiIngester` builds its own AST summaries and writes `.cc-mini/wiki/entities/*.md`.  It has a custom drift tracker and frontmatter status model (`raw_ast` → `partially_digested` → `digested` → `stale`).
- **workflow**: `CodeIntel Provider` (design doc) targets CodeGraph → Codebase-Memory-MCP → `rg` fallback.  It does not maintain its own entity cache.
- **Overlap**: Both provide "what exists in the codebase" introspection.  `WikiIngester` is self-hosted but redundant if CodeGraph or `rg` is available.

### 2. Task Tracking ↔ Work Log + Workflow Next

- **wiki**: `TaskPack` is a rich structured object (`GoalStack`, `EditSpec`, entity status, deferred issues, micro-forks).  `TaskPackManager` persists it under `.cc-mini/wiki/taskpacks/`.
- **workflow**: `work_log.py` generates compact Markdown summaries under `.ai-dev/worklogs/`.  `workflow_next.py` infers coarse state from git + doctor + artifact flags.
- **Overlap**: Both track "what is the current task and what should happen next."  `TaskPack` is machine-readable and schema-heavy; work log is human-readable and intentionally minimal.

### 3. Diagnostics ↔ Workflow Doctor

- **wiki**: `WikiLinter` checks internal wiki structure (orphan taskpacks, missing frontmatter, old snapshots).  `ReconcileEngine` checks source-hash drift.
- **workflow**: `workflow_doctor.py` checks required workflow files, local artifacts in git status, Markdown code fences, and CodeGraph availability.
- **Overlap**: Both run read-only diagnostics.  `workflow_doctor` focuses on repo-wide workflow readiness; `WikiLinter` focuses on `.cc-mini/wiki/` internal consistency.

### 4. Closeout / Review ↔ Review Packet + Rollback Helper

- **wiki**: `CloseoutStore` saves JSON+Markdown closeout records.  `PostEditGuard` does AST-level impact analysis after patch.
- **workflow**: `review_packet.py` builds compact review packets from git diff metadata.  `rollback_helper.py` prints safe rollback suggestions.  `commands.py` already wires `/close` to `CloseoutRecord`.
- **Overlap**: Both cover "review what just happened."  `PostEditGuard` is AST-centric and requires original contents; `review_packet` is git-diff-centric and needs no AST.

### 5. State Machine ↔ Workflow Next

- **wiki**: `flow_state.py` injects a rigid 4-state prompt (`PLAN` → `LOCATE` → `IMPLEMENT` → `VERIFY`) into the LLM system prompt.
- **workflow**: `workflow_next.py` infers a coarse external state (`blocked`, `needs_test_gate`, `needs_fresh_review`, `ready_to_commit`, `done`) from objective signals.
- **Overlap**: Both constrain what the agent should do next.  `flow_state` is prompt-level and LLM-enforced; `workflow_next` is signal-based and read-only.

---

## Recommendations

### Preserve (keep as-is)

| Item | Rationale |
|------|-----------|
| `flow_state.py` mode separation | `build_mode_system_prompt()` is the runtime boundary between `standard` and `wiki_strict`.  It is low-cost and keeps the two modes visibly separated. |
| `wiki/taskpack.py` dataclasses | `TaskPack`, `EditSpec`, `GoalStack`, `DeferredIssue`, `MicroForkNote` are referenced by `/prime`, `/plan`, and tests (`test_wiki_phase1.py`, `test_wiki_phase3.py`).  Removing them would break existing command surfaces. |
| `wiki/closeout.py` | `CloseoutRecord` / `CloseoutStore` are already consumed by `commands.py` (`/close`, `/milestone-review`).  This is the active closeout path. |
| `wiki/semantic_artifacts.py` | `SemanticArtifactStore` is tested in `test_wiki_phase3.py` and supports the derived/manual layer concept.  It is small and harmless. |
| `wiki/target_identity.py` | Used by `/prime`.  Keep until `/prime` is explicitly replaced. |

### Downgrade to Legacy / Future Work

| Item | Rationale | Suggested Future Path |
|------|-----------|----------------------|
| `knowledge/ingester.py` full ingestion | Self-hosted AST parsing and entity writing is maintenance-heavy.  CodeGraph or `rg` provide the same capability without a custom cache. | Replace with CodeIntel provider query + on-demand file read.  Retain `ChangedFileTracker` logic if still useful. |
| `knowledge/watcher.py` background observer | `watchdog` dependency + background thread adds complexity.  The `/digest --changed` surface can be triggered explicitly. | Remove background observer; keep `ChangedFileTracker` as an explicit accumulator if `/digest --changed` is kept. |
| `knowledge/dehydrator.py` RuntimeSnapshot | Overlaps with `core/dehydration.py` (`maybe_dehydrate_messages`) and `core/checkpoint.py`.  The snapshot format is wiki-specific and not consumed by the workflow path. | Consolidate into `core/checkpoint.py` or remove if `core/dehydration` covers the need. |
| `wiki/lint.py` | Internal wiki health checks are not on the active workflow path.  The repo already has `workflow_doctor` for readiness checks. | Deprecate; if wiki-internal health is ever needed, fold a minimal check into `workflow_doctor`. |
| `wiki/archive.py` | Auto-archiving is a later-phase convenience.  Manual `git clean` + `.gitignore` already handle local artifacts. | Mark as future work; do not wire into v1 commands. |
| `wiki/maintenance.py` auto-cleanup | Same rationale as archive.  The `dry_run` default is safe, but the surface is not essential for Phase 1. | Keep `project_artifact_maintenance()` view-only projection (already used by `/maintenance`); defer auto-cleanup. |
| `wiki/reconcile.py` `apply_action` | Reconcile actions (`RE_DIGEST`, `ARCHIVE`, `DELETE`) mutate the filesystem.  In v1, `/reconcile` is already view-only. | Keep `project_artifact_reconcile()` view-only projection (already used by `/reconcile`); remove or hide `apply_action` from v1 surface. |
| `wiki/post_edit_guard.py` AST impact analysis | AST-level diff is sophisticated but requires original contents, which are not always available.  `review_packet.py` + `test_selector.py` cover the "what changed and what to test" need with simpler inputs. | Keep as a later-phase optional surface; do not treat as the primary review path in v1. |
| `wiki/query_archive.py` | Not referenced by any active command or test. | Deprecate unless a later-phase command explicitly needs it. |

### Consolidate with New Workflow

| wiki component | workflow replacement / consolidation |
|----------------|--------------------------------------|
| `WikiIngester` entity scan | CodeIntel provider `status` + `files` queries |
| `ChangedFileTracker` | Could be absorbed into `workflow_test` or `test_selector` as "what changed since last check" |
| `WikiLinter` orphan checks | `workflow_doctor` could optionally check `.cc-mini/wiki/` structure |
| `PostEditGuard` impact analysis | `review_packet` (git diff) + `test_selector` (changed file → test mapping) |
| `TaskPackManager` persistence | Could be simplified to JSON-only; the Markdown index generation is redundant with `AGENTS.md` + `PROJECT_MAP.md` |
| `CloseoutStore` | Already the active path; no change needed |

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| `TaskPack` schema drift | Medium | `TaskPack` is used by `/prime` and `/plan`.  Any schema change must update `taskpack.py`, `commands.py`, and `test_wiki_phase1.py`. |
| `flow_state` prompt conflicts with `workflow_next` | Low | `flow_state` is prompt-only; `workflow_next` is read-only recommendation.  They can coexist as long as `workflow_next` does not silently override prompt constraints. |
| `.cc-mini/wiki/` directory continues to grow | Low | `archive.py` and `maintenance.py` exist but are not wired to auto-run.  Add a note to `workflow_doctor` warning if `.cc-mini/wiki/` is large. |
| Background watcher thread leaks | Low | `knowledge/watcher.py` uses `watchdog.observers.Observer`.  If the REPL exits uncleanly, the daemon thread should die, but this is untested. |
| Dual closeout paths | Medium | `commands.py` `/close` uses `wiki/closeout.py`.  No second closeout store exists in workflow, so this is currently safe.  Do not introduce a second one. |

---

## Suggested Next Steps (no new task numbers)

1. **Preserve the active surfaces**: `/scan`, `/prime`, `/plan` in `wiki_strict` mode; `/close`, `/milestone-review` in both modes.
2. **Do not expand wiki-specific storage**: Avoid adding new entity types to `.cc-mini/wiki/` unless they replace an existing one.
3. **Consolidate diagnostics**: If `workflow_doctor` is extended, consider adding a lightweight `.cc-mini/wiki/` size/orphan check rather than maintaining `WikiLinter` separately.
4. **Defer auto-maintenance**: Keep `/reconcile` and `/maintenance` as view-only projections.  Do not enable `apply_action` or auto-archive in v1.
5. **Document the overlap**: When future tasks modify `workflow_next` or `review_packet`, check whether the change makes a wiki module redundant and note it in the task log.
6. **Evaluate `knowledge/` deprecation after CodeIntel matures**: Once `CodeIntel Provider` v1 (Task 035–036) is stable and provides `files` + `query`, revisit whether `WikiIngester` can be replaced by on-demand CodeGraph queries.
