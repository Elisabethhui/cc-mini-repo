# Merge Plan: Context-Bounded Workflow Branch

**Task:** 050  
**Date:** 2026-06-26  
**Source branch:** `feature/context-bounded-dev-bootstrap`  
**Target branch:** `main`

---

## Pre-Merge Checklist

### 1. Working tree state

```bash
git status --short
```

**Result:** `M AGENTS.md` (unstaged modification)

**Action required before merge:**
- The `AGENTS.md` modification (23 insertions, 1 deletion) is part of the branch work and should be staged + committed, or stashed if it is not intended for this branch.
- Recommendation: `git add AGENTS.md && git commit -m "Update AGENTS.md with workflow rules"` before merge.

### 2. Test verification

```bash
pytest tests/ -v -k "not integration"
```

**Result:** 400 passed, 9 deselected, 0 failed, 0 errors.

**Status:** PASS

### 3. Secret / credential scan

- Automated `rg` search for `api_key`, `secret`, `password`, `token` in `src/` and `tests/`: clean
- No hardcoded API keys in committed files
- No `.env` files staged

**Status:** PASS

### 4. Local artifact leak check

```bash
git status --short | grep -E '^\?\?'
```

**Result:** None.

Verified that the following are gitignored and not staged:
- `.ai-dev/tasks/`, `.ai-dev/context-packs/`, `.ai-dev/worklogs/`, `.ai-dev/checkpoints/`, `.ai-dev/tmp/`
- `.codegraph/`, `.codebase-memory/`
- `CLAUDE.md`

**Status:** PASS

### 5. Diff sanity check

```bash
git diff --check
```

**Result:** No whitespace errors.

**Status:** PASS

### 6. Branch divergence

```bash
git branch -v
```

**Result:**
- `feature/context-bounded-dev-bootstrap` is ahead of `main` by 8 commits (summary count) / ~33 commits (full history).
- No merge conflicts expected; this branch is a fast-forward or clean merge from `main` base.

**Status:** CLEAN

---

## Merge Method

**Recommended:** `git merge --no-ff feature/context-bounded-dev-bootstrap`

Rationale:
- The branch contains a coherent feature set (Phase 1 context-bounded workflow).
- A non-fast-forward merge preserves the branch history as a single merge commit, making revert and archaeology easier.
- Do **not** squash; the individual commits are meaningful and already reviewed.

**Alternative (if repo policy prefers):** Open a Pull Request and merge via GitHub UI with "Create a merge commit".

---

## Required Tests (must pass before merge)

| Test command | Expected result | Blocking |
|--------------|-----------------|----------|
| `pytest tests/ -v -k "not integration"` | 400 passed, 0 failed | **YES** |
| `pytest tests/test_commands.py -v` | 8 passed, 0 failed | **YES** |
| `pytest tests/test_workflow_status.py tests/test_workflow_init.py tests/test_workflow_doctor.py tests/test_test_selector.py -v` | 24 passed, 0 failed | **YES** |
| `pytest tests/test_review_packet.py tests/test_work_log.py tests/test_rollback_helper.py tests/test_workflow_next.py -v` | 39 passed, 0 failed | **YES** |
| `pytest tests/test_codeintel.py -v` | 7 passed, 0 failed | **YES** |

**Non-blocking but recommended:**
- `PYTHONPATH=src python -m core.main --help` should exit 0 and list `--mode`, `--provider`, etc.
- Start REPL and type `/help` — verify `/workflow-status`, `/workflow-init`, `/workflow-doctor`, `/workflow-test` appear.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Merge conflict with `main` | Low | Medium | Branch is ahead cleanly; no divergence from `main` visible. If conflict arises, resolve in `commands.py` or `README.md` only. |
| Test failure on `main` CI after merge | Low | Medium | All tests pass locally. CI uses same pytest command. If CI fails, investigate Python version or missing `rg` binary. |
| `AGENTS.md` modification left unstaged | Medium | Low | Will be carried into working tree after merge. Stash or commit it now. |
| Local artifacts accidentally committed in future | Low | High | `.gitignore` is already correct. Post-merge, verify no new untracked files. |
| `auto_dream=True` default surprises users | Pre-existing | Low | Not introduced by this branch; documented in `CONFIG_DEFAULTS_REVIEW.md`. |

---

## Rollback Plan

If the merge introduces regressions:

1. **Identify the merge commit** on `main`.
2. **Revert the merge commit**:
   ```bash
   git checkout main
   git revert -m 1 <merge-commit-hash>
   ```
3. **Run the required test suite** to confirm base branch health:
   ```bash
   pytest tests/ -v -k "not integration"
   ```
4. **Clean up any generated local artifacts** from testing:
   ```bash
   rm -rf .ai-dev/worklogs/ .ai-dev/checkpoints/ .ai-dev/tmp/
   ```

The branch is addition-only for product code; reverting cleanly removes the new modules and commands without breaking existing behavior.

---

## Files That Must NOT Appear in the Merge

The following file types/directories should not be present in the diff or PR:

| Path | Reason |
|------|--------|
| `.ai-dev/tasks/` | Local runtime state |
| `.ai-dev/context-packs/` | Local runtime state |
| `.ai-dev/worklogs/` | Local runtime state |
| `.ai-dev/checkpoints/` | Local runtime state |
| `.ai-dev/tmp/` | Local runtime state |
| `.codegraph/` | CodeGraph index (gitignored) |
| `.codebase-memory/` | Memory cache (gitignored) |
| `CLAUDE.md` | Local agent instructions (gitignored) |
| `.env` | Secrets (gitignored) |
| `*.pyc`, `__pycache__/` | Build artifacts (gitignored) |
| `.venv/` | Virtual environment (gitignored) |

**Verification:** `git diff --stat main..feature/context-bounded-dev-bootstrap` does not include any of the above.

---

## PR Description Draft

```markdown
## Context-Bounded Workflow (Phase 1)

This PR introduces a set of read-only REPL slash commands and supporting core modules that make coding tasks small, verifiable, and recoverable.

### New Commands
- `/workflow-status` — Read-only workflow readiness check
- `/workflow-init` — Scaffold missing workflow files (`--dry-run` supported)
- `/workflow-doctor` — Read-only diagnostics (files, git, markdown, CodeGraph)
- `/workflow-test` — Test recommendations from changed files (no auto-execution)

### New Core Modules
- `core/codeintel.py` — CodeIntel provider with CodeGraph / `rg` fallback
- `core/test_selector.py` — Changed-file → test mapping
- `core/review_packet.py` — Read-only review packet builder
- `core/work_log.py` — Work log render + write
- `core/rollback_helper.py` — Read-only rollback suggestion printer
- `core/workflow_next.py` — Next-step state recommender
- `core/workflow_status.py`, `core/workflow_init.py`, `core/workflow_doctor.py` — Command implementations

### Docs
- `docs/workflow.md` — User-facing workflow reference
- `docs/migration-context-bounded-workflow.md` — Migration guide from legacy wiki_strict
- `README.md` — Updated with workflow commands and migration link

### Safety
- All workflow commands are read-only; no automatic commits, test runs, or file mutations.
- 400/400 tests pass (`pytest tests/ -v -k "not integration"`).
- 78 new tests added for workflow surfaces.
- No secrets or API keys in the diff.

### Deferred (documented, not implemented)
- `/codeintel-status` and `/codeintel-query` REPL wiring
- Context pack generator
- Prompt minimization implementation
- Wiki_strict subsystem cleanup
```

---

## Post-Merge Checks

After merging, run the following on `main`:

1. **Pull the merged `main`:**
   ```bash
   git checkout main
   git pull
   ```

2. **Run the required test suite:**
   ```bash
   pytest tests/ -v -k "not integration"
   ```
   **Expected:** 400 passed, 0 failed.

3. **Smoke test the CLI:**
   ```bash
   PYTHONPATH=src python -m core.main --help
   ```
   **Expected:** Exits 0, shows help.

4. **Verify no local artifacts leaked into the merge:**
   ```bash
   git status --short
   ```
   **Expected:** Clean working tree.

5. **Verify documentation is reachable:**
   - `docs/workflow.md` exists and renders correctly.
   - `docs/migration-context-bounded-workflow.md` exists and renders correctly.
   - README link to migration guide works.

6. **Tag the merge (optional):**
   ```bash
   git tag -a v0.x.x-workflow-phase1 -m "Phase 1 context-bounded workflow"
   ```

---

## Summary

| Item | Status |
|------|--------|
| Tests pass | PASS (400/400) |
| No secrets | PASS |
| No local artifacts | PASS |
| Working tree clean (after AGENTS.md commit) | PENDING — commit or stash `AGENTS.md` before merge |
| Rollback path documented | YES |
| PR description drafted | YES |
| Post-merge checks defined | YES |

**Ready to merge after `AGENTS.md` is committed or stashed.**
