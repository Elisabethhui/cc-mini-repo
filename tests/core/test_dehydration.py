
from core.dehydration import maybe_dehydrate_messages


def test_dehydrate_old_tool_results_replaces_large_content():
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "ok"},
        {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": "t1",
                "content": "x" * 5000,
                "is_error": False,
            }],
        },
        {"role": "assistant", "content": "consumed"},
        {"role": "user", "content": "recent"},
        {"role": "assistant", "content": "latest"},
    ]
    result = maybe_dehydrate_messages(messages)
    assert result.replaced_count == 1
    dehydrated = messages[2]["content"][0]["content"]
    assert "[tool_result dehydrated]" in dehydrated


def test_short_tool_result_not_dehydrated():
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "ok"},
        {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": "t1",
                "content": "short",
                "is_error": False,
            }],
        },
        {"role": "assistant", "content": "consumed"},
        {"role": "user", "content": "recent"},
        {"role": "assistant", "content": "latest"},
    ]
    result = maybe_dehydrate_messages(messages)
    assert result.replaced_count == 0
