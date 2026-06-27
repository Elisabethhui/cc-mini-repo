from __future__ import annotations

import pytest

from core.context_budget import BudgetState
from core.context_pack import ContextPackBuilder, _estimate_tokens
from core.plan_graph import PlanGraph, TaskNode
from core.runtime_state import RuntimeStateStore


class FakeRetrievalResult:
    """Fake retrieval result for testing."""

    def __init__(
        self,
        query_type: str = "symbols",
        query: str = "test",
        ok: bool = True,
        items: tuple[str, ...] = (),
        confidence: float = 0.95,
        truncated: bool = False,
    ):
        self.query_type = query_type
        self.query = query
        self.ok = ok
        self.items = items
        self.confidence = confidence
        self.truncated = truncated


class TestEstimateTokens:
    def test_empty_string(self):
        assert _estimate_tokens("") == 0

    def test_short_text(self):
        assert _estimate_tokens("hello world") == 6

    def test_long_text(self):
        text = "a" * 1800
        assert _estimate_tokens(text) == 1000


class TestContextPackBuilder:
    def test_basic_pack(self, tmp_path):
        builder = ContextPackBuilder(context_window=10000)
        pack = builder.build(goal="Implement feature X")

        assert "# Context Pack" in pack.markdown
        assert "**Goal:** Implement feature X" in pack.markdown
        assert pack.budget_report.state == BudgetState.OK
        assert not pack.truncated
        assert pack.artifact_handles == []

    def test_pack_with_plan_graph(self, tmp_path):
        builder = ContextPackBuilder(context_window=10000)
        pg = PlanGraph(run_id="r1", goal="Build app", phase="charter")
        pg.add_decision("Use Python 3.11")
        pg.add_open_question("Which framework?")
        pg.add_risk("Performance")
        pg.set_next_action("Write tests")
        pg.add_task(TaskNode(id="t1", goal="Set up repo"))

        pack = builder.build(goal="Build app", plan_graph=pg)

        assert "**Goal:** Build app" in pack.markdown
        assert "**Phase:** charter" in pack.markdown
        assert "**Next Action:** Write tests" in pack.markdown
        assert "## Decisions" in pack.markdown
        assert "Use Python 3.11" in pack.markdown
        assert "## Open Questions" in pack.markdown
        assert "Which framework?" in pack.markdown
        assert "## Risks" in pack.markdown
        assert "Performance" in pack.markdown
        assert "## Task Summary" in pack.markdown
        assert "(ready) t1: Set up repo" in pack.markdown
        assert pack.budget_report.state == BudgetState.OK

    def test_pack_with_retrieval_results(self, tmp_path):
        builder = ContextPackBuilder(context_window=10000)
        results = [
            FakeRetrievalResult(
                query_type="symbols",
                query="run_query",
                items=("src/core/engine.py:42:def run_query",),
                confidence=0.95,
            ),
            FakeRetrievalResult(
                query_type="tests",
                query="run_query",
                items=("tests/test_engine.py:10:def test_run_query",),
                confidence=0.85,
            ),
        ]

        pack = builder.build(goal="Fix bug", retrieval_results=results)

        assert "## Relevant Code" in pack.markdown
        assert "src/core/engine.py:42:def run_query" in pack.markdown
        assert "tests/test_engine.py:10:def test_run_query" in pack.markdown
        assert "confidence: 0.95" in pack.markdown

    def test_pack_with_test_recommendations(self, tmp_path):
        builder = ContextPackBuilder(context_window=10000)
        recommendations = ["pytest tests/test_engine.py -v", "pytest tests/test_config.py -v"]

        pack = builder.build(goal="Add config", test_recommendations=recommendations)

        assert "## Test Recommendations" in pack.markdown
        assert "pytest tests/test_engine.py -v" in pack.markdown
        assert "pytest tests/test_config.py -v" in pack.markdown

    def test_pack_with_runtime_state(self, tmp_path):
        builder = ContextPackBuilder(context_window=10000)
        state = {"phase": "implement", "current_step": "Write engine", "next_action": "Run tests"}

        pack = builder.build(goal="Build engine", runtime_state=state)

        assert "## Runtime State" in pack.markdown
        assert "**phase**: implement" in pack.markdown
        assert "**current_step**: Write engine" in pack.markdown

    def test_pack_truncates_when_too_large(self, tmp_path):
        """Small context window should trigger truncation."""
        builder = ContextPackBuilder(
            context_window=500,
            system_prompt_tokens=50,
            tool_schema_tokens=20,
            message_tokens=50,
            reserved_output_tokens=100,
            safety_margin_tokens=50,
        )
        pg = PlanGraph(run_id="r1", goal="x" * 1000)
        pg.add_decision("D1")
        pg.add_decision("D2")
        pg.add_task(TaskNode(id="t1", goal="Task" * 50))

        pack = builder.build(goal="x" * 1000, plan_graph=pg)

        assert pack.truncated is True
        assert len(pack.warnings) > 0
        assert "truncated" in pack.warnings[0].lower()

    def test_pack_externalizes_to_store(self, tmp_path):
        store = RuntimeStateStore(str(tmp_path), run_id="test")
        builder = ContextPackBuilder(
            context_window=600,
            system_prompt_tokens=50,
            tool_schema_tokens=20,
            message_tokens=50,
            reserved_output_tokens=100,
            safety_margin_tokens=50,
        )
        results = [
            FakeRetrievalResult(
                query_type="symbols",
                query="x",
                items=tuple(f"line-{i}" for i in range(100)),
                confidence=0.95,
            ),
        ]

        pack = builder.build(
            goal="Big goal",
            retrieval_results=results,
            store=store,
        )

        # Low-priority retrieval should be externalized
        assert len(pack.artifact_handles) > 0
        assert any("retrieval" in h for h in pack.artifact_handles)

        # Verify artifacts were written
        for handle in pack.artifact_handles:
            assert handle in store.list_artifacts()

    def test_pack_budget_report_within_window(self, tmp_path):
        builder = ContextPackBuilder(context_window=32768)
        pg = PlanGraph(run_id="r1", goal="Build app")
        pg.add_task(TaskNode(id="t1", goal="Step 1"))

        pack = builder.build(goal="Build app", plan_graph=pg)

        assert pack.budget_report.projected_total_tokens <= pack.budget_report.context_window
        assert pack.budget_report.available_input_tokens >= 0
        assert pack.budget_report.packed_context_tokens > 0

    def test_empty_inputs(self, tmp_path):
        builder = ContextPackBuilder(context_window=10000)
        pack = builder.build(goal="Simple goal")

        assert "# Context Pack" in pack.markdown
        assert "**Goal:** Simple goal" in pack.markdown
        assert "## Decisions" not in pack.markdown
        assert "## Relevant Code" not in pack.markdown
        assert "## Test Recommendations" not in pack.markdown
        assert "## Runtime State" not in pack.markdown
        assert "## Task Summary" not in pack.markdown

    def test_large_task_dag_limited_to_10(self, tmp_path):
        builder = ContextPackBuilder(context_window=10000)
        pg = PlanGraph(run_id="r1", goal="Build app")
        for i in range(15):
            pg.add_task(TaskNode(id=f"t{i}", goal=f"Task {i}"))

        pack = builder.build(goal="Build app", plan_graph=pg)

        assert "## Task Summary" in pack.markdown
        # Should show at most 10 tasks + "... and X more"
        task_lines = [l for l in pack.markdown.splitlines() if l.startswith("- (ready)")]
        assert len(task_lines) == 10
        assert "... and 5 more tasks" in pack.markdown

    def test_high_priority_items_always_included(self, tmp_path):
        """P0 and P1 items should never be externalized."""
        store = RuntimeStateStore(str(tmp_path), run_id="test")
        builder = ContextPackBuilder(
            context_window=600,
            system_prompt_tokens=50,
            tool_schema_tokens=20,
            message_tokens=50,
            reserved_output_tokens=100,
            safety_margin_tokens=50,
        )
        pg = PlanGraph(run_id="r1", goal="Build app")
        pg.add_decision("Critical decision")
        pg.add_open_question("Critical question?")

        pack = builder.build(goal="Build app", plan_graph=pg, store=store)

        # P0 and P1 should still be in markdown even with tiny budget
        assert "**Goal:** Build app" in pack.markdown
        assert "## Decisions" in pack.markdown
        assert "Critical decision" in pack.markdown
        assert "## Open Questions" in pack.markdown
        assert "Critical question?" in pack.markdown

    def test_retrieval_results_with_no_items_omitted(self, tmp_path):
        builder = ContextPackBuilder(context_window=10000)
        results = [
            FakeRetrievalResult(ok=True, items=()),
            FakeRetrievalResult(ok=False, items=("a",)),
        ]

        pack = builder.build(goal="Fix bug", retrieval_results=results)

        assert "## Relevant Code" not in pack.markdown

    def test_context_window_configurable(self, tmp_path):
        """Builder should work with different context_window values."""
        for window in [8192, 16384, 32768, 100000]:
            builder = ContextPackBuilder(
                context_window=window,
                reserved_output_tokens=min(2048, window // 4),
                safety_margin_tokens=min(1024, window // 8),
                system_prompt_tokens=min(500, window // 16),
                tool_schema_tokens=min(200, window // 32),
                message_tokens=min(1000, window // 8),
            )
            pack = builder.build(goal="Test")
            assert pack.budget_report.context_window == window
            assert pack.budget_report.projected_total_tokens <= window

    def test_markdown_formatting(self, tmp_path):
        builder = ContextPackBuilder(context_window=10000)
        pg = PlanGraph(run_id="r1", goal="Build app", phase="charter")
        pg.set_next_action("Write code")

        pack = builder.build(goal="Build app", plan_graph=pg)

        lines = pack.markdown.splitlines()
        assert lines[0] == "# Context Pack"
        assert pack.markdown.count("**Goal:**") == 1
        assert pack.markdown.count("**Phase:**") == 1
        assert pack.markdown.count("**Next Action:**") == 1

    def test_artifact_handles_in_markdown(self, tmp_path):
        store = RuntimeStateStore(str(tmp_path), run_id="test")
        builder = ContextPackBuilder(
            context_window=800,
            system_prompt_tokens=50,
            tool_schema_tokens=20,
            message_tokens=50,
            reserved_output_tokens=100,
            safety_margin_tokens=50,
        )
        results = [
            FakeRetrievalResult(
                query_type="symbols",
                query="x",
                items=tuple(f"line-{i}" for i in range(100)),
            ),
        ]

        pack = builder.build(goal="Big goal", retrieval_results=results, store=store)

        if pack.artifact_handles:
            assert "## Externalized Artifacts" in pack.markdown
            for handle in pack.artifact_handles:
                assert f"`{handle}`" in pack.markdown

    def test_truncation_notice(self, tmp_path):
        builder = ContextPackBuilder(
            context_window=500,
            system_prompt_tokens=50,
            tool_schema_tokens=20,
            message_tokens=50,
            reserved_output_tokens=100,
            safety_margin_tokens=50,
        )
        pg = PlanGraph(run_id="r1", goal="x" * 500)
        for i in range(20):
            pg.add_decision(f"Decision {i}: " + "x" * 50)

        pack = builder.build(goal="x" * 500, plan_graph=pg)

        if pack.truncated:
            assert "truncated or externalized" in pack.markdown
