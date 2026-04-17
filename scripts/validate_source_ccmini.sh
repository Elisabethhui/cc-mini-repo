#!/usr/bin/env bash
set -euo pipefail

# ===== 固定环境 =====
VENV="/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv"
WORKDIR="/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo"
PY="$VENV/bin/python"

# ===== 与已安装测试保持一致 =====
export CC_MINI_MODEL="Qwen3.5-9B-MLX-4bit"
export CC_MINI_PROVIDER="openai"
export OPENAI_BASE_URL="http://localhost:8000/v1"
export OPENAI_API_KEY="w2hqq0809"
export CC_MINI_MAX_TOKENS="32000"
export CC_MINI_AUTO_APPROVE="1"
export CC_MINI_AUTO_COMPACT="1"

TS="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="$WORKDIR/validation-runs/$TS-source"
mkdir -p "$RUN_DIR"

exec > >(tee "$RUN_DIR/source-validation.log") 2>&1

echo "=== Source CC-MINI Validation ==="
echo "Timestamp: $TS"
echo "Run dir: $RUN_DIR"

cd "$WORKDIR"

echo
echo "=== Environment Snapshot ==="
echo "PY=$PY"
env | grep -E '^(CC_MINI_|OPENAI_)' | sort | tee "$RUN_DIR/env.snapshot"

echo
echo "=== Runtime Validation ==="
PYTHONPATH=src "$PY" --version
PYTHONPATH=src "$PY" -c "from core.config import RunMode; print('runtime ok')"

echo
echo "=== Core Module Imports ==="
PYTHONPATH=src "$PY" -c "from core.config import RunMode; print('config ok')"
PYTHONPATH=src "$PY" -c "from core.token_budget import TokenBudgetManager; print('token_budget ok')"
PYTHONPATH=src "$PY" -c "from core.flow_state import FlowState; print('flow_state ok')"
PYTHONPATH=src "$PY" -c "from core.coordinator import *; print('coordinator ok')"
PYTHONPATH=src "$PY" -c "from core.checkpoint import CheckpointManager; print('checkpoint ok')"
PYTHONPATH=src "$PY" -c "import core.dehydration as d; print('dehydration ok')"
PYTHONPATH=src "$PY" -c "from core.knowledge.ingester import WikiIngester; print('ingester ok')"
PYTHONPATH=src "$PY" -c "from core.knowledge.watcher import WikiDebounceWatcher; print('watcher ok')"
PYTHONPATH=src "$PY" -c "from core.wiki.reconcile import *; print('reconcile ok')"
PYTHONPATH=src "$PY" -c "from core.wiki.archive import *; print('archive ok')"
PYTHONPATH=src "$PY" -c "from core.wiki.query_archive import *; print('query_archive ok')"
PYTHONPATH=src "$PY" -c "from core.wiki.lint import *; print('lint ok')"
PYTHONPATH=src "$PY" -c "from core.wiki.maintenance import *; print('maintenance ok')"

echo
echo "=== Pytest Regression ==="
PYTHONPATH=src "$PY" -m pytest tests/ -q | tee "$RUN_DIR/pytest.log"

echo
echo "=== Summary ==="
{
  echo "source_validation_run=$TS"
  echo "runtime_ok=true"
  echo "core_imports_ok=true"
  echo "pytest_checked=true"
  echo "next_step=use current-task package to validate analysis/plan/patch/maintenance chain"
} | tee "$RUN_DIR/summary.txt"

echo
echo "Source validation finished."
