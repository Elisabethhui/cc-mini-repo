import json
import time
from io import StringIO
from unittest.mock import MagicMock

from rich.console import Console

from core.commands import CommandContext, handle_command
from core.coordinator import classify_task_intent
from core.tools.agent import AgentTool
from core.worker_manager import WorkerManager


class _FakeEngine:
    def __init__(self):
        self.prompts: list[str] = []
        self.aborted = False

    def submit(self, prompt: str):
        self.prompts.append(prompt)
        yield ("text", f"done:{prompt}")

    def abort(self) -> None:
        self.aborted = True


def _wait_for_notification(manager: WorkerManager, timeout: float = 1.0) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        notifications = manager.drain_notifications()
        if notifications:
            return notifications[0]
        time.sleep(0.01)
    raise AssertionError("Timed out waiting for worker notification")


def test_task_intent_classifier_distinguishes_coding_and_general_requests():
    assert classify_task_intent("fix src/core/main.py") == "coding-adjacent"
    assert classify_task_intent("summarize the release notes") == "general"


def test_task_command_builds_task_intake_prompt():
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("task", "summarize the release notes", ctx)

    output = console.file.getvalue()
    assert "Routing as general intake." in output
    assert ctx.pending_query is not None
    assert "Intent: general" in ctx.pending_query
    assert "Prefer the coding-adjacent route" in ctx.pending_query


def test_agent_tool_preserves_task_kind_and_worker_context():
    engine = _FakeEngine()
    manager = WorkerManager(build_worker_engine=lambda: engine)
    tool = AgentTool(manager)

    result = tool.execute(
        description="Research docs",
        prompt="Review the README and report the scope.",
        task_kind="research",
    )

    payload = json.loads(result.content)
    assert payload["task_kind"] == "research"

    notification = _wait_for_notification(manager)
    assert "<task-kind>research</task-kind>" in notification
    assert "Agent \"Research docs\" (research) completed" in notification
    assert engine.prompts[0].startswith("This is a research task.")
