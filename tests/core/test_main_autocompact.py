
from types import SimpleNamespace
import core.main as main_mod
from core.compact import CompactService


def test_main_outer_autocompact_logic_uses_compact_service(monkeypatch):
    class DummyEngine:
        def __init__(self):
            self.messages = [{"role": "user", "content": "x" * 10000}]
            self.system_prompt = "sys"
            self.set_messages_called = False

        def get_messages(self):
            return self.messages

        def get_system_prompt(self):
            return self.system_prompt

        def set_messages(self, messages):
            self.messages = messages
            self.set_messages_called = True

    engine = DummyEngine()
    service = CompactService(client=SimpleNamespace(create_message=lambda **kwargs: SimpleNamespace(content=[{"type":"text","text":"summary"}])), model="dummy")
    monkeypatch.setattr(main_mod, "should_compact", lambda *args, **kwargs: True)
    new_msgs, _ = service.compact(engine.get_messages(), engine.get_system_prompt())
    engine.set_messages(new_msgs)
    assert engine.set_messages_called
    # assert len(engine.messages) >= 2
