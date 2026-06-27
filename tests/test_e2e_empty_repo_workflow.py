"""E2E dry-run: empty repository path.

Validates the workflow for a brand-new project with no existing code:
  goal -> PlanGraph -> task DAG -> context pack

No real LLM, CodeGraph, or OMLX is used.
"""

from core.plan_graph import PlanGraph, TaskNode
from core.context_pack import ContextPackBuilder
from core.runtime_state import RuntimeStateStore


def test_empty_repo_plan_graph_and_task_dag(tmp_path):
    """An empty repo can produce a PlanGraph with a task DAG."""
    goal = "Build a minimal task tracker CLI"

    graph = PlanGraph(
        run_id="e2e-empty-001",
        goal=goal,
        phase="plan",
        next_action="Define architecture slices",
    )
    graph.add_decision("Use argparse for CLI")
    graph.add_open_question("Should tasks persist to disk?")
    graph.add_risk("Scope creep on UI features")

    # Task DAG
    graph.add_task(TaskNode(id="t1", goal="Set up project structure", depends_on=[]))
    graph.add_task(TaskNode(id="t2", goal="Implement add command", depends_on=["t1"]))
    graph.add_task(TaskNode(id="t3", goal="Implement list command", depends_on=["t1"]))
    graph.add_task(TaskNode(id="t4", goal="Add persistence", depends_on=["t2", "t3"]))

    assert graph.run_id == "e2e-empty-001"
    assert graph.goal == goal
    assert len(graph.task_dag) == 4
    assert len(graph.ready_tasks()) == 1  # t1 has no deps
    assert len(graph.topological_order()) == 4


def test_empty_repo_context_pack_within_budget(tmp_path):
    """Context pack for an empty repo fits within a configurable window."""
    goal = "Build a minimal task tracker CLI"

    graph = PlanGraph(
        run_id="e2e-empty-002",
        goal=goal,
        phase="plan",
        next_action="Define architecture slices",
    )
    graph.add_task(TaskNode(id="t1", goal="Set up project structure", depends_on=[]))
    graph.add_task(TaskNode(id="t2", goal="Implement add command", depends_on=["t1"]))

    # Use a small window to force truncation behavior
    builder = ContextPackBuilder(
        context_window=4096,
        reserved_output_tokens=512,
        safety_margin_tokens=256,
    )
    pack = builder.build(goal=goal, plan_graph=graph)

    assert pack.budget_report.state.value in ("ok", "warning")
    assert pack.budget_report.projected_total_tokens <= 4096
    assert goal in pack.markdown
    assert "t1" in pack.markdown or "t2" in pack.markdown


def test_empty_repo_runtime_state_persisted(tmp_path):
    """Runtime state is saved and recoverable for an empty-repo plan."""
    store = RuntimeStateStore(str(tmp_path), run_id="e2e-empty-003")
    store.save_state({
        "run_id": "e2e-empty-003",
        "phase": "plan",
        "goal": "Build a minimal task tracker CLI",
        "next_action": "Define architecture slices",
        "decisions": ["Use argparse for CLI"],
        "open_questions": ["Should tasks persist to disk?"],
        "artifacts": [],
        "budget_reports": [],
        "current_step": "",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    })

    loaded = store.load_state()
    assert loaded["phase"] == "plan"
    assert loaded["goal"] == "Build a minimal task tracker CLI"
    assert loaded["decisions"] == ["Use argparse for CLI"]


def test_empty_repo_plan_graph_json_round_trip(tmp_path):
    """PlanGraph serializes and deserializes correctly."""
    graph = PlanGraph(
        run_id="e2e-empty-004",
        goal="Build a minimal task tracker CLI",
        phase="plan",
        next_action="Define architecture slices",
    )
    graph.add_task(TaskNode(id="t1", goal="Set up project structure", depends_on=[]))
    graph.add_decision("Use argparse")

    json_text = graph.to_json()
    restored = PlanGraph.from_json(json_text)

    assert restored.run_id == graph.run_id
    assert restored.goal == graph.goal
    assert len(restored.task_dag) == len(graph.task_dag)
    assert restored.decisions == graph.decisions
