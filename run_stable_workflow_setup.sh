#!/usr/bin/env bash
set -eu

# Stable setup runner for the context-bounded workflow task files.
# Run this from the repository root after placing all generator scripts there.
#
# Required generator scripts:
# - generate_task_000_025_files.sh
# - generate_task_026_030_files.sh
# - generate_task_031_035_files.sh
# - generate_task_036_040_files.sh
# - generate_task_041_045_files.sh
# - generate_task_046_050_files.sh

require_file() {
  if [ ! -f "$1" ]; then
    echo "Missing required script: $1"
    exit 1
  fi
}

commit_if_changed() {
  message="$1"
  shift

  git add "$@"

  if git diff --cached --quiet; then
    echo "No staged changes for: $message"
    git restore --staged "$@" >/dev/null 2>&1 || true
    return 0
  fi

  git commit -m "$message"
}

echo "== Context-bounded workflow stable setup =="

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "This directory is not a git repository."
  exit 1
fi

if [ -n "$(git status --short)" ]; then
  echo "Working tree is not clean. Please commit/stash/review existing changes first."
  echo
  git status --short
  exit 1
fi

require_file "generate_task_000_025_files.sh"
require_file "generate_task_026_030_files.sh"
require_file "generate_task_031_035_files.sh"
require_file "generate_task_036_040_files.sh"
require_file "generate_task_041_045_files.sh"
require_file "generate_task_046_050_files.sh"

echo "== Step 1/6: Generate tasks 000-025 =="
bash generate_task_000_025_files.sh
commit_if_changed "Regenerate context-bounded workflow tasks 000-025" AGENTS.md .gitignore .ai-dev

echo "== Step 2/6: Generate tasks 026-030 =="
bash generate_task_026_030_files.sh
commit_if_changed "Add workflow review init doctor codeintel and context pack plans" .ai-dev

echo "== Step 3/6: Generate tasks 031-035 =="
bash generate_task_031_035_files.sh
commit_if_changed "Add workflow init doctor and codeintel implementation tasks" .ai-dev

echo "== Step 4/6: Generate tasks 036-040 =="
bash generate_task_036_040_files.sh
commit_if_changed "Add codeintel test selector review packet and worklog tasks" .ai-dev

echo "== Step 5/6: Generate tasks 041-045 =="
bash generate_task_041_045_files.sh
commit_if_changed "Add rollback next state wiki strict prompt and docs tasks" .ai-dev

echo "== Step 6/6: Generate tasks 046-050 =="
bash generate_task_046_050_files.sh
commit_if_changed "Add migration config e2e final review and merge tasks" .ai-dev

echo "== Final status =="
git status --short
echo
echo "Recent commits:"
git log --oneline -8
echo
echo "Done. If git status is clean, proceed with task-021 workflow smoke review execution."
