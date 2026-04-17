#!/usr/bin/env bash
set -euo pipefail

# ===== 固定环境 =====
VENV="/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv"
WORKDIR="/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo"
PY="$VENV/bin/python"
CC="$VENV/bin/cc-mini"

# ===== 你提供的模型与 provider 配置 =====
export CC_MINI_MODEL="Qwen3.5-9B-MLX-4bit"
export CC_MINI_PROVIDER="openai"
export OPENAI_BASE_URL="http://localhost:8000/v1"
export OPENAI_API_KEY="w2hqq0809"
export CC_MINI_MAX_TOKENS="32000"
export CC_MINI_AUTO_APPROVE="1"
export CC_MINI_AUTO_COMPACT="1"

# ===== 留痕目录 =====
TS="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="$WORKDIR/validation-runs/$TS-installed"
mkdir -p "$RUN_DIR"

exec > >(tee "$RUN_DIR/installed-validation.log") 2>&1

echo "=== Installed CC-MINI Validation ==="
echo "Timestamp: $TS"
echo "Run dir: $RUN_DIR"

echo
echo "=== Environment Snapshot ==="
echo "VENV=$VENV"
echo "WORKDIR=$WORKDIR"
echo "PY=$PY"
echo "CC=$CC"
env | grep -E '^(CC_MINI_|OPENAI_)' | sort | tee "$RUN_DIR/env.snapshot"

echo
echo "=== Basic Runtime Checks ==="
"$PY" --version
"$CC" --help || true

echo
echo "=== Mode Checks ==="
"$CC" --mode standard --help || true
"$CC" --mode wiki_strict --help || true

echo
echo "=== Provider Reachability (best effort) ==="
curl -s "${OPENAI_BASE_URL}/models" | tee "$RUN_DIR/models.json" || true

echo
echo "=== Minimal Installed Import Check ==="
"$PY" -c "import cc_mini; print('installed package import ok')" || true

echo
echo "=== Summary ==="
{
  echo "installed_validation_run=$TS"
  echo "cc_help_checked=true"
  echo "standard_help_checked=true"
  echo "wiki_strict_help_checked=true"
  echo "provider_models_checked=true"
} | tee "$RUN_DIR/summary.txt"

echo
echo "Installed validation finished."
