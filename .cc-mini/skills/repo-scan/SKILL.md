---
name: repo-scan
description: Pre-scan the current repository, build a project map, and initialize manifests for later reading skills
context: fork
allowed-tools: Bash, Read, Glob, Grep, Write
arguments: [optional repo path]
---

# Repo Scan

You are performing only a repository pre-scan task.

## Goal
Build a lightweight map of the current project without deeply reading many source files.

## Constraints
- Do not deeply analyze code logic in this skill.
- Do not read more than 5 source files.
- Prefer Bash, Glob, and Grep over broad Read calls.
- Skip generated, cache, dependency, build, binary, and vendor directories.
- All file paths written into manifests must be repository-relative paths.
- When calling Read, always resolve paths to absolute paths rooted at the target repo.

## Required tasks
1. Resolve the repository root.
2. Create `./code-reading-notes/` and `./code-reading-notes/00_repo_scan/` if missing.
3. Run the repository snapshot script.
4. Identify:
   - top-level directories
   - likely entry files
   - likely configuration files
   - likely core runtime files
   - likely module groups
5. Create:
   - `./code-reading-notes/00_repo_scan/repo_snapshot.json`
   - `./code-reading-notes/00_repo_scan/repo_overview.md`
   - `./code-reading-notes/00_repo_scan/file_manifest.json`
   - `./code-reading-notes/00_repo_scan/reading_order.md`
   - `./code-reading-notes/00_repo_scan/module_candidates.json`
   - `./code-reading-notes/manifest.json`
   - `./code-reading-notes/TODO.md`
   - `./code-reading-notes/progress.md`

## Output requirements
`repo_overview.md` must explain:
- what the repository likely does
- which files should be read first
- which directories are likely core vs peripheral
- what the next best skill is

## Stop condition
Stop after scan artifacts and manifests are written.
Do not produce file-level or module-level deep summaries here.
