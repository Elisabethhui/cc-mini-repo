#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"

mkdir -p "$ROOT/.project-ops/project-definition"
mkdir -p "$ROOT/.project-ops/workflow"
mkdir -p "$ROOT/.project-ops/state"
mkdir -p "$ROOT/.project-ops/templates"
mkdir -p "$ROOT/.project-ops/rules"
mkdir -p "$ROOT/.project-ops/runs"
mkdir -p "$ROOT/.project-ops/archive"
mkdir -p "$ROOT/.project-ops/tmp"
mkdir -p "$ROOT/.project-ops/failed"
mkdir -p "$ROOT/.claude"
mkdir -p "$ROOT/scripts/agent"

echo "[info] created target directories"

if [ -d "$ROOT/memory-bank" ]; then
  [ -f "$ROOT/memory-bank/progress.md" ] && cp "$ROOT/memory-bank/progress.md" "$ROOT/.project-ops/state/progress.md"
  [ -f "$ROOT/memory-bank/findings.md" ] && cp "$ROOT/memory-bank/findings.md" "$ROOT/.project-ops/state/findings.md"
  [ -f "$ROOT/memory-bank/decisions.md" ] && cp "$ROOT/memory-bank/decisions.md" "$ROOT/.project-ops/state/decisions.md"
  [ -f "$ROOT/memory-bank/architecture.md" ] && cp "$ROOT/memory-bank/architecture.md" "$ROOT/.project-ops/state/architecture.md"
  [ -f "$ROOT/memory-bank/current-task.md" ] && cp "$ROOT/memory-bank/current-task.md" "$ROOT/.project-ops/workflow/current-task.md"
fi

echo "[info] best-effort migration from memory-bank done"
echo "[next] manually review .project-ops/ content before continuing"
