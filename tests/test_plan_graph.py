from core.plan_graph import PlanGraph, TaskNode


def test_default_plan_graph():
    pg = PlanGraph(run_id="r1")
    assert pg.run_id == "r1"
    assert pg.phase == "intake"
    assert pg.task_dag == []
    assert pg.decisions == []


def test_task_node_round_trip():
    node = TaskNode(
        id="t1",
        goal="Add config parser",
        depends_on=["t0"],
        allowed_files=["src/core/config.py"],
        forbidden_files=["src/core/engine.py"],
        test_strategy="pytest",
        context_budget_hint=8000,
        acceptance_criteria=["Parses TOML", "Handles missing keys"],
    )
    d = node.to_dict()
    restored = TaskNode.from_dict(d)
    assert restored.id == "t1"
    assert restored.goal == "Add config parser"
    assert restored.depends_on == ["t0"]
    assert restored.allowed_files == ["src/core/config.py"]
    assert restored.forbidden_files == ["src/core/engine.py"]
    assert restored.test_strategy == "pytest"
    assert restored.context_budget_hint == 8000
    assert restored.acceptance_criteria == ["Parses TOML", "Handles missing keys"]


def test_plan_graph_json_round_trip():
    pg = PlanGraph(run_id="run-42", project_name="cc-mini", phase="charter")
    pg.goal = "Build a bounded-context coding runtime"
    pg.non_goals = ["Replace CodeGraph"]
    pg.constraints = ["context_window <= 32768"]
    pg.assumptions = ["Python 3.11+ available"]
    pg.modules = ["runtime_profile", "context_budget"]
    pg.interfaces = ["Engine.submit()"]
    pg.risks = ["Local model too slow"]
    pg.open_questions = ["Which tokenizer?"]
    pg.decisions = ["Use dataclasses"]
    pg.acceptance_tests = ["All tests pass"]
    pg.artifacts = ["docs/architecture.md"]
    pg.next_action = "Write runtime_profile.py"

    pg.add_task(TaskNode(id="t1", goal="Write runtime_profile.py"))
    pg.add_task(TaskNode(id="t2", goal="Write tests", depends_on=["t1"]))

    json_text = pg.to_json()
    restored = PlanGraph.from_json(json_text)

    assert restored.run_id == "run-42"
    assert restored.project_name == "cc-mini"
    assert restored.phase == "charter"
    assert restored.goal == "Build a bounded-context coding runtime"
    assert restored.non_goals == ["Replace CodeGraph"]
    assert restored.constraints == ["context_window <= 32768"]
    assert restored.assumptions == ["Python 3.11+ available"]
    assert restored.modules == ["runtime_profile", "context_budget"]
    assert restored.interfaces == ["Engine.submit()"]
    assert restored.risks == ["Local model too slow"]
    assert restored.open_questions == ["Which tokenizer?"]
    assert restored.decisions == ["Use dataclasses"]
    assert restored.acceptance_tests == ["All tests pass"]
    assert restored.artifacts == ["docs/architecture.md"]
    assert restored.next_action == "Write runtime_profile.py"
    assert len(restored.task_dag) == 2
    assert restored.task_by_id("t1").goal == "Write runtime_profile.py"
    assert restored.task_by_id("t2").depends_on == ["t1"]


def test_incremental_add_and_update_task():
    pg = PlanGraph()
    pg.add_task(TaskNode(id="a", goal="First"))
    pg.add_task(TaskNode(id="b", goal="Second", depends_on=["a"]))

    assert len(pg.task_dag) == 2
    assert pg.update_task("a", goal="Updated first")
    assert pg.task_by_id("a").goal == "Updated first"
    assert not pg.update_task("c", goal="Missing")


def test_remove_task():
    pg = PlanGraph()
    pg.add_task(TaskNode(id="x"))
    assert pg.remove_task("x")
    assert pg.task_by_id("x") is None
    assert not pg.remove_task("y")


def test_add_decision_avoids_duplicates():
    pg = PlanGraph()
    pg.add_decision("Use dataclasses")
    pg.add_decision("Use dataclasses")
    assert pg.decisions == ["Use dataclasses"]


def test_add_open_question_and_resolve():
    pg = PlanGraph()
    pg.add_open_question("Q1")
    pg.add_open_question("Q2")
    assert pg.open_questions == ["Q1", "Q2"]
    assert pg.resolve_open_question("Q1")
    assert pg.open_questions == ["Q2"]
    assert not pg.resolve_open_question("Q3")


def test_add_risk_assumption_module_interface_artifact():
    pg = PlanGraph()
    pg.add_risk("OOM")
    pg.add_risk("OOM")
    pg.add_assumption("Python 3.11")
    pg.add_assumption("Python 3.11")
    pg.add_module("engine")
    pg.add_module("engine")
    pg.add_interface("Engine.submit")
    pg.add_interface("Engine.submit")
    pg.add_artifact("docs/plan.md")
    pg.add_artifact("docs/plan.md")

    assert pg.risks == ["OOM"]
    assert pg.assumptions == ["Python 3.11"]
    assert pg.modules == ["engine"]
    assert pg.interfaces == ["Engine.submit"]
    assert pg.artifacts == ["docs/plan.md"]


def test_ready_tasks():
    pg = PlanGraph()
    pg.add_task(TaskNode(id="a", goal="No deps"))
    pg.add_task(TaskNode(id="b", goal="Depends on a", depends_on=["a"]))
    ready = pg.ready_tasks()
    assert len(ready) == 1
    assert ready[0].id == "a"


def test_topological_order():
    pg = PlanGraph()
    pg.add_task(TaskNode(id="c", goal="Third", depends_on=["b"]))
    pg.add_task(TaskNode(id="a", goal="First"))
    pg.add_task(TaskNode(id="b", goal="Second", depends_on=["a"]))

    order = pg.topological_order()
    ids = [n.id for n in order]
    assert ids.index("a") < ids.index("b")
    assert ids.index("b") < ids.index("c")


def test_topological_order_cycle_ignored():
    pg = PlanGraph()
    pg.add_task(TaskNode(id="a", depends_on=["b"]))
    pg.add_task(TaskNode(id="b", depends_on=["a"]))
    order = pg.topological_order()
    # Kahn's algorithm with cycle returns partial order
    assert len(order) <= 2


def test_set_phase_and_next_action():
    pg = PlanGraph()
    pg.set_phase("implement")
    pg.set_next_action("Write tests")
    assert pg.phase == "implement"
    assert pg.next_action == "Write tests"


def test_from_json_ignores_unknown_fields():
    import json
    raw = json.dumps({
        "run_id": "r1",
        "phase": "charter",
        "unknown_field": "ignored",
        "task_dag": [{"id": "t1", "goal": "G"}],
    })
    pg = PlanGraph.from_json(raw)
    assert pg.run_id == "r1"
    assert pg.phase == "charter"
    assert pg.task_by_id("t1").goal == "G"


def test_estimate_tokens():
    pg = PlanGraph(run_id="r1")
    empty_tokens = pg.estimate_tokens()
    assert empty_tokens > 0

    pg.goal = "x" * 10000
    large_tokens = pg.estimate_tokens()
    assert large_tokens > empty_tokens
    assert large_tokens > 5000


def test_to_preservation_dict():
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_decision("Use Python")
    pg.add_open_question("Q?")
    pg.add_module("api")
    pg.add_risk("risk1")
    pg.set_next_action("Do it")

    d = pg.to_preservation_dict()
    assert d["run_id"] == "r1"
    assert d["goal"] == "Build app"
    assert d["decisions"] == ["Use Python"]
    assert d["open_questions"] == ["Q?"]
    assert d["modules"] == ["api"]
    assert d["risks"] == ["risk1"]
    assert d["next_action"] == "Do it"
    assert "task_dag" not in d
    assert "artifacts" not in d
    assert "acceptance_tests" not in d
