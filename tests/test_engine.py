from unittest.mock import MagicMock, patch
from core.engine import Engine
from core.config import default_max_tokens_for_model
from core.tools.base import Tool, ToolResult
from core.permissions import PermissionChecker
from core.token_budget import TokenBudgetManager, BudgetThresholds


class EchoTool(Tool):
    name = "Echo"
    description = "Returns the input message"
    input_schema = {
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    }

    def execute(self, message: str) -> ToolResult:
        return ToolResult(content=f"Echo: {message}")


def _make_engine(auto_approve=True):
    return Engine(
        tools=[EchoTool()],
        system_prompt="You are a test assistant.",
        permission_checker=PermissionChecker(auto_approve=auto_approve),
        max_tokens=1_000,
        context_window=100_000,
    )


def _make_text_response(text: str):
    """Simulate an API response with just text (no tool calls)."""
    block = MagicMock()
    block.type = "text"
    block.text = text

    final_msg = MagicMock()
    final_msg.content = [block]

    stream = MagicMock()
    stream.__enter__ = MagicMock(return_value=stream)
    stream.__exit__ = MagicMock(return_value=False)
    stream.text_stream = iter([text])
    stream.get_final_message = MagicMock(return_value=final_msg)
    return stream


def _make_tool_then_text_response(tool_name, tool_input, tool_use_id, text):
    """Simulate: first response has tool_use, second response has text."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = tool_use_id
    tool_block.name = tool_name
    tool_block.input = tool_input

    first_final = MagicMock()
    first_final.content = [tool_block]
    first_stream = MagicMock()
    first_stream.__enter__ = MagicMock(return_value=first_stream)
    first_stream.__exit__ = MagicMock(return_value=False)
    first_stream.text_stream = iter([])
    first_stream.get_final_message = MagicMock(return_value=first_final)

    second_stream = _make_text_response(text)
    return [first_stream, second_stream]


def test_engine_returns_text_events():
    engine = _make_engine()
    with patch.object(engine._client, "stream_messages", return_value=_make_text_response("hello")):
        events = list(engine.submit("hi"))
    text_events = [e for e in events if e[0] == "text"]
    assert any("hello" in e[1] for e in text_events)


def test_engine_executes_tool_and_loops():
    engine = _make_engine()
    streams = _make_tool_then_text_response("Echo", {"message": "world"}, "tu_1", "done")

    with patch.object(engine._client, "stream_messages", side_effect=streams):
        events = list(engine.submit("use the echo tool"))

    tool_result_events = [e for e in events if e[0] == "tool_result"]
    assert len(tool_result_events) == 1
    _, tool_name, _, result = tool_result_events[0]
    assert tool_name == "Echo"
    assert "Echo: world" in result.content


def test_engine_denied_tool_returns_error_result():
    engine = _make_engine(auto_approve=False)
    streams = _make_tool_then_text_response("Echo", {"message": "hi"}, "tu_2", "ok")

    with patch.object(engine._permissions, "_prompt_user", return_value="deny"):
        with patch.object(engine._client, "stream_messages", side_effect=streams):
            events = list(engine.submit("echo hi"))

    tool_result_events = [e for e in events if e[0] == "tool_result"]
    assert tool_result_events[0][3].is_error


def test_engine_unknown_tool_returns_error():
    engine = _make_engine()
    streams = _make_tool_then_text_response("UnknownTool", {}, "tu_3", "done")

    with patch.object(engine._client, "stream_messages", side_effect=streams):
        events = list(engine.submit("use unknown"))

    tool_result_events = [e for e in events if e[0] == "tool_result"]
    assert tool_result_events[0][3].is_error
    assert "Unknown tool" in tool_result_events[0][3].content


def test_engine_uses_model_specific_default_max_tokens():
    engine = Engine(
        tools=[EchoTool()],
        system_prompt="You are a test assistant.",
        permission_checker=PermissionChecker(auto_approve=True),
        model="claude-sonnet-4",
        context_window=200_000,
    )

    with patch.object(engine._client, "stream_messages", return_value=_make_text_response("hello")) as stream:
        list(engine.submit("hi"))

    assert stream.call_args.kwargs["model"] == "claude-sonnet-4"
    assert stream.call_args.kwargs["max_tokens"] == default_max_tokens_for_model("claude-sonnet-4")


def test_engine_normalizes_assistant_tool_use_blocks_before_retrying():
    engine = _make_engine()
    streams = _make_tool_then_text_response("Echo", {"message": "world"}, "tu_1", "done")

    with patch.object(engine._client, "stream_messages", side_effect=streams) as stream:
        list(engine.submit("use the echo tool"))

    second_messages = stream.call_args_list[1].kwargs["messages"]
    assistant_message = second_messages[1]
    assistant_block = assistant_message["content"][0]

    assert isinstance(assistant_block, dict)
    assert assistant_block == {
        "type": "tool_use",
        "id": "tu_1",
        "name": "Echo",
        "input": {"message": "world"},
    }


def test_engine_normalizes_tool_result_blocks_before_follow_up_request():
    engine = _make_engine()
    streams = _make_tool_then_text_response("Echo", {"message": "world"}, "tu_1", "done")

    with patch.object(engine._client, "stream_messages", side_effect=streams) as stream:
        list(engine.submit("use the echo tool"))

    second_messages = stream.call_args_list[1].kwargs["messages"]
    tool_result_message = second_messages[2]

    assert tool_result_message["content"] == [{
        "type": "tool_result",
        "tool_use_id": "tu_1",
        "content": "Echo: world",
        "is_error": False,
    }]


def test_engine_preflight_hard_stop_blocks_llm_call():
    """HARD_STOP pre-flight should prevent the LLM call and emit a checkpoint event."""
    engine = _make_engine()
    # Tiny window forces hard_stop regardless of message size
    engine._budget_manager = TokenBudgetManager(
        context_window=50,
        max_output_tokens=20,
        safety_margin_tokens=10,
    )

    with patch.object(engine._client, "stream_messages") as mock_stream:
        events = list(engine.submit("hi"))
        mock_stream.assert_not_called()

    text_events = [e for e in events if e[0] == "text"]
    assert any("checkpoint" in e[1].lower() for e in text_events)


def test_engine_preflight_warning_allows_llm_call():
    """WARNING pre-flight should dehydrate but still allow the LLM call."""
    engine = _make_engine()
    # Low warning_ratio so the default system prompt + tools trigger WARNING
    # but stay below PRESERVE (default 0.75)
    engine._budget_manager = TokenBudgetManager(
        context_window=10_000,
        max_output_tokens=2_000,
        safety_margin_tokens=1_000,
        thresholds=BudgetThresholds(warning_ratio=0.001),
    )

    with patch.object(engine._client, "stream_messages", return_value=_make_text_response("hello")):
        events = list(engine.submit("hi"))

    text_events = [e for e in events if e[0] == "text"]
    assert any("hello" in e[1] for e in text_events)


def test_engine_preflight_preserve_tries_compact():
    """PRESERVE pre-flight should attempt compact if compact_service is available."""
    engine = _make_engine()
    # Small window + low preserve_ratio forces PRESERVE but stays below SPLIT
    engine._budget_manager = TokenBudgetManager(
        context_window=200,
        max_output_tokens=50,
        safety_margin_tokens=20,
        thresholds=BudgetThresholds(preserve_ratio=0.5, split_ratio=0.9),
    )

    compact_called = False

    class FakeCompactService:
        def compact(self, messages, system_prompt):
            nonlocal compact_called
            compact_called = True
            # Simulate compaction by clearing most messages
            messages[:] = messages[-2:] if len(messages) >= 2 else messages

    engine._compact_service = FakeCompactService()

    with patch.object(engine._client, "stream_messages", return_value=_make_text_response("hello")):
        events = list(engine.submit("hi"))

    assert compact_called is True
    text_events = [e for e in events if e[0] == "text"]
    assert any("hello" in e[1] for e in text_events)


def test_engine_preflight_preserve_falls_back_when_compact_fails():
    """If compact fails in PRESERVE state, engine should not silently ignore it."""
    engine = _make_engine()
    engine._budget_manager = TokenBudgetManager(
        context_window=200,
        max_output_tokens=50,
        safety_margin_tokens=20,
        thresholds=BudgetThresholds(preserve_ratio=0.5, split_ratio=0.9),
    )

    class BrokenCompactService:
        def compact(self, messages, system_prompt):
            raise RuntimeError("compact failure")

    engine._compact_service = BrokenCompactService()

    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()
    try:
        with patch.object(engine._client, "stream_messages", return_value=_make_text_response("hello")):
            events = list(engine.submit("hi"))
    finally:
        sys.stdout = old_stdout

    output = captured.getvalue()
    assert "[Compact Failed]" in output
    # PRESERVE does not stop the engine, so the LLM call should still proceed
    text_events = [e for e in events if e[0] == "text"]
    assert any("hello" in e[1] for e in text_events)
