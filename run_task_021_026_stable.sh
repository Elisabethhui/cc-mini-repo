#!/usr/bin/env bash
set -eu

# Stable runner for tasks 021-026.
#
# Usage:
#   bash run_task_021_026_stable.sh prepare
#   bash run_task_021_026_stable.sh closeout
#
# prepare:
#   - runs task-021 workflow smoke checks
#   - creates local ignored artifacts for task-021, task-022, task-023
#   - copies task-024 and task-025 templates into .ai-dev/tasks/
#   - creates a handoff prompt for implementing task-024
#
# closeout:
#   - runs task-026 checks after task-024/025 product implementation
#   - runs map sync when CodeGraph is available
#   - runs targeted tests when matching test files exist
#   - writes a local worklog

mode="${1:-prepare}"

mkdir -p .ai-dev/tasks
mkdir -p .ai-dev/context-packs
mkdir -p .ai-dev/worklogs
mkdir -p .ai-dev/tmp

now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

append_cmd_output() {
  log_file="$1"
  title="$2"
  shift 2

  {
    echo
    echo "### $title"
    echo
    echo '```text'
    "$@" 2>&1 || true
    echo '```'
  } >> "$log_file"
}

check_ignore() {
  path="$1"
  git check-ignore "$path" >/dev/null 2>&1
}

copy_if_exists() {
  src="$1"
  dst="$2"
  if [ -f "$src" ]; then
    cp "$src" "$dst"
  else
    echo "Missing template: $src" >&2
    return 1
  fi
}

run_prepare() {
  echo "== task-021: workflow smoke review execution =="

  smoke_log=".ai-dev/worklogs/task-021-workflow-smoke-review.md"
  {
    echo "# Workflow Smoke Review Execution: task-021"
    echo
    echo "Generated: $(now_utc)"
    echo
    echo "## Decision"
    echo
    echo "pending"
    echo
    echo "## Checks"
  } > "$smoke_log"

  append_cmd_output "$smoke_log" "git status --short" git status --short
  append_cmd_output "$smoke_log" "find .ai-dev -maxdepth 3 -type f" find .ai-dev -maxdepth 3 -type f
  append_cmd_output "$smoke_log" "git diff --check" git diff --check

  {
    echo
    echo "## Ignore Checks"
    echo
  } >> "$smoke_log"

  for p in \
    ".ai-dev/tasks/example.md" \
    ".ai-dev/context-packs/example.md" \
    ".ai-dev/worklogs/example.md" \
    ".ai-dev/checkpoints/example.md" \
    ".ai-dev/tmp/example.md" \
    ".codegraph/example.db" \
    ".codebase-memory/example.db"
  do
    if check_ignore "$p"; then
      echo "- OK ignored: \`$p\`" >> "$smoke_log"
    else
      echo "- FAIL not ignored: \`$p\`" >> "$smoke_log"
    fi
  done

  {
    echo
    echo "## Markdown Fence Check"
    echo
  } >> "$smoke_log"

  python3 - <<'PY' >> "$smoke_log" 2>&1 || true
from pathlib import Path
paths = [Path("AGENTS.md"), Path(".ai-dev/WORKFLOW.md")]
paths += list(Path(".ai-dev/skills").glob("*/SKILL.md"))
paths += list(Path(".ai-dev/templates").glob("*.md"))
paths += list(Path(".ai-dev/design").glob("*.md"))
bad = []
for path in paths:
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    count = text.count("```")
    if count % 2:
        bad.append((str(path), count))
if bad:
    print("Unbalanced fenced code blocks:")
    for path, count in bad:
        print(f"- {path}: {count}")
else:
    print("OK: fenced code blocks appear balanced.")
PY

  echo "Wrote $smoke_log"

  echo "== task-022: first dry run execution =="

  dry_run=".ai-dev/tasks/task-022-first-dry-run.md"
  if [ -f ".ai-dev/templates/FIRST_DRY_RUN_EXECUTION.md" ]; then
    cp ".ai-dev/templates/FIRST_DRY_RUN_EXECUTION.md" "$dry_run"
  else
    cat > "$dry_run" <<'EOF'
# First Dry Run Execution: task-022

## Dry Run Goal

Use the workflow to answer this read-only question:

"How would cc-mini implement a read-only `workflow status` command?"
EOF
  fi

  dry_log=".ai-dev/worklogs/task-022-first-dry-run.md"
  {
    echo "# First Dry Run Work Log: task-022"
    echo
    echo "Generated: $(now_utc)"
    echo
    echo "## Goal"
    echo
    echo "Read-only dry run for implementing \`cc-mini workflow status\`."
  } > "$dry_log"

  append_cmd_output "$dry_log" "rg workflow/status/commands anchors" rg -n "workflow|status|commands|argparse|slash" src tests .ai-dev

  if has_cmd codegraph; then
    append_cmd_output "$dry_log" "codegraph status" codegraph status
    append_cmd_output "$dry_log" "codegraph query workflow" codegraph query workflow
    append_cmd_output "$dry_log" "codegraph query status" codegraph query status
    append_cmd_output "$dry_log" "codegraph query commands" codegraph query commands
  else
    {
      echo
      echo "## CodeGraph"
      echo
      echo "CodeGraph unavailable; dry run used rg fallback."
    } >> "$dry_log"
  fi

  echo "Wrote $dry_run"
  echo "Wrote $dry_log"

  echo "== task-023: workflow status plan review =="

  plan_review=".ai-dev/worklogs/task-023-workflow-status-plan-review.md"
  {
    echo "# Workflow Status Plan Review: task-023"
    echo
    echo "Generated: $(now_utc)"
    echo
    echo "## Plan File"
    echo
    echo "- .ai-dev/design/WORKFLOW_STATUS_PLAN.md"
    echo
    echo "## Decision"
    echo
    echo "ready-for-task-024 if plan file exists and working tree has no unrelated dirty product files."
    echo
    echo "## Next"
    echo
    echo "- Use .ai-dev/tasks/task-024-workflow-status-core.md as the implementation task."
  } > "$plan_review"

  echo "Wrote $plan_review"

  echo "== prepare task-024 and task-025 local task files =="

  copy_if_exists ".ai-dev/templates/TASK_024_WORKFLOW_STATUS_CORE.md" ".ai-dev/tasks/task-024-workflow-status-core.md"
  copy_if_exists ".ai-dev/templates/TASK_025_WORKFLOW_STATUS_COMMAND.md" ".ai-dev/tasks/task-025-workflow-status-command.md"

  handoff=".ai-dev/tmp/task-024-handoff-prompt.md"
  cat > "$handoff" <<'EOF'
# Handoff Prompt: task-024

Use the context-bounded workflow.

Read:

1. `AGENTS.md`
2. `.ai-dev/WORKFLOW.md`
3. `.ai-dev/PROJECT_MAP.md`
4. `.ai-dev/tasks/task-024-workflow-status-core.md`
5. `.ai-dev/TESTING.md`

Goal:

Implement the core read-only workflow status logic for `cc-mini workflow status`.

Hard rules:

- Do not implement workflow init.
- Do not require CodeGraph.
- Do not mutate `.ai-dev/` at runtime.
- Keep edits limited to the task.
- Add targeted tests.
- After implementation, run map-sync/test-gate/review closeout.
EOF

  echo "Wrote .ai-dev/tasks/task-024-workflow-status-core.md"
  echo "Wrote .ai-dev/tasks/task-025-workflow-status-command.md"
  echo "Wrote $handoff"

  echo
  echo "Prepare complete."
  echo "Next human action:"
  echo "  Give .ai-dev/tmp/task-024-handoff-prompt.md to your coding agent, or ask it to implement task-024."
  echo
  echo "Reminder: .ai-dev/tasks, .ai-dev/worklogs, and .ai-dev/tmp are local ignored artifacts."
}

run_closeout() {
  echo "== task-026: closeout =="

  closeout=".ai-dev/worklogs/task-026-workflow-status-closeout.md"
  {
    echo "# Workflow Status Closeout: task-026"
    echo
    echo "Generated: $(now_utc)"
    echo
    echo "## Git State"
  } > "$closeout"

  append_cmd_output "$closeout" "git status --short" git status --short
  append_cmd_output "$closeout" "git diff --stat" git diff --stat
  append_cmd_output "$closeout" "git diff --name-only" git diff --name-only

  {
    echo
    echo "## Map Sync"
    echo
  } >> "$closeout"

  if has_cmd codegraph; then
    append_cmd_output "$closeout" "codegraph sync" codegraph sync
    append_cmd_output "$closeout" "codegraph status" codegraph status
    append_cmd_output "$closeout" "codegraph affected tests" sh -c 'git diff --name-only | codegraph affected --stdin --quiet'
  else
    echo "CodeGraph unavailable; use manual test mapping from .ai-dev/TESTING.md." >> "$closeout"
  fi

  {
    echo
    echo "## Targeted Tests"
    echo
  } >> "$closeout"

  if [ -f "tests/test_workflow_status.py" ]; then
    append_cmd_output "$closeout" "pytest tests/test_workflow_status.py -v" pytest tests/test_workflow_status.py -v
  else
    echo "- SKIP: tests/test_workflow_status.py not found" >> "$closeout"
  fi

  if [ -f "tests/test_commands.py" ]; then
    append_cmd_output "$closeout" "pytest tests/test_commands.py -v" pytest tests/test_commands.py -v
  else
    echo "- SKIP: tests/test_commands.py not found" >> "$closeout"
  fi

  {
    echo
    echo "## Review Checklist"
    echo
    echo "- [ ] stayed inside task scope"
    echo "- [ ] product tests passed or failures classified"
    echo "- [ ] no local artifacts staged"
    echo "- [ ] no secrets"
    echo "- [ ] rollback path clear"
    echo
    echo "## Suggested Next"
    echo
    echo "If tests pass and diff is scoped, run fresh-review/review-rollback and commit product changes."
  } >> "$closeout"

  echo "Wrote $closeout"
}

case "$mode" in
  prepare)
    run_prepare
    ;;
  closeout)
    run_closeout
    ;;
  *)
    echo "Unknown mode: $mode"
    echo "Usage: bash run_task_021_026_stable.sh prepare|closeout"
    exit 1
    ;;
esac
