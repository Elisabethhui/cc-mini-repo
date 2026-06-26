# Migration Guide: Context-Bounded Workflow

This guide helps users migrate from the legacy wiki_strict / memory-bank / `.cc-mini` workflow to the new context-bounded workflow.

> **Do not delete your old data.** Back it up first. The migration is gradual and read-only.

---

## What Changed

| Before (legacy) | After (context-bounded) |
|-----------------|------------------------|
| `.cc-mini/wiki/` — entity cache, taskpacks, reports | `.ai-dev/` — workflow files, skills, templates, design docs |
| `memory-bank/` — session memory | `~/.mini-claude/` — KAIROS memory (unchanged) |
| `.cc-mini/skills/` — skills | `.ai-dev/skills/` — skills |
| `scripts/`, `manifests/`, `docs/wiki/` — build artifacts | Removed during project cleanup |
| Phase 1–6 wiki lifecycle with AST ingestion | Phase 1 bootstrap → scan → prime → plan; later phases deferred |
| `/init_build`, deep reconcile, auto-maintenance | `/workflow-status`, `/workflow-init`, `/workflow-doctor`, `/workflow-test` |

The legacy wiki_strict subsystem (`src/core/wiki/`, `src/core/knowledge/`) still exists in the codebase for backward compatibility, but its later-phase surfaces (patch, post-edit, auto-reconcile, auto-archive) are **deferred and view-only** in the current release.

---

## New Directory Structure

### Committed workflow files

These belong in version control and are created by `/workflow-init`:

| Path | Purpose |
|------|---------|
| `AGENTS.md` | Agent rules for this repository |
| `.ai-dev/README.md` | Overview of the `.ai-dev/` tree |
| `.ai-dev/WORKFLOW.md` | Context-bounded workflow description |
| `.ai-dev/PROJECT_MAP.md` | Compact navigation map |
| `.ai-dev/CODEGRAPH.md` | CodeGraph setup instructions |
| `.ai-dev/TESTING.md` | Testing registry and commands |
| `.ai-dev/skills/` | Reusable SKILL.md workflows |
| `.ai-dev/templates/` | Task templates |
| `.ai-dev/design/` | Design documents and reviews |

### Local-only runtime artifacts

These are **gitignored** and must not be committed:

| Path | Purpose |
|------|---------|
| `.ai-dev/tasks/` | Task cards and plans |
| `.ai-dev/context-packs/` | Generated context packs |
| `.ai-dev/worklogs/` | Work logs per task |
| `.ai-dev/checkpoints/` | Session checkpoints |
| `.ai-dev/tmp/` | Temporary files |
| `.codegraph/` | CodeGraph index |
| `.codebase-memory/` | Codebase memory cache |
| `CLAUDE.md` | Local agent instructions (gitignored by default) |

---

## Step-by-Step Migration

### 1. Back up your old data

```bash
# If you have an old .cc-mini/ directory with wiki entities or taskpacks
cp -r .cc-mini .cc-mini-backup-$(date +%Y%m%d)

# If you have an old memory-bank/
cp -r memory-bank memory-bank-backup-$(date +%Y%m%d)
```

### 2. Scaffold the new workflow files

Start the REPL and run the init command:

```bash
cc-mini
> /workflow-init
```

Or preview what it will create without writing:

```
> /workflow-init --dry-run
```

This creates the committed scaffold (`AGENTS.md`, `.ai-dev/*.md`, `.ai-dev/skills/`, `.ai-dev/templates/`) without touching your source code.

### 3. Verify the environment

```
> /workflow-status
```

Check that:
- Required files are present
- Local artifact paths are ignored
- Git is clean (or you understand the unstaged changes)

### 4. Run diagnostics

```
> /workflow-doctor
```

This checks:
- Required workflow files
- Whether local artifacts are tracked by git
- Markdown code fence consistency
- CodeGraph availability

### 5. Understand what is still available

The old commands still exist but their scope is reduced:

| Old command | Current status |
|-------------|---------------|
| `/scan` | Available — scans workspace for wiki entities |
| `/prime` | Available — generates TaskPack from digest |
| `/plan` | Available — structured plan in wiki_strict mode |
| `/reconcile` | **View-only** — projection, no file mutations |
| `/maintenance` | **View-only** — projection, no file mutations |
| `/post_edit` | Later-phase demo/stub, not part of Phase 1 |
| `/init_build` | Legacy, not part of Phase 1 |

---

## Old Directories and Files

### `.cc-mini/`

Previously used for:
- `.cc-mini/wiki/entities/` — AST-based entity cache
- `.cc-mini/wiki/taskpacks/` — TaskPack JSON files
- `.cc-mini/wiki/reports/` — closeout, deferred issues, micro-forks
- `.cc-mini/wiki/snapshots/` — runtime snapshots
- `.cc-mini/drift_log.json` — drift tracker

**Current status:** The `.cc-mini/` directory is no longer created by `/workflow-init`.  If you have an existing `.cc-mini/` from an earlier version, it is safe to keep it as a backup, but new workflow commands do not write to it.  The old wiki ingestion and watcher (`src/core/knowledge/`) are still present but considered legacy.

### `memory-bank/`

Previously used for cross-session memory.  The KAIROS memory system now stores data in `~/.mini-claude/` by default.  If you have a local `memory-bank/`, back it up; it is no longer the active memory path.

### `scripts/`, `manifests/`, `docs/wiki/`

These directories were removed during project cleanup.  They are listed in `.gitignore`.  If you have local copies, back them up before deleting.

---

## CodeGraph Is Optional

CodeGraph is not required for the context-bounded workflow.

- **When available:** `/workflow-test` and future `/codeintel-query` use CodeGraph for compact code queries.
- **When unavailable:** The system falls back to `rg` (ripgrep) and manual file reading.
- **Setup (optional):**
  ```bash
  codegraph init
  codegraph status
  ```

See `.ai-dev/CODEGRAPH.md` for daily use commands.

---

## Compatibility Notes

- **Not all old wiki_strict产物 are migrated automatically.**  TaskPacks, entity files, and closeout records in `.cc-mini/wiki/` remain where they are.  If you need them, access them manually or back them up.
- **The `wiki_strict` mode still exists** as a runtime mode (`cc-mini --mode wiki_strict`), but its Phase 1 surface is the active path.  Later-phase features (auto-patch, auto-reconcile, auto-archive) are explicitly deferred.
- **`standard` mode is unchanged** and remains the default general-purpose REPL.
- **Skills migrated** from `.cc-mini/skills/` to `.ai-dev/skills/`.  If you had custom skills in the old path, move them to the new path.

---

## Quick Reference

| Need | Command |
|------|---------|
| Check workflow readiness | `/workflow-status` |
| Create missing scaffold | `/workflow-init` |
| Run diagnostics | `/workflow-doctor` |
| Get test recommendations | `/workflow-test` |
| List all commands | `/help` |
| List skills | `/skills` |

For full workflow documentation, see `docs/workflow.md`.
