
from pathlib import Path
import core.engine as engine_mod
from core.engine import Engine
from core.token_budget import BudgetThresholds
from tests.conftest import (
    DummyClient,
    DummyFinalMessage,
    DummyPermissionChecker,
    DummyTextBlock,
    DummyToolUseBlock,
    DummyUsage,
    DummyStream,
    DummyReadOnlyTool,
    DummyWriteTool,
    DummySessionStore,
    DummyCostTracker,
)


def test_engine_checkpoints_after_usage_threshold(tmp_repo, monkeypatch):
    monkeypatch.chdir(tmp_repo)
    eng = Engine(
        tools=[],
        system_prompt="sys",
        permission_checker=DummyPermissionChecker(),
        session_store=DummySessionStore(),
        cost_tracker=DummyCostTracker(),
    )
    eng._client = DummyClient([
        DummyStream(
            text_chunks=["hello"],
            final_message=DummyFinalMessage(
                content=[DummyTextBlock("done")],
                usage=DummyUsage(input_tokens=27000, output_tokens=100),
            ),
        )
    ])
    eng._budget_manager.thresholds = BudgetThresholds(
        soft_limit=1000,
        compact_limit=2000,
        checkpoint_limit=2500,
        hard_stop_limit=3000,
        max_context=32768,
    )
    events = list(eng.submit("hi"))
    texts = [e[1] for e in events if e[0] == "text"]
    assert any("checkpoint saved" in t.lower() for t in texts)
    assert (tmp_repo / "code-reading-notes" / "checkpoint_report.md").exists()


def test_engine_records_recent_written_artifacts(tmp_repo, monkeypatch):
    monkeypatch.chdir(tmp_repo)
    target = tmp_repo / "x.txt"
    eng = Engine(
        tools=[DummyWriteTool()],
        system_prompt="sys",
        permission_checker=DummyPermissionChecker(),
        session_store=DummySessionStore(),
        cost_tracker=DummyCostTracker(),
    )
    eng._client = DummyClient([
        DummyStream(
            final_message=DummyFinalMessage(
                content=[DummyToolUseBlock("Write", {"file_path": str(target)})],
                usage=DummyUsage(input_tokens=10, output_tokens=10),
            ),
        ),
        DummyStream(
            final_message=DummyFinalMessage(
                content=[DummyTextBlock("done")],
                usage=DummyUsage(input_tokens=20, output_tokens=10),
            ),
        ),
    ])
    events = list(eng.submit("please write"))
    assert str(target) in eng._recent_written_artifacts
    assert target.exists()


def test_engine_tool_result_budget_check_after_messages_append(tmp_repo, monkeypatch):
    monkeypatch.chdir(tmp_repo)
    eng = Engine(
        tools=[DummyReadOnlyTool()],
        system_prompt="sys",
        permission_checker=DummyPermissionChecker(),
        session_store=DummySessionStore(),
        cost_tracker=DummyCostTracker(),
    )
    eng._client = DummyClient([
        DummyStream(
            final_message=DummyFinalMessage(
                content=[DummyToolUseBlock("ReadOnlyDummy", {})],
                usage=DummyUsage(input_tokens=10, output_tokens=10),
            ),
        ),
        DummyStream(
            final_message=DummyFinalMessage(
                content=[DummyTextBlock("after tool")],
                usage=DummyUsage(input_tokens=10, output_tokens=10),
            ),
        ),
    ])
    eng._budget_manager.thresholds = BudgetThresholds(
        soft_limit=100,
        compact_limit=200,
        checkpoint_limit=300,
        hard_stop_limit=350,
        max_context=32768,
    )
    events = list(eng.submit("run tool"))
    # May or may not checkpoint depending on rough estimate, but should complete without exception
    assert events
