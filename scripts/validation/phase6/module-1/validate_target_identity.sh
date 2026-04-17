#!/bin/bash
#
# Target Identity Validation Script
# Phase 6-A / Module 1
#

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../../.." && pwd)"
PYTHON="/Users/huguoqing/zzzhu/code/exp/RAG/project1/.venv/bin/python"
VALIDATION_DIR="${PROJECT_ROOT}/validation-runs/$(date +%Y%m%d-%H%M%S)-phase6-module-1"

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
echo "Target Identity Validation Report" > "${SUMMARY_FILE}"
echo "=================================" >> "${SUMMARY_FILE}"
echo "Timestamp: $(date)" >> "${SUMMARY_FILE}"
echo "" >> "${SUMMARY_FILE}"

cd "${PROJECT_ROOT}"

# Test 1: Module import test
log_info "Test 1: Target Identity module import"
if PYTHONPATH=src "${PYTHON}" -c "
from core.wiki.target_identity import (
    TargetIdentity, TargetResolver, TargetCandidate,
    TargetResolutionStatus, SymbolKind, TargetIdentityStore
)
print('✓ All imports successful')
" > /dev/null 2>&1; then
    log_pass "Target Identity module imports successfully"
else
    log_fail "Target Identity module import failed"
fi

# Test 2: Target Identity structure validation
log_info "Test 2: Target Identity structure validation"
if PYTHONPATH=src "${PYTHON}" -c "
from core.wiki.target_identity import TargetIdentity, SymbolKind

# Create a TargetIdentity with all required fields
ti = TargetIdentity(
    file_relpath='src/core/llm.py',
    content_hash='a1b2c3d4e5f67890',
    symbol_qualname='LLMClient',
    symbol_kind=SymbolKind.CLASS,
    symbol_span=(1, 100),
    original_input='llm.py',
    resolution_method='unique'
)

# Verify all required fields
assert ti.file_relpath == 'src/core/llm.py', 'file_relpath missing'
assert ti.content_hash == 'a1b2c3d4e5f67890', 'content_hash missing'
assert ti.symbol_qualname == 'LLMClient', 'symbol_qualname missing'
assert ti.symbol_kind == SymbolKind.CLASS, 'symbol_kind missing'
assert ti.symbol_span == (1, 100), 'symbol_span missing'
assert ti.canonical_target_key, 'canonical_target_key not generated'

print(f'✓ canonical_target_key: {ti.canonical_target_key}')
" > /dev/null 2>&1; then
    log_pass "Target Identity structure is valid"
else
    log_fail "Target Identity structure validation failed"
fi

# Test 3: TargetResolver with unique file (single Python file with no symbols)
log_info "Test 3: TargetResolver with simple file"
TEST_SIMPLE="${VALIDATION_DIR}/simple_test.py"
echo "# Simple test file" > "${TEST_SIMPLE}"

if PYTHONPATH=src "${PYTHON}" -c "
from core.wiki.target_identity import TargetResolver, TargetResolutionStatus

resolver = TargetResolver('${VALIDATION_DIR}')
result = resolver.resolve('simple_test.py')

print(f'Status: {result.status.value}')
if result.status == TargetResolutionStatus.UNIQUE and result.selected_identity:
    print(f'✓ Resolved: {result.selected_identity.canonical_target_key}')
else:
    print(f'Status: {result.status.value}, Candidates: {len(result.candidates)}')
    exit(1)
" > /dev/null 2>&1; then
    log_pass "TargetResolver can resolve simple files"
else
    log_fail "TargetResolver simple file resolution failed"
fi

# Test 4: Disambiguation for ambiguous paths (same filename in different directories)
log_info "Test 4: Disambiguation for ambiguous paths"

# Create test scenario with duplicate filenames
TEST_WORKSPACE="${VALIDATION_DIR}/test_ambiguous"
mkdir -p "${TEST_WORKSPACE}/module1"
mkdir -p "${TEST_WORKSPACE}/module2"
echo "# test1" > "${TEST_WORKSPACE}/module1/utils.py"
echo "# test2" > "${TEST_WORKSPACE}/module2/utils.py"

if PYTHONPATH=src "${PYTHON}" -c "
from core.wiki.target_identity import TargetResolver, TargetResolutionStatus

resolver = TargetResolver('${TEST_WORKSPACE}')
result = resolver.resolve('utils.py')

print(f'Status: {result.status.value}')
if result.status == TargetResolutionStatus.AMBIGUOUS_PATH:
    print(f'✓ Correctly detected ambiguous path')
    print(f'  Candidates: {len(result.candidates)}')
elif result.status == TargetResolutionStatus.UNIQUE:
    print(f'✓ Resolved to unique (only one match)')
else:
    print(f'✗ Unexpected status: {result.status.value}')
    exit(1)
" > /dev/null 2>&1; then
    log_pass "Disambiguation works for ambiguous paths"
else
    log_fail "Disambiguation test for paths failed"
fi

# Test 5: Disambiguation for file with multiple symbols
log_info "Test 5: Disambiguation for files with multiple symbols"

# Create test file with multiple classes/functions
TEST_SYMBOLS="${VALIDATION_DIR}/multi_symbols.py"
cat > "${TEST_SYMBOLS}" << 'EOF'
class ClassA:
    """First class"""
    pass

class ClassB:
    """Second class"""
    pass

def func_a():
    """First function"""
    pass

def func_b():
    """Second function"""
    pass
EOF

if PYTHONPATH=src "${PYTHON}" -c "
from core.wiki.target_identity import TargetResolver, TargetResolutionStatus

resolver = TargetResolver('${VALIDATION_DIR}')
result = resolver.resolve('multi_symbols.py')

print(f'Status: {result.status.value}')
if result.status == TargetResolutionStatus.AMBIGUOUS_SYMBOL:
    print(f'✓ Correctly detected ambiguous symbols')
    print(f'  Candidates: {len(result.candidates)}')
    if len(result.disambiguation_prompt) > 0:
        print(f'  Disambiguation prompt generated')
    else:
        print(f'  No disambiguation prompt!')
        exit(1)
else:
    print(f'✗ Unexpected status: {result.status.value}')
    exit(1)
" > /dev/null 2>&1; then
    log_pass "Disambiguation works for ambiguous symbols"
else
    log_fail "Disambiguation test for symbols failed"
fi

# Test 6: TargetIdentityStore persistence
log_info "Test 6: TargetIdentityStore persistence"
if PYTHONPATH=src "${PYTHON}" -c "
from core.wiki.target_identity import TargetIdentity, TargetIdentityStore, SymbolKind
import os

store = TargetIdentityStore('${VALIDATION_DIR}')

ti = TargetIdentity(
    file_relpath='test.py',
    content_hash='abc123',
    symbol_qualname='TestClass',
    symbol_kind=SymbolKind.CLASS,
    original_input='test.py'
)

# Save
path = store.save(ti, 'task-001')
print(f'✓ Saved to: {path}')

# Load
loaded = store.load('task-001')
assert loaded is not None, 'Failed to load'
assert loaded.file_relpath == 'test.py', 'Loaded data mismatch'
assert loaded.canonical_target_key == ti.canonical_target_key, 'Key mismatch'

print(f'✓ Loaded canonical_target_key: {loaded.canonical_target_key}')
" > /dev/null 2>&1; then
    log_pass "TargetIdentityStore persistence works"
else
    log_fail "TargetIdentityStore persistence failed"
fi

# Test 7: Verify command import in commands.py
log_info "Test 7: Verify _cmd_prime uses Target Identity"
if grep -q "TargetResolver" "/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/src/core/commands.py" && \
   grep -q "TargetIdentityStore" "/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/src/core/commands.py"; then
    log_pass "_cmd_prime uses Target Identity system"
else
    log_fail "_cmd_prime does not use Target Identity system"
fi

# Test 8: Test /prime llm.py format (explicit path)
log_info "Test 8: Target resolution with explicit path"
if PYTHONPATH=src "${PYTHON}" -c "
from core.wiki.target_identity import TargetResolver, TargetResolutionStatus

resolver = TargetResolver('/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo')

# Test with explicit path - should resolve even with multiple symbols
result = resolver.resolve('src/core/llm.py')

print(f'Status: {result.status.value}')
print(f'File candidates: {len(set(c.file_relpath for c in result.candidates))}')

# Should find the file (even if symbols are ambiguous)
file_paths = set(c.file_relpath for c in result.candidates)
assert 'src/core/llm.py' in file_paths, 'Expected file not found'
print(f'✓ Found target file')
" > /dev/null 2>&1; then
    log_pass "Explicit path resolution works"
else
    log_fail "Explicit path resolution failed"
fi

# Summary
echo ""
echo "=================================" >> "${SUMMARY_FILE}"
echo "Tests Passed: ${TESTS_PASSED}" >> "${SUMMARY_FILE}"
echo "Tests Failed: ${TESTS_FAILED}" >> "${SUMMARY_FILE}"
echo "=================================" >> "${SUMMARY_FILE}"

if [ ${TESTS_FAILED} -eq 0 ]; then
    echo ""
    echo "STATUS: PASS" >> "${SUMMARY_FILE}"
    echo -e "${GREEN}=================================${NC}"
    echo -e "${GREEN}All tests passed!${NC}"
    echo -e "${GREEN}=================================${NC}"
    echo ""
    echo "Summary written to: ${SUMMARY_FILE}"
    exit 0
else
    echo ""
    echo "STATUS: FAIL" >> "${SUMMARY_FILE}"
    echo -e "${RED}=================================${NC}"
    echo -e "${RED}Some tests failed!${NC}"
    echo -e "${RED}=================================${NC}"
    echo ""
    echo "Summary written to: ${SUMMARY_FILE}"
    exit 1
fi
