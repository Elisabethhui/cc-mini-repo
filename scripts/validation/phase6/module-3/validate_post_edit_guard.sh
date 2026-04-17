#!/bin/bash
#
# Post Edit Guard Validation Script
# Phase 6-A / Module 3
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
VALIDATION_DIR="${PROJECT_ROOT}/validation-runs/$(date +%Y%m%d-%H%M%S)-phase6-module-3"

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
echo "Post Edit Guard Validation Report" > "${SUMMARY_FILE}"
echo "=================================" >> "${SUMMARY_FILE}"
echo "Timestamp: $(date)" >> "${SUMMARY_FILE}"
echo "" >> "${SUMMARY_FILE}"

cd "${PROJECT_ROOT}"

# Test 1: Module import test
log_info "Test 1: PostEditGuard module imports successfully"
if PYTHONPATH=src "${PYTHON}" -c "
from core.wiki.post_edit_guard import PostEditGuard, CompletionState, ImpactSummary
assert CompletionState.PATCHED.value == 'patched'
assert CompletionState.IMPACT_PENDING.value == 'impact_pending'
assert CompletionState.IMPACT_CLEAN.value == 'impact_clean'
assert CompletionState.COMPLETE.value == 'complete'
assert CompletionState.BLOCKED.value == 'blocked'
print('Module imported successfully')
print('CompletionState enum verified')
" > /dev/null 2>&1; then
    log_pass "PostEditGuard module imports and enum works"
else
    log_fail "PostEditGuard module import failed"
fi

# Test 2: Command registration test
log_info "Test 2: /post_edit command is registered"
if PYTHONPATH=src "${PYTHON}" -c "
from core.commands import _HANDLERS
assert 'post_edit' in _HANDLERS, 'post_edit not in handlers'
print('post_edit command registered')
" > /dev/null 2>&1; then
    log_pass "post_edit command is registered"
else
    log_fail "post_edit command not registered"
fi

# Test 3: PostEditGuard initialization
log_info "Test 3: PostEditGuard initializes correctly"
TEST_WORKSPACE="${VALIDATION_DIR}/test_workspace"
mkdir -p "${TEST_WORKSPACE}"

cd "${TEST_WORKSPACE}"

if PYTHONPATH="${PROJECT_ROOT}/src" "${PYTHON}" -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}/src')
from core.wiki.post_edit_guard import PostEditGuard
from pathlib import Path

guard = PostEditGuard('${TEST_WORKSPACE}')
assert guard.workspace == Path('${TEST_WORKSPACE}').resolve()
assert guard.impact_dir.exists()
print('PostEditGuard initialized')
print('Impact dir: ' + str(guard.impact_dir))
" > /dev/null 2>&1; then
    log_pass "PostEditGuard initializes correctly"
else
    log_fail "PostEditGuard initialization failed"
fi

# Test 4: Impact analysis generates correct state transitions
log_info "Test 4: Impact analysis generates state transitions"

# Create a demo Python file
mkdir -p "${TEST_WORKSPACE}/.cc-mini/wiki/entities"

cat > "${TEST_WORKSPACE}/demo_module.py" << 'EOF'
def greet():
    """Say hello."""
    return "hello"

class Greeter:
    pass
EOF

# Create an entity that references the function
cat > "${TEST_WORKSPACE}/.cc-mini/wiki/entities/demo_module.py.md" << 'EOF'
---
title: demo_module.py
source: demo_module.py
created: 2026-04-15
status: digested
---

# demo_module.py

## Functions

- **greet**: Returns "hello"

## Classes

- **Greeter**: Empty class
EOF

cd "${TEST_WORKSPACE}"

if PYTHONPATH="${PROJECT_ROOT}/src" "${PYTHON}" -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}/src')
from core.wiki.post_edit_guard import PostEditGuard, CompletionState
from pathlib import Path

workspace = Path('${TEST_WORKSPACE}')
guard = PostEditGuard(str(workspace))

# Simulate original content
original_content = '''def greet():
    \"\"\"Say hello.\"\"\"
    return \"hello\"

class Greeter:
    pass
'''

# Simulate patched content by updating the file
patched_content = '''def greet(name: str = \"world\") -> str:
    \"\"\"Say hello to someone.\"\"\"
    return f\"hello, {name}\"

class Greeter:
    \"\"\"A greeter class.\"\"\"
    def greet(self) -> str:
        return \"hello from Greeter\"
'''

demo_file = workspace / 'demo_module.py'
demo_file.write_text(patched_content)

# Analyze the patch
original_contents = {'demo_module.py': original_content}
patched_files = ['demo_module.py']

summary = guard.analyze_patch('test-task-001', patched_files, original_contents)

# Verify state
assert summary.task_id == 'test-task-001', 'Task ID mismatch'
assert len(summary.patched_files) == 1, 'Patched files count mismatch'
assert len(summary.changed_symbols) > 0, 'No changed symbols detected'
assert summary.has_public_api_change == True, 'Public API change not detected'
assert summary.completion_state == CompletionState.IMPACT_PENDING, f'Expected IMPACT_PENDING, got {summary.completion_state}'
assert summary.impacted_count > 0, 'Expected impacted entities'

print('Impact analysis completed')
print(f'State: {summary.completion_state.value}')
print(f'Changed symbols: {len(summary.changed_symbols)}')
print(f'Impacted entities: {summary.impacted_count}')
" > /dev/null 2>&1; then
    log_pass "Impact analysis generates correct state transitions"
else
    log_fail "Impact analysis failed or state incorrect"
fi

# Test 5: Impact summary persistence
log_info "Test 5: Impact summary persistence works"

# Create fresh workspace for test 5 to avoid conflicts
TEST_WORKSPACE_5="${VALIDATION_DIR}/test_workspace_5"
mkdir -p "${TEST_WORKSPACE_5}"

cd "${TEST_WORKSPACE_5}"

if PYTHONPATH="${PROJECT_ROOT}/src" "${PYTHON}" -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}/src')
from core.wiki.post_edit_guard import PostEditGuard, CompletionState
from pathlib import Path

workspace = Path('${TEST_WORKSPACE_5}')
guard = PostEditGuard(str(workspace))

# Setup test file
original_content = '''def greet():
    return \"hello\"
'''

(workspace / 'demo_module.py').write_text('def greet(name: str = \"world\") -> str:\n    return f\"hello, {name}\"')

summary = guard.analyze_patch('persist-test', ['demo_module.py'], {'demo_module.py': original_content})
saved_path = guard.save_impact_summary(summary)

assert saved_path.exists(), 'Impact summary not saved'

# Load it back
loaded = guard.load_impact_summary('persist-test')
assert loaded is not None, 'Failed to load impact summary'
assert loaded.task_id == 'persist-test', 'Loaded task ID mismatch'
assert loaded.completion_state.value == 'impact_clean', f'Loaded state mismatch: {loaded.completion_state}'

print('Impact summary saved and loaded')
" > /dev/null 2>&1; then
    log_pass "Impact summary persistence works"
else
    log_fail "Impact summary persistence failed"
fi

# Test 6: Completion state machine
log_info "Test 6: Completion state machine transitions correctly"

# Create fresh workspace for test 6
TEST_WORKSPACE_6="${VALIDATION_DIR}/test_workspace_6"
mkdir -p "${TEST_WORKSPACE_6}"

cd "${TEST_WORKSPACE_6}"

if PYTHONPATH="${PROJECT_ROOT}/src" "${PYTHON}" -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}/src')
from core.wiki.post_edit_guard import PostEditGuard, CompletionState
from pathlib import Path

workspace = Path('${TEST_WORKSPACE_6}')
guard = PostEditGuard(str(workspace))

# Test 1: Initial state after patch with impacts should be IMPACT_PENDING
original_content = '''def test():
    pass
'''
(workspace / 'demo_module.py').write_text('def test(x: int) -> int:\n    return x')

summary = guard.analyze_patch('state-machine-test', ['demo_module.py'], {'demo_module.py': original_content})
guard.save_impact_summary(summary)

assert summary.completion_state == CompletionState.IMPACT_CLEAN, f'Expected IMPACT_CLEAN, got {summary.completion_state}'
print('State after patch: IMPACT_CLEAN (no pending impacts in this case)')

# Test 2: Finalize completion
state = guard.finalize_completion('state-machine-test', verification_passed=True)
assert state == CompletionState.COMPLETE, f'Expected COMPLETE, got {state}'
print('State transition: IMPACT_CLEAN -> COMPLETE')

# Test 3: BLOCKED state
original_content = '''def test2():
    pass
'''
(workspace / 'demo_module.py').write_text('def test2() -> int:\n    return \"string\"')  # Type mismatch

summary = guard.analyze_patch('blocked-test', ['demo_module.py'], {'demo_module.py': original_content})
summary.blockers.append('Type mismatch detected')
guard.save_impact_summary(summary)

state = guard.finalize_completion('blocked-test', verification_passed=False)
assert state == CompletionState.BLOCKED, f'Expected BLOCKED, got {state}'
print('State: BLOCKED when verification fails')

# Test 4: BLOCKED with blockers
state = guard.finalize_completion('blocked-test', verification_passed=True)
assert state == CompletionState.BLOCKED, f'Expected BLOCKED with blockers, got {state}'
print('State: BLOCKED when blockers exist')

print('All state transitions verified')
" > /dev/null 2>&1; then
    log_pass "Completion state machine transitions correctly"
else
    log_fail "State machine transition failed"
fi

# Test 7: Output format validation
log_info "Test 7: Impact summary output format is correct"

cd "${TEST_WORKSPACE}"

if PYTHONPATH="${PROJECT_ROOT}/src" "${PYTHON}" -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}/src')
from core.wiki.post_edit_guard import ImpactSummary, CompletionState, format_impact_summary, ChangedSymbol

summary = ImpactSummary(
    task_id='format-test',
    patched_files=['test.py'],
    changed_symbols=[
        ChangedSymbol(name='greet', symbol_type='function', file_path='test.py', change_type='modified'),
    ],
    completion_state=CompletionState.IMPACT_PENDING,
)

output = format_impact_summary(summary)

# Verify output contains expected sections
assert 'POST-EDIT IMPACT ANALYSIS' in output, 'Missing header'
assert 'Task ID: format-test' in output, 'Missing task ID'
assert 'State: IMPACT_PENDING' in output, 'Missing state'
assert 'Changed Symbols:' in output, 'Missing changed symbols section'
assert 'greet (function): modified' in output, 'Missing symbol details'

print('Output format validated')
" > /dev/null 2>&1; then
    log_pass "Impact summary output format is correct"
else
    log_fail "Output format validation failed"
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
    echo "Summary: ${SUMMARY_FILE}"
    exit 0
else
    echo ""
    echo "STATUS: FAIL" >> "${SUMMARY_FILE}"
    echo -e "${RED}=================================${NC}"
    echo -e "${RED}Some tests failed!${NC}"
    echo -e "${RED}=================================${NC}"
    echo ""
    echo "Summary: ${SUMMARY_FILE}"
    exit 1
fi
