import json

import pytest
from core.context_budget import BudgetState
from core.plan_graph import PlanGraph, TaskNode
from core.plan_preservation import PlanPreservationManager, PlanningPack
from core.runtime_state import RuntimeStateStore


class TestEstimateTokens:
    def test_empty_plan_estimate(self):
        pg = PlanGraph(run_id="r1")
        assert pg.estimate_tokens() > 0

    def test_large_plan_estimate(self):
        pg = PlanGraph(run_id="r1", goal="x" * 10000)
        tokens = pg.estimate_tokens()
        assert tokens > 5000


class TestBudgetCheck:
    def test_ok_state(self):
        pg = PlanGraph(run_id="r1")
        mgr = PlanPreservationManager(pg, context_window=100000)
        assert mgr.check_budget() == BudgetState.OK

    def test_preserve_state(self):
        pg = PlanGraph(run_id="r1", goal="x" * 40000)
        mgr = PlanPreservationManager(pg, context_window=32768)
        state = mgr.check_budget()
        assert state in (BudgetState.PRESERVE, BudgetState.SPLIT, BudgetState.HARD_STOP)

    def test_hard_stop_state(self):
        pg = PlanGraph(run_id="r1", goal="x" * 50000)
        mgr = PlanPreservationManager(pg, context_window=32768)
        state = mgr.check_budget()
        assert state == BudgetState.HARD_STOP


class TestPreserve:
    def test_preserves_to_store(self, tmp_path):
        store = RuntimeStateStore(str(tmp_path), run_id="test-run")
        pg = PlanGraph(run_id="test-run", goal="Build app")
        pg.add_decision("Use Python")
        pg.add_open_question("Which framework?")
        pg.add_module("api")
        pg.add_risk("Scaling")
        pg.set_next_action("Set up repo")
        pg.add_task(TaskNode(id="t1", goal="Step 1"))

        mgr = PlanPreservationManager(pg, store=store)
        pack = mgr.preserve()

        assert pack.run_id == "test-run"
        assert pack.goal == "Build app"
        assert "Use Python" in pack.decisions
        assert "Which framework?" in pack.open_questions
        assert "api" in pack.modules
        assert "Scaling" in pack.risks
        assert pack.next_action == "Set up repo"
        assert len(pack.task_summary) == 1
        assert pack.task_summary[0]["id"] == "t1"

        # Check files were written
        assert (store.base_dir / "plan-graph.json").exists()
        assert (store.base_dir / "planning-pack.json").exists()

    def test_updates_runtime_state(self, tmp_path):
        store = RuntimeStateStore(str(tmp_path), run_id="test-run")
        pg = PlanGraph(run_id="test-run", goal="Build app")
        pg.add_decision("Use Python")
        pg.set_next_action("Set up repo")

        mgr = PlanPreservationManager(pg, store=store)
        mgr.preserve()

        state = store.load_state()
        assert state["goal"] == "Build app"
        assert state["phase"] == "intake"
        assert state["next_action"] == "Set up repo"
        assert "Use Python" in state["decisions"]

    def test_materializes_large_goal(self, tmp_path):
        store = RuntimeStateStore(str(tmp_path), run_id="test-run")
        large_goal = "x" * 10000
        pg = PlanGraph(run_id="test-run", goal=large_goal)

        mgr = PlanPreservationManager(pg, store=store)
        pack = mgr.preserve()

        assert len(pack.artifact_handles) > 0
        assert any("goal" in h for h in pack.artifact_handles)
        assert len(pack.chunk_summaries) > 0

        # Verify artifact was written
        assert "goal.md" in store.list_artifacts()

    def test_materializes_large_constraints(self, tmp_path):
        store = RuntimeStateStore(str(tmp_path), run_id="test-run")
        pg = PlanGraph(run_id="test-run", goal="Build app")
        pg.constraints = ["short", "x" * 10000]

        mgr = PlanPreservationManager(pg, store=store)
        pack = mgr.preserve()

        assert len(pack.artifact_handles) >= 1
        assert any("constraint" in h for h in pack.artifact_handles)

    def test_no_store_no_crash(self):
        pg = PlanGraph(run_id="r1")
        mgr = PlanPreservationManager(pg, store=None)
        pack = mgr.preserve()
        assert pack.run_id == "r1"
        assert pack.artifact_handles == []

    def test_requirements_summary(self):
        pg = PlanGraph(run_id="r1", goal="Build app")
        pg.constraints = ["Use Python 3.11"]
        pg.assumptions = ["Linux only"]
        pg.non_goals = ["Mobile support"]
        pg.acceptance_tests = ["All tests pass"]

        mgr = PlanPreservationManager(pg)
        pack = mgr.preserve()

        assert "Build app" in pack.requirements_summary
        assert "Use Python 3.11" in pack.requirements_summary
        assert "Linux only" in pack.requirements_summary
        assert "Mobile support" in pack.requirements_summary
        assert "All tests pass" in pack.requirements_summary


class TestNextPack:
    def test_next_pack_is_compact(self):
        pg = PlanGraph(run_id="r1", goal="Big project")
        pg.add_decision("D1")
        pg.add_open_question("Q1")
        pg.add_module("mod1")
        pg.add_risk("risk1")
        pg.set_next_action("Do something")
        pg.add_task(TaskNode(id="t1", goal="Task 1"))

        mgr = PlanPreservationManager(pg)
        pack = mgr.create_next_pack()

        assert pack.run_id == "r1"
        assert pack.goal == "Big project"
        assert pack.decisions == ["D1"]
        assert pack.open_questions == ["Q1"]
        assert pack.modules == ["mod1"]
        assert pack.risks == ["risk1"]
        assert pack.next_action == "Do something"
        assert len(pack.task_summary) == 1

    def test_next_pack_truncates_large_goal(self, tmp_path):
        store = RuntimeStateStore(str(tmp_path), run_id="test-run")
        large_goal = "word " * 5000  # ~30000 chars
        pg = PlanGraph(run_id="test-run", goal=large_goal)

        mgr = PlanPreservationManager(pg, store=store)
        pack = mgr.create_next_pack()

        assert len(pack.goal) < len(large_goal)
        assert "[see artifact:" in pack.goal
        assert len(pack.artifact_handles) > 0
        assert len(pack.chunk_summaries) > 0


class TestDeterministicSummarizer:
    def test_chunk_summary_is_deterministic(self):
        text = "First sentence here. Second sentence here. " * 1000
        pg = PlanGraph(run_id="r1", goal=text)
        mgr = PlanPreservationManager(pg)

        summaries1 = mgr._generate_chunk_summaries(text)
        summaries2 = mgr._generate_chunk_summaries(text)

        assert summaries1 == summaries2
        assert len(summaries1) > 0
        assert "words" in summaries1[0]

    def test_requirements_summary_is_deterministic(self):
        pg = PlanGraph(run_id="r1", goal="G", constraints=["C1"], assumptions=["A1"])
        mgr1 = PlanPreservationManager(pg)
        mgr2 = PlanPreservationManager(pg)

        assert mgr1._generate_requirements_summary() == mgr2._generate_requirements_summary()

    def test_small_text_no_chunks(self):
        pg = PlanGraph(run_id="r1", goal="Small goal")
        mgr = PlanPreservationManager(pg)

        summaries = mgr._generate_chunk_summaries("Small goal")
        assert summaries == []


class TestPlanningPackSerialization:
    def test_round_trip(self):
        pack = PlanningPack(
            run_id="r1",
            phase="charter",
            goal="Build app",
            decisions=["Use Python"],
            open_questions=["Q1"],
            modules=["api"],
            risks=["risk1"],
            next_action="Do it",
            task_summary=[{"id": "t1", "goal": "Task 1", "status": "ready"}],
            artifact_handles=["goal.md"],
            requirements_summary="Summary",
            chunk_summaries=["Chunk 1 (10 words)"],
        )

        d = pack.to_dict()
        assert d["run_id"] == "r1"
        assert d["phase"] == "charter"
        assert d["goal"] == "Build app"
        assert d["decisions"] == ["Use Python"]

        json_text = pack.to_json()
        restored = json.loads(json_text)
        assert restored["run_id"] == "r1"
        assert restored["task_summary"][0]["id"] == "t1"
