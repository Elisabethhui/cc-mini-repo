#!/bin/bash
#
# Init Build Validation Script
# Phase 6-A / Module 2
#

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../../.." && pwd)"
PYTHON="/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python"
VALIDATION_DIR="${PROJECT_ROOT}/validation-runs/$(date +%Y%m%d-%H%M%S)-phase6-module-2"

# Create validation directory
mkdir -p "${VALIDATION_DIR}"
SUMMARY_FILE="${VALIDATION_DIR}/summary.txt"

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
    echo "[INFO] $1" >> "${SUMMARY_FILE}"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    echo "[PASS] $1" >> "${SUMMARY_FILE}"
    ((TESTS_PASSED++)) || true
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    echo "[FAIL] $1" >> "${SUMMARY_FILE}"
    ((TESTS_FAILED++)) || true
}

# Initialize summary
echo "Init Build Validation Report" > "${SUMMARY_FILE}"
echo "============================" >> "${SUMMARY_FILE}"
echo "Timestamp: $(date)" >> "${SUMMARY_FILE}"
echo "" >> "${SUMMARY_FILE}"

cd "${PROJECT_ROOT}"

# Test 1: Command registration test
log_info "Test 1: /init_build command is registered"
if PYTHONPATH=src "${PYTHON}" -c "
from core.commands import _HANDLERS
assert 'init_build' in _HANDLERS, 'init_build not in handlers'
print('✓ init_build command registered')
" > /dev/null 2>&1; then
    log_pass "init_build command is registered"
else
    log_fail "init_build command not registered"
fi

# Test 2: Init build creates wiki structure
log_info "Test 2: Init build creates wiki structure"
TEST_WORKSPACE="${VALIDATION_DIR}/test_workspace"
mkdir -p "${TEST_WORKSPACE}"

# Create a simple Python file
cat > "${TEST_WORKSPACE}/test_module.py" << 'EOF'
def hello():
    '''Say hello.'''
    return 'hello'

class TestClass:
    '''Test class.'''
    pass
EOF

cd "${TEST_WORKSPACE}"

# Run init_build via Python
PYTHONPATH="${PROJECT_ROOT}/src" "${PYTHON}" -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}/src')
from core.commands import _cmd_init_build
from unittest.mock import MagicMock

ctx = MagicMock()
ctx.console = MagicMock()

# Run init_build
_cmd_init_build(ctx, '')
" 2>&1 || true

# Check that wiki structure was created
if [ -d "${TEST_WORKSPACE}/.cc-mini/wiki" ] && \
   [ -f "${TEST_WORKSPACE}/.cc-mini/wiki/index.md" ] && \
   [ -d "${TEST_WORKSPACE}/.cc-mini/wiki/entities" ]; then
    log_pass "Init build creates wiki structure"
else
    log_fail "Init build wiki structure creation failed"
fi

# Test 3: Init build generates entities
log_info "Test 3: Init build generates entities"
cd "${TEST_WORKSPACE}"

if [ -f "${TEST_WORKSPACE}/.cc-mini/wiki/entities/test_module.py.md" ]; then
    log_pass "Init build generates entity files"
else
    log_fail "Init build did not generate entity files"
fi

# Test 4: Init build populates index.md
log_info "Test 4: Init build populates index.md"
if [ -s "${TEST_WORKSPACE}/.cc-mini/wiki/index.md" ]; then
    log_pass "index.md is populated"
else
    log_fail "index.md is empty or not populated"
fi

# Test 5: Command uses existing scan/digest capabilities
log_info "Test 5: Command reuses scan/digest capabilities"
if grep -q "WikiIngester" "/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/src/core/commands.py" && \
   grep -q "ingest_all" "/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/src/core/commands.py"; then
    log_pass "Command reuses existing ingest capabilities"
else
    log_fail "Command does not reuse existing capabilities"
fi

# Test 6: Help text is descriptive
log_info "Test 6: Help text is descriptive"
if grep -q "Initialize wiki base" "/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/src/core/commands.py"; then
    log_pass "Help text is descriptive"
else
    log_fail "Help text not found"
fi

# Summary
echo ""
echo "============================" >> "${SUMMARY_FILE}"
echo "Tests Passed: ${TESTS_PASSED}" >> "${SUMMARY_FILE}"
echo "Tests Failed: ${TESTS_FAILED}" >> "${SUMMARY_FILE}"
echo "============================" >> "${SUMMARY_FILE}"

if [ ${TESTS_FAILED} -eq 0 ]; then
    echo ""
    echo "STATUS: PASS" >> "${SUMMARY_FILE}"
    echo -e "${GREEN}============================${NC}"
    echo -e "${GREEN}All tests passed!${NC}"
    echo -e "${GREEN}============================${NC}"
    echo ""
    echo "Summary: ${SUMMARY_FILE}"
    exit 0
else
    echo ""
    echo "STATUS: FAIL" >> "${SUMMARY_FILE}"
    echo -e "${RED}============================${NC}"
    echo -e "${RED}Some tests failed!${NC}"
    echo -e "${RED}============================${NC}"
    echo ""
    echo "Summary: ${SUMMARY_FILE}"
    exit 1
fi
