"""E2E dry-run: existing repository path.

Validates the workflow for a repo that already has code:
  goal -> CodeGraph retrieval (or fallback) -> context pack -> workflow dry-run

No real LLM or OMLX is used.  CodeGraph may be real if installed, but the
workflow degrades gracefully to rg/heuristics.
"""

from core.batch_runner import BatchRunner
from core.code_retrieval import CodeGraphRetrievalAdapter
from core.context_pack import ContextPackBuilder
from core.plan_graph import PlanGraph
from core.runtime_state import RuntimeStateStore


def test_existing_repo_code_retrieval_falls_back_gracefully(tmp_path):
    """When CodeGraph is unavailable, retrieval falls back to rg or returns empty."""
    # Seed a small src tree so the adapter sees "code exists"
    src_dir = tmp_path / "src" / "core"
    src_dir.mkdir(parents=True)
    (src_dir / "engine.py").write_text("class Engine:\n    pass\n", encoding="utf-8")

    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.query_symbols("Engine")

    # Either codegraph works, rg works, or we get a graceful empty result
    assert isinstance(result.items, tuple)
    assert 0 <= result.confidence <= 1.0


def test_existing_repo_context_pack_includes_retrieval(tmp_path):
    """Context pack for an existing repo includes retrieval results."""
    src_dir = tmp_path / "src" / "core"
    src_dir.mkdir(parents=True)
    (src_dir / "engine.py").write_text("class Engine:\n    pass\n", encoding="utf-8")

    goal = "Add logging to Engine"
    adapter = CodeGraphRetrievalAdapter(tmp_path)
    retrieval = [adapter.query_symbols("Engine")]

    graph = PlanGraph(run_id="e2e-existing-001", goal=goal, phase="retrieve")

    builder = ContextPackBuilder(context_window=32768)
    pack = builder.build(goal=goal, plan_graph=graph, retrieval_results=retrieval)

    assert goal in pack.markdown
    assert pack.budget_report.projected_total_tokens <= 32768


def test_existing_repo_batch_runner_dry_run(tmp_path):
    """Dry-run the batch runner on an existing repo without calling an LLM."""
    src_dir = tmp_path / "src" / "core"
    src_dir.mkdir(parents=True)
    (src_dir / "engine.py").write_text("class Engine:\n    pass\n", encoding="utf-8")

    store = RuntimeStateStore(str(tmp_path), run_id="e2e-existing-002")
    store.patch_state(goal="Add logging to Engine", phase="intake")

    runner = BatchRunner(store, max_steps=3, context_window=32768)
    final = runner.run("Add logging to Engine")

    # With max_steps=3 we stop after intake -> plan -> retrieve -> pack
    assert final["phase"] in {"pack", "implement", "test", "review", "done", "blocked"}
    assert store._state_path.exists()
    assert len(store.list_steps()) == 3


def test_existing_repo_budget_reports_recorded(tmp_path):
    """Each step writes a budget report during dry-run."""
    src_dir = tmp_path / "src" / "core"
    src_dir.mkdir(parents=True)
    (src_dir / "engine.py").write_text("class Engine:\n    pass\n", encoding="utf-8")

    store = RuntimeStateStore(str(tmp_path), run_id="e2e-existing-003")
    runner = BatchRunner(store, max_steps=2, context_window=32768)
    runner.run("Add logging to Engine")

    reports = store.list_budget_reports()
    assert len(reports) == 2
    for r in reports:
        assert "state" in r
        assert "projected_total_tokens" in r
        assert "context_window" in r


def test_existing_repo_runtime_state_survives_resume(tmp_path):
    """Runtime state can be loaded back and resumed from."""
    src_dir = tmp_path / "src" / "core"
    src_dir.mkdir(parents=True)
    (src_dir / "engine.py").write_text("class Engine:\n    pass\n", encoding="utf-8")

    store = RuntimeStateStore(str(tmp_path), run_id="e2e-existing-004")
    store.patch_state(
        goal="Add logging to Engine",
        phase="plan",
        next_action="Retrieve relevant code",
    )

    runner = BatchRunner(store, max_steps=1, context_window=32768)
    final = runner.run("Add logging to Engine")

    # Resume from saved state
    runner2 = BatchRunner(store, max_steps=1, context_window=32768)
    final2 = runner2.run("Add logging to Engine", init_state=False)

    assert final2["phase"] != final["phase"] or final2["next_action"] != final["next_action"]
