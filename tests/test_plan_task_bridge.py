from __future__ import annotations

import pytest

from core.dev_contract import TaskResult, VerificationSpec
from core.plan_graph import PlanGraph, TaskNode
from core.plan_task_bridge import PlanToTaskBridge, _derive_context_budget


# ---------------------------------------------------------------------------
# from_goal tests
# ---------------------------------------------------------------------------

def test_from_goal_returns_planning_intake():
    specs = PlanToTaskBridge.from_goal(
        goal="Build something", run_id="r1", context_window=32768
    )
    assert len(specs) == 1
    spec = specs[0]
    assert spec.id == "task-001-intake"
    assert spec.task_kind == "planning"
    assert spec.task_type == "intake"
    assert spec.executable is False
    assert spec.planning_required is True
    assert spec.verification.kind == "contract"
    assert "Goal is refined into executable TaskSpecs" in spec.done_definition
    assert spec.run_id == "r1"


def test_from_goal_does_not_generate_business_files_for_flask():
    specs = PlanToTaskBridge.from_goal(
        goal="创建 Flask 图片上传服务", run_id="r1", context_window=32768
    )
    assert len(specs) == 1
    spec = specs[0]
    # Must NOT invent app.py, requirements.txt, etc.
    for forbidden in ("app.py", "requirements.txt", "tests/test_app.py"):
        assert forbidden not in spec.allowed_files
        assert forbidden not in spec.forbidden_files
        assert forbidden not in " ".join(spec.risks)
        assert forbidden not in spec.goal


def test_from_goal_does_not_generate_business_files_for_react():
    specs = PlanToTaskBridge.from_goal(
        goal="Create a React image upload component", run_id="r2", context_window=32768
    )
    assert len(specs) == 1
    spec = specs[0]
    for forbidden in ("App.jsx", "package.json", "src/components"):
        assert forbidden not in spec.allowed_files
        assert forbidden not in spec.forbidden_files


def test_from_goal_is_stable_across_different_goals():
    goals = [
        "Build a CLI tool",
        "Create a Django REST API",
        "Fix a bug in the auth module",
        "Refactor the database layer",
    ]
    for g in goals:
        specs = PlanToTaskBridge.from_goal(goal=g, run_id="r", context_window=32768)
        assert len(specs) == 1
        assert specs[0].planning_required is True
        assert specs[0].executable is False


# ---------------------------------------------------------------------------
# from_plan_graph with task_dag
# ---------------------------------------------------------------------------

def test_from_plan_graph_with_empty_dag_returns_intake():
    pg = PlanGraph(run_id="r1", goal="Build app")
    specs = PlanToTaskBridge.from_plan_graph(pg, context_window=32768)
    assert len(specs) == 1
    assert specs[0].planning_required is True
    assert specs[0].task_type == "intake"


def test_from_plan_graph_converts_task_nodes():
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(TaskNode(id="t1", goal="Add config"))
    pg.add_task(TaskNode(id="t2", goal="Add tests", depends_on=["t1"]))

    specs = PlanToTaskBridge.from_plan_graph(pg, context_window=32768)
    assert len(specs) == 2
    ids = {s.id for s in specs}
    assert ids == {"t1", "t2"}


def test_from_plan_graph_executable_when_files_and_strategy_present():
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(
        TaskNode(
            id="t1",
            goal="Add config",
            allowed_files=["src/core/config.py"],
            test_strategy="pytest tests/test_config.py",
            acceptance_criteria=["Parses TOML"],
        )
    )

    specs = PlanToTaskBridge.from_plan_graph(pg, context_window=32768)
    assert len(specs) == 1
    spec = specs[0]
    assert spec.executable is True
    assert spec.planning_required is False
    assert spec.verification.kind == "command"
    assert spec.verification.command == ["pytest", "tests/test_config.py"]
    assert spec.allowed_files == ["src/core/config.py"]
    assert "Parses TOML" in spec.done_definition


def test_from_plan_graph_not_executable_when_missing_allowed_files():
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(
        TaskNode(
            id="t1",
            goal="Add config",
            allowed_files=[],
            test_strategy="pytest tests/test_config.py",
        )
    )

    specs = PlanToTaskBridge.from_plan_graph(pg, context_window=32768)
    spec = specs[0]
    assert spec.executable is False
    assert any("allowed_files" in r for r in spec.risks)


def test_from_plan_graph_not_executable_when_missing_test_strategy():
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(
        TaskNode(
            id="t1",
            goal="Add config",
            allowed_files=["src/core/config.py"],
            test_strategy="",
        )
    )

    specs = PlanToTaskBridge.from_plan_graph(pg, context_window=32768)
    spec = specs[0]
    assert spec.executable is False
    assert any("test_strategy" in r for r in spec.risks)


# ---------------------------------------------------------------------------
# Budget / context_window tests
# ---------------------------------------------------------------------------

def test_context_budget_capped_when_hint_exceeds_window():
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(
        TaskNode(
            id="t1",
            goal="Big task",
            allowed_files=["src/a.py"],
            test_strategy="pytest",
            context_budget_hint=50000,
        )
    )

    specs = PlanToTaskBridge.from_plan_graph(pg, context_window=32768)
    spec = specs[0]
    # Available budget for 32768 window is 32768 - 2048 - 1024 = 29696
    assert spec.context_budget <= 29696
    assert any("capped" in r.lower() for r in spec.risks)


def test_context_budget_risk_when_window_too_small():
    specs = PlanToTaskBridge.from_goal(
        goal="Tiny", run_id="r1", context_window=1000
    )
    spec = specs[0]
    assert spec.context_budget > 0
    assert any("insufficient headroom" in r.lower() for r in spec.risks)


def test_derive_context_budget_with_zero_hint():
    budget, risks = _derive_context_budget(context_window=32768, hint=0, num_tasks=2)
    assert budget > 0
    assert budget <= 32768 - 2048 - 1024
    assert not risks


# ---------------------------------------------------------------------------
# update_plan_with_task_results tests
# ---------------------------------------------------------------------------

def test_update_plan_passed_becomes_decision():
    pg = PlanGraph(run_id="r1", goal="Build app")
    result = TaskResult(task_id="t1", status="passed", notes="All good")
    PlanToTaskBridge.update_plan_with_task_results(pg, [result])
    assert any("t1 passed" in d for d in pg.decisions)


def test_update_plan_failed_becomes_risk():
    pg = PlanGraph(run_id="r1", goal="Build app")
    result = TaskResult(task_id="t1", status="failed", notes="Broke")
    PlanToTaskBridge.update_plan_with_task_results(pg, [result])
    assert any("t1 failed" in r for r in pg.risks)


def test_update_plan_blocked_updates_next_action():
    pg = PlanGraph(run_id="r1", goal="Build app")
    result = TaskResult(
        task_id="t1", status="blocked", next_action="Revisit architecture"
    )
    PlanToTaskBridge.update_plan_with_task_results(pg, [result])
    assert pg.next_action == "Revisit architecture"


def test_update_plan_split_updates_next_action():
    pg = PlanGraph(run_id="r1", goal="Build app")
    result = TaskResult(task_id="t1", status="split")
    PlanToTaskBridge.update_plan_with_task_results(pg, [result])
    assert "split" in pg.next_action.lower()


def test_update_plan_needs_planning_updates_next_action():
    pg = PlanGraph(run_id="r1", goal="Build app")
    result = TaskResult(task_id="t1", status="needs_planning")
    PlanToTaskBridge.update_plan_with_task_results(pg, [result])
    assert "needs_planning" in pg.next_action.lower()


def test_update_plan_does_not_remove_tasks():
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(TaskNode(id="t1", goal="Do it"))
    result = TaskResult(task_id="t1", status="passed")
    PlanToTaskBridge.update_plan_with_task_results(pg, [result])
    assert pg.task_by_id("t1") is not None


def test_update_plan_failed_with_risks_appends_all():
    pg = PlanGraph(run_id="r1", goal="Build app")
    result = TaskResult(
        task_id="t1", status="failed", risks=["Race condition", "Memory leak"]
    )
    PlanToTaskBridge.update_plan_with_task_results(pg, [result])
    assert any("Race condition" in r for r in pg.risks)
    assert any("Memory leak" in r for r in pg.risks)


def test_update_plan_unknown_status_becomes_open_question():
    pg = PlanGraph(run_id="r1", goal="Build app")
    result = TaskResult(task_id="t1", status="unknown")
    PlanToTaskBridge.update_plan_with_task_results(pg, [result])
    assert any("unknown" in q for q in pg.open_questions)
