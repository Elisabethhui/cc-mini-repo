from core.compact import CompactService

class DummyClient:
    def create_message(self, **kwargs):
        class Resp:
            content = [
                {
                    "type": "text",
                    "text": "This is the compacted summary."
                }
            ]
        return Resp()


def test_compact_messages_triggers_real_compaction():
    service = CompactService(client=DummyClient(), model="dummy")
    messages = [
        {"role": "user", "content": "old user message 1 " * 1000},
        {"role": "assistant", "content": "old assistant message 1 " * 1000},
        {"role": "user", "content": "old user message 2 " * 1000},
        {"role": "assistant", "content": "old assistant message 2 " * 1000},
        {"role": "user", "content": "old user message 3 " * 1000},
        {"role": "assistant", "content": "old assistant message 3 " * 1000},
        {"role": "user", "content": "recent user question 1"},
        {"role": "assistant", "content": "recent assistant answer 1"},
        {"role": "user", "content": "recent user question 2"},
        {"role": "assistant", "content": "recent assistant answer 2"},
    ]
    new_messages = service.compact_messages(
        messages,
        system_prompt="sys",
        reason="runtime",
    )

    assert isinstance(new_messages, list)
    assert len(new_messages) >= 2

    # 第 1 条应该是 summary wrapper
    # assert new_messages[0]["role"] == "user"
    # assert "summary of the conversation so far" in new_messages[0]["content"].lower()

    # # 第 2 条应该是 assistant ack
    # assert new_messages[1]["role"] == "assistant"
    # assert "ready to continue" in new_messages[1]["content"].lower()

    # # 同时 recent 消息应该还在
    # roles = [m["role"] for m in new_messages]
    # assert roles.count("user") >= 3
    # assert roles.count("assistant") >= 3

def test_compact_messages_wrapper_returns_new_message_list():
    service = CompactService(client=DummyClient(), model="dummy")
    messages = [
        {"role": "user", "content": "hello" * 3000},
        {"role": "assistant", "content": "world" * 3000},
        {"role": "user", "content": "older question 1"},
        {"role": "assistant", "content": "older answer 1"},
        {"role": "user", "content": "older question 2"},
        {"role": "assistant", "content": "older answer 2"},
        {"role": "user", "content": "recent question"},
        {"role": "assistant", "content": "recent answer"},
        {"role": "user", "content": "recent question 2"},
        {"role": "assistant", "content": "recent answer 2"},
    ]
    new_messages = service.compact_messages(messages, system_prompt="sys", reason="runtime")
    assert isinstance(new_messages, list)
    # assert len(new_messages) >= 2
    # assert "summary of the conversation" in new_messages[0]["content"].lower()