import json

from core.batch_runner import BatchRunner
from core.context_budget import BudgetState
from core.runtime_state import RuntimeStateStore


def test_basic_run_reaches_done(tmp_path):
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)

    called = []

    def worker(state):
        called.append(state.get("phase"))

    def review_worker(state):
        called.append(state.get("phase"))
        # Review gate requires an explicit decision to reach done
        state["review_decision"] = "commit"

    final = runner.run("Build feature X", workers={
        "intake": worker,
        "plan": worker,
        "retrieve": worker,
        "pack": worker,
        "implement": worker,
        "test": worker,
        "review": review_worker,
    })

    assert final["phase"] == "done"
    assert final["next_action"] == "Task completed"
    assert runner.step_count == 8
    assert called == ["intake", "plan", "retrieve", "pack", "implement", "test", "review"]


def test_max_steps_limits_execution(tmp_path):
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=2, context_window=32768)

    final = runner.run("Build feature X")

    # Only 2 steps executed: intake -> plan -> (stopped)
    assert runner.step_count == 2
    assert final["phase"] == "retrieve"


def test_workers_receive_and_can_mutate_state(tmp_path):
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)

    def review_worker(state):
        # Reviewer decides changes are needed, go back to implement
        state["phase"] = "implement"
        state["next_action"] = "Revise implementation"

    final = runner.run("Build feature X", workers={
        "review": review_worker,
    })

    # Because review worker mutated phase to implement,
    # the runner continues: implement -> test -> review -> ...
    # But since review worker always sets to implement, it loops.
    # With max_steps=10, it stops at 10.
    assert runner.step_count == 10
    assert final["phase"] == "implement"


def test_each_step_writes_runtime_state(tmp_path):
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=3, context_window=32768)

    runner.run("Build feature X")

    assert store._state_path.exists()
    state = store.load_state()
    assert state["goal"] == "Build feature X"
    assert state["phase"] == "pack"  # after 3 steps: intake -> plan -> retrieve -> pack


def test_each_step_records_budget_report(tmp_path):
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=3, context_window=32768)

    runner.run("Build feature X")

    reports = store.list_budget_reports()
    # Only the steps that were actually executed (not terminal) record reports
    # Steps: intake, plan, retrieve -> 3 reports
    assert len(reports) == 3
    for r in reports:
        assert "state" in r
        assert "projected_total_tokens" in r


def test_next_action_is_updated_every_step(tmp_path):
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=7, context_window=32768)

    def review_worker(state):
        state["review_decision"] = "commit"

    runner.run("Build feature X", workers={"review": review_worker})

    state = store.load_state()
    assert state["next_action"] == "Task completed"
    steps = store.list_steps()
    assert len(steps) == 7


def test_budget_preserve_transitions_to_plan(tmp_path):
    """Large state triggers PRESERVE; runner returns to plan, not blocked."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    # Small window so a modest goal exceeds preserve threshold
    runner = BatchRunner(
        store,
        max_steps=1,
        context_window=4000,
        reserved_output_tokens=100,
        safety_margin_tokens=50,
    )

    # Goal length ~2200 chars -> packed ~1250 -> total ~3100 -> ratio ~0.775 (preserve)
    final = runner.run("x" * 2200)

    assert final["phase"] == "plan"
    assert "preserve" in final["next_action"].lower()
    # Preservation pipeline writes a step log and budget report
    assert len(store.list_steps()) >= 1
    assert len(store.list_budget_reports()) >= 1


def test_budget_split_transitions_to_plan(tmp_path):
    """Very large state triggers SPLIT; runner returns to plan."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(
        store,
        max_steps=1,
        context_window=4000,
        reserved_output_tokens=100,
        safety_margin_tokens=50,
    )

    # Goal length ~2900 chars -> packed ~1638 -> total ~3488 -> ratio ~0.872 (split)
    final = runner.run("x" * 2900)

    assert final["phase"] == "plan"
    assert "split" in final["next_action"].lower()
    assert len(store.list_steps()) >= 1


def test_hard_stop_transitions_to_blocked(tmp_path):
    """Extremely large state triggers HARD_STOP; runner becomes blocked."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(
        store,
        max_steps=1,
        context_window=4000,
        reserved_output_tokens=100,
        safety_margin_tokens=50,
    )

    # Goal length ~3500 chars -> packed ~1944 -> total ~3794 -> ratio ~0.949 (hard_stop)
    final = runner.run("x" * 3500)

    assert final["phase"] == "blocked"
    assert "hard_stop" in final["next_action"].lower() or "human" in final["next_action"].lower()


def test_preserve_phase_explicitly(tmp_path):
    """Starting from preserve phase runs preservation and returns to plan."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    store.patch_state(phase="preserve", goal="test")
    runner = BatchRunner(
        store,
        max_steps=1,
        context_window=32768,
    )

    final = runner.run("test")
    assert final["phase"] == "plan"
    assert "preserve" in final["next_action"].lower()


def test_split_phase_explicitly(tmp_path):
    """Starting from split phase runs preservation and returns to plan."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    store.patch_state(phase="split", goal="test")
    runner = BatchRunner(
        store,
        max_steps=1,
        context_window=32768,
    )

    final = runner.run("test")
    assert final["phase"] == "plan"
    assert "split" in final["next_action"].lower()


def test_unknown_phase_becomes_blocked(tmp_path):
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    store.patch_state(phase="unknown_phase", goal="test")
    runner = BatchRunner(store, max_steps=1, context_window=32768)

    final = runner.run("test")
    assert final["phase"] == "blocked"
    assert "unknown" in final["next_action"].lower()


def test_step_logs_contain_budget_info(tmp_path):
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=2, context_window=32768)

    runner.run("Build feature X")

    steps = store.list_steps()
    assert len(steps) == 2
    for step_name in steps:
        content = store.read_step_log(step_name.replace(".md", ""))
        assert "Budget:" in content
        assert "Goal:" in content


def test_run_supervised_calls_engine_once_per_step(tmp_path):
    """Each step in supervised mode should trigger exactly one model call."""
    from unittest.mock import MagicMock, patch
    from core.engine import Engine
    from core.tools.base import Tool, ToolResult
    from core.permissions import PermissionChecker
    from core.context_pack import ContextPackBuilder

    class NoopTool(Tool):
        name = "Noop"
        description = "Noop"
        input_schema = {"type": "object", "properties": {}}

        def execute(self) -> ToolResult:
            return ToolResult(content="ok")

    engine = Engine(
        tools=[NoopTool()],
        system_prompt="test",
        permission_checker=PermissionChecker(auto_approve=True),
        max_tokens=1000,
        context_window=100_000,
    )

    stream = MagicMock()
    stream.__enter__ = MagicMock(return_value=stream)
    stream.__exit__ = MagicMock(return_value=False)
    stream.text_stream = iter(["step output"])
    final_msg = MagicMock()
    final_msg.content = [MagicMock(type="text", text="step output")]
    stream.get_final_message = MagicMock(return_value=final_msg)

    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=3, context_window=32768)
    builder = ContextPackBuilder(context_window=32768)

    with patch.object(engine._client, "stream_messages", return_value=stream) as mock_stream:
        final = runner.run_supervised(
            goal="Build feature X",
            engine=engine,
            pack_builder=builder,
        )

    # 3 steps => 3 model calls
    assert mock_stream.call_count == 3
    assert runner.step_count == 3
    assert final["phase"] == "pack"  # intake -> plan -> retrieve -> pack


def test_run_supervised_writes_step_result_artifacts(tmp_path):
    """Supervised run should write a StepResult artifact for every step."""
    from unittest.mock import MagicMock, patch
    from core.engine import Engine
    from core.tools.base import Tool, ToolResult
    from core.permissions import PermissionChecker
    from core.context_pack import ContextPackBuilder

    class NoopTool(Tool):
        name = "Noop"
        description = "Noop"
        input_schema = {"type": "object", "properties": {}}

        def execute(self) -> ToolResult:
            return ToolResult(content="ok")

    engine = Engine(
        tools=[NoopTool()],
        system_prompt="test",
        permission_checker=PermissionChecker(auto_approve=True),
        max_tokens=1000,
        context_window=100_000,
    )

    stream = MagicMock()
    stream.__enter__ = MagicMock(return_value=stream)
    stream.__exit__ = MagicMock(return_value=False)
    stream.text_stream = iter(["step output"])
    final_msg = MagicMock()
    final_msg.content = [MagicMock(type="text", text="step output")]
    stream.get_final_message = MagicMock(return_value=final_msg)

    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=2, context_window=32768)
    builder = ContextPackBuilder(context_window=32768)

    with patch.object(engine._client, "stream_messages", return_value=stream):
        runner.run_supervised(
            goal="Build feature X",
            engine=engine,
            pack_builder=builder,
        )

    artifacts = store.list_artifacts()
    assert len(artifacts) == 2
    assert all(a.startswith("step-result-") for a in artifacts)

    for name in artifacts:
        content = store.read_artifact(name)
        data = json.loads(content)
        assert "step_number" in data
        assert "phase" in data
        assert "assistant_text" in data
        assert "tool_calls" in data


def test_run_supervised_respects_budget_hard_stop(tmp_path):
    """If the engine reports a hard-stop, the runner should transition to blocked."""
    from unittest.mock import MagicMock, patch
    from core.engine import Engine
    from core.tools.base import Tool, ToolResult
    from core.permissions import PermissionChecker
    from core.context_pack import ContextPackBuilder

    class NoopTool(Tool):
        name = "Noop"
        description = "Noop"
        input_schema = {"type": "object", "properties": {}}

        def execute(self) -> ToolResult:
            return ToolResult(content="ok")

    engine = Engine(
        tools=[NoopTool()],
        system_prompt="test",
        permission_checker=PermissionChecker(auto_approve=True),
        max_tokens=1000,
        context_window=100_000,
    )

    # Simulate a hard-stop response (checkpoint text)
    stream = MagicMock()
    stream.__enter__ = MagicMock(return_value=stream)
    stream.__exit__ = MagicMock(return_value=False)
    stream.text_stream = iter(["[checkpoint saved; run /resume-from-checkpoint]"])
    final_msg = MagicMock()
    final_msg.content = [MagicMock(type="text", text="[checkpoint saved; run /resume-from-checkpoint]")]
    stream.get_final_message = MagicMock(return_value=final_msg)

    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=3, context_window=32768)
    builder = ContextPackBuilder(context_window=32768)

    with patch.object(engine._client, "stream_messages", return_value=stream):
        final = runner.run_supervised(
            goal="Build feature X",
            engine=engine,
            pack_builder=builder,
        )

    # First step hits hard_stop -> blocked
    assert final["phase"] == "blocked"
    assert "hard_stop" in final["next_action"].lower() or "budget" in final["next_action"].lower()


def test_resume_supervised_continues_from_saved_phase(tmp_path):
    """Resume should pick up from the phase stored in runtime state."""
    from unittest.mock import MagicMock, patch
    from core.engine import Engine
    from core.tools.base import Tool, ToolResult
    from core.permissions import PermissionChecker
    from core.context_pack import ContextPackBuilder

    class NoopTool(Tool):
        name = "Noop"
        description = "Noop"
        input_schema = {"type": "object", "properties": {}}

        def execute(self) -> ToolResult:
            return ToolResult(content="ok")

    engine = Engine(
        tools=[NoopTool()],
        system_prompt="test",
        permission_checker=PermissionChecker(auto_approve=True),
        max_tokens=1000,
        context_window=100_000,
    )

    stream = MagicMock()
    stream.__enter__ = MagicMock(return_value=stream)
    stream.__exit__ = MagicMock(return_value=False)
    stream.text_stream = iter(["step output"])
    final_msg = MagicMock()
    final_msg.content = [MagicMock(type="text", text="step output")]
    stream.get_final_message = MagicMock(return_value=final_msg)

    store = RuntimeStateStore(str(tmp_path), run_id="test")
    # Pre-seed state at "plan" phase with prior step artifacts
    store.save_state({
        "run_id": "test",
        "phase": "plan",
        "goal": "Build feature X",
        "next_action": "Plan the implementation",
        "decisions": [],
        "open_questions": [],
        "artifacts": [],
        "budget_reports": [],
        "current_step": "",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    })
    store.write_artifact("step-result-001.json", '{"step_number": 1}')
    store.write_artifact("step-result-002.json", '{"step_number": 2}')

    runner = BatchRunner(store, max_steps=3, context_window=32768)
    builder = ContextPackBuilder(context_window=32768)

    with patch.object(engine._client, "stream_messages", return_value=stream) as mock_stream:
        final = runner.resume_supervised(
            goal="Build feature X",
            engine=engine,
            pack_builder=builder,
        )

    # Should continue from plan -> retrieve -> pack -> implement (3 steps)
    assert mock_stream.call_count == 3
    assert runner.step_count == 5  # continued from 2 -> 3,4,5
    assert final["phase"] == "implement"


def test_resume_supervised_returns_terminal_state_without_calling_model(tmp_path):
    """Resuming a run that is already done or blocked should not call the model."""
    from unittest.mock import MagicMock, patch
    from core.engine import Engine
    from core.tools.base import Tool, ToolResult
    from core.permissions import PermissionChecker
    from core.context_pack import ContextPackBuilder

    class NoopTool(Tool):
        name = "Noop"
        description = "Noop"
        input_schema = {"type": "object", "properties": {}}

        def execute(self) -> ToolResult:
            return ToolResult(content="ok")

    engine = Engine(
        tools=[NoopTool()],
        system_prompt="test",
        permission_checker=PermissionChecker(auto_approve=True),
        max_tokens=1000,
        context_window=100_000,
    )

    store = RuntimeStateStore(str(tmp_path), run_id="test")
    store.save_state({
        "run_id": "test",
        "phase": "blocked",
        "goal": "Build feature X",
        "next_action": "Hard stop: budget",
        "decisions": [],
        "open_questions": [],
        "artifacts": [],
        "budget_reports": [],
        "current_step": "",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    })

    runner = BatchRunner(store, max_steps=3, context_window=32768)
    builder = ContextPackBuilder(context_window=32768)

    with patch.object(engine._client, "stream_messages") as mock_stream:
        final = runner.resume_supervised(
            goal="Build feature X",
            engine=engine,
            pack_builder=builder,
        )

    mock_stream.assert_not_called()
    assert final["phase"] == "blocked"


def test_test_gate_failing_tests_goto_revise(tmp_path):
    """Test gate should route to revise when tests fail."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)
    next_phase, next_action = runner._test_gate({"test_decision": "failed"})
    assert next_phase == "revise"
    assert "revise" in next_action.lower()


def test_test_gate_failure_flag_goto_revise(tmp_path):
    """Test gate should route to revise when test_failure flag is set."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)
    next_phase, next_action = runner._test_gate({"test_failure": True})
    assert next_phase == "revise"


def test_test_gate_passing_goto_review(tmp_path):
    """Test gate should proceed to review when tests pass."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)
    next_phase, next_action = runner._test_gate({})
    assert next_phase == "review"
    assert "review" in next_action.lower()


def test_review_gate_commit_goto_done(tmp_path):
    """Review gate should allow done when decision is commit."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)
    next_phase, next_action = runner._review_gate({"review_decision": "commit"})
    assert next_phase == "done"
    assert "completed" in next_action.lower()


def test_review_gate_revise_blocked(tmp_path):
    """Review gate should block when decision is revise."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)
    next_phase, next_action = runner._review_gate({"review_decision": "revise"})
    assert next_phase == "blocked"
    assert "revise" in next_action.lower()


def test_review_gate_rollback_blocked(tmp_path):
    """Review gate should block when decision is rollback."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)
    next_phase, next_action = runner._review_gate({"review_decision": "rollback"})
    assert next_phase == "blocked"
    assert "rollback" in next_action.lower()


def test_review_gate_hold_blocked(tmp_path):
    """Review gate should block when decision is hold."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)
    next_phase, next_action = runner._review_gate({"review_decision": "hold"})
    assert next_phase == "blocked"
    assert "hold" in next_action.lower()


def test_review_gate_split_returns_to_plan(tmp_path):
    """Review gate should return to plan when decision is split."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)
    next_phase, next_action = runner._review_gate({"review_decision": "split"})
    assert next_phase == "plan"
    assert "planning" in next_action.lower()


def test_review_gate_reslice_returns_to_plan(tmp_path):
    """Review gate should return to plan when decision is reslice."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)
    next_phase, next_action = runner._review_gate({"review_decision": "reslice"})
    assert next_phase == "plan"


def test_review_gate_no_decision_blocked(tmp_path):
    """Review gate should block when no review decision is recorded."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)
    next_phase, next_action = runner._review_gate({})
    assert next_phase == "blocked"
    assert "incomplete" in next_action.lower()


def test_review_gate_prevents_auto_done_in_run(tmp_path):
    """Without explicit review_decision, runner should not reach done."""
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)
    final = runner.run("Build feature X")
    assert final["phase"] == "blocked"
    assert "incomplete" in final["next_action"].lower()
