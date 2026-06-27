from core.batch_runner import BatchRunner
from core.context_budget import BudgetState
from core.runtime_state import RuntimeStateStore


def test_basic_run_reaches_done(tmp_path):
    store = RuntimeStateStore(str(tmp_path), run_id="test")
    runner = BatchRunner(store, max_steps=10, context_window=32768)

    called = []

    def worker(state):
        called.append(state.get("phase"))

    final = runner.run("Build feature X", workers={
        "intake": worker,
        "plan": worker,
        "retrieve": worker,
        "pack": worker,
        "implement": worker,
        "test": worker,
        "review": worker,
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

    runner.run("Build feature X")

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
