
import types
import pytest


class DummyUsage:
    def __init__(self, input_tokens=0, output_tokens=0, cache_read_input_tokens=0, cache_creation_input_tokens=0):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_read_input_tokens = cache_read_input_tokens
        self.cache_creation_input_tokens = cache_creation_input_tokens


class DummyTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class DummyToolUseBlock:
    def __init__(self, name, input=None, id="toolu_1"):
        self.type = "tool_use"
        self.name = name
        self.input = input or {}
        self.id = id


class DummyFinalMessage:
    def __init__(self, content, usage=None):
        self.content = content
        self.usage = usage


class DummyStream:
    def __init__(self, text_chunks=None, final_message=None):
        self.text_stream = iter(text_chunks or [])
        self._final_message = final_message

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get_final_message(self):
        return self._final_message

    def close(self):
        return None


class DummyClient:
    def __init__(self, streams=None):
        self.streams = list(streams or [])

    def stream_messages(self, **kwargs):
        if not self.streams:
            raise RuntimeError("No more streams configured")
        return self.streams.pop(0)

    def create_message(self, **kwargs):
        # compact.py uses this
        return DummyFinalMessage([{"type": "text", "text": "compact summary"}])

    def is_authentication_error(self, e):
        return False

    def is_retryable_error(self, e):
        return False

    def is_api_error(self, e):
        return False

    def error_message(self, e):
        return str(e)


class DummyPermissionChecker:
    def __init__(self, decision="allow"):
        self.decision = decision

    def check(self, tool, tool_input):
        return self.decision


class DummyReadOnlyTool:
    name = "ReadOnlyDummy"

    def to_api_schema(self):
        return {"name": self.name, "input_schema": {"type": "object", "properties": {}}}

    def is_read_only(self):
        return True

    def get_activity_description(self, **kwargs):
        return "Reading"

    def execute(self, **kwargs):
        from core.tools.base import ToolResult
        return ToolResult(content="x" * 1500, is_error=False)


class DummyWriteTool:
    name = "Write"

    def to_api_schema(self):
        return {"name": self.name, "input_schema": {"type": "object", "properties": {"file_path": {"type": "string"}}}}

    def is_read_only(self):
        return False

    def get_activity_description(self, **kwargs):
        return "Writing"

    def execute(self, **kwargs):
        from core.tools.base import ToolResult
        fp = kwargs.get("file_path")
        if fp:
            from pathlib import Path
            Path(fp).write_text("new content", encoding="utf-8")
        return ToolResult(content="ok", is_error=False)


class DummySessionStore:
    def __init__(self):
        self.messages = []

    def append_message(self, message):
        self.messages.append(message)


class DummyCostTracker:
    def __init__(self):
        self.last_input_tokens = 0
        self.usages = []
        self.lines = []

    def add_usage(self, model, usage, api_duration_s=0):
        self.last_input_tokens = usage.get("input_tokens", 0)
        self.usages.append((model, usage, api_duration_s))

    def add_lines_changed(self, added, removed):
        self.lines.append((added, removed))


@pytest.fixture
def tmp_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    notes = repo / "code-reading-notes"
    notes.mkdir()
    (notes / "manifest.json").write_text("{}", encoding="utf-8")
    return repo
