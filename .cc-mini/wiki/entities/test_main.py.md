# Entity: tests/test_main.py

## Classes
- **class DummyTool**: 无文档说明
  - Methods: execute
- **class _FakeEscListener**: A no-op replacement for EscListener that doesn't touch the terminal.
  - Methods: __init__, __enter__, __exit__, pause, resume, check_esc_nonblocking

## Functions
- **def _make_text_stream()**: 无文档说明
- **def _make_engine()**: 无文档说明
- **def test_run_query_prints_text()**: run_query should print text events to stdout in print_mode.
- **def test_run_query_handles_tool_call_event()**: run_query should display tool call info via rich console.
- **def test_run_query_handles_keyboard_interrupt()**: run_query should gracefully handle KeyboardInterrupt.