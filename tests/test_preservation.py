from pathlib import Path

import pytest

from core.preservation import PreservationPipeline, _extract_structured_summary, _materialise_large_tool_results, _prune_old_tool_results
from core.context_budget import BudgetState, BudgetReport
from core.runtime_state import RuntimeStateStore


def test_warning_prunes_old_tool_results(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="warn-run")
    pipeline = PreservationPipeline(state_store=store)

    long_content = "x" * 10_000
    messages = [
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tu1", "content": long_content}]},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "next"},
    ]

    result = pipeline.run(BudgetState.WARNING, messages, current_step="s1")
    assert "Continue with reduced context" in result.next_action
    # Old tool result should be truncated in place
    assert messages[0]["content"][0]["content"].endswith("[...truncated from 10000 chars]")


def test_preserve_extracts_structured_state_and_saves(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="preserve-run")
    pipeline = PreservationPipeline(state_store=store)

    messages = [
        {"role": "user", "content": "Let's edit src/core/engine.py and add a new class Foo."},
        {"role": "assistant", "content": "Done. I also created tests/test_foo.py."},
    ]

    result = pipeline.run(
        BudgetState.PRESERVE,
        messages,
        goal="Add Foo feature",
        phase="implement",
        current_step="step-3",
        decisions=["Use dataclass"],
        open_questions=["Should we add validation?"],
        artifacts=["src/core/engine.py"],
    )

    assert "Review preserved state" in result.next_action
    assert result.saved_paths
    assert (tmp_path / ".ai-dev" / "runtime" / "preserve-run" / "state.json").exists()

    state = store.load_state()
    assert state["goal"] == "Add Foo feature"
    assert state["phase"] == "implement"
    assert state["current_step"] == "step-3"
    assert state["decisions"] == ["Use dataclass"]
    assert state["open_questions"] == ["Should we add validation?"]
    assert state["artifacts"] == ["src/core/engine.py"]


def test_preserve_materialises_large_tool_results(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="artifact-run")
    pipeline = PreservationPipeline(state_store=store)

    long_output = "line\n" * 5_000  # ~30k chars
    messages = [
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "tu_big", "content": long_output}
        ]},
    ]

    result = pipeline.run(BudgetState.PRESERVE, messages, current_step="s1")
    assert result.artifact_handles
    assert "tool_result_tu_big.txt" in result.artifact_handles[0]

    # The message content should now be a handle, not the full text
    assert messages[0]["content"][0]["content"].startswith("[artifact:")
    assert "Original output was" in messages[0]["content"][0]["content"]

    # Artifact file should exist
    assert "tool_result_tu_big.txt" in store.list_artifacts()


def test_split_recommends_batches_and_saves(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="split-run")
    pipeline = PreservationPipeline(state_store=store)

    result = pipeline.run(
        BudgetState.SPLIT,
        messages=[],
        goal="Refactor everything",
        phase="plan",
        current_step="step-1",
    )

    assert "Split current task" in result.next_action
    assert result.saved_paths
    state = store.load_state()
    assert state["goal"] == "Refactor everything"
    assert state["next_action"] == "Split current task into smaller executable batches."
    assert (tmp_path / ".ai-dev" / "runtime" / "split-run" / "steps" / "split-step-1.md").exists()


def test_hard_stop_requires_human_decision(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="hard-run")
    pipeline = PreservationPipeline(state_store=store)

    result = pipeline.run(
        BudgetState.HARD_STOP,
        messages=[],
        goal="Add huge feature",
        phase="implement",
        current_step="step-5",
    )

    assert "HARD_STOP" in result.next_action
    assert "Human decision required" in result.next_action
    state = store.load_state()
    assert "HARD_STOP" in state["next_action"]


def test_ok_returns_continue_normally():
    pipeline = PreservationPipeline(state_store=None)
    result = pipeline.run(BudgetState.OK, messages=[])
    assert result.next_action == "Continue normally."
    assert not result.saved_paths


def test_extract_structured_summary_finds_files_and_symbols():
    messages = [
        {"role": "user", "content": 'file:"src/core/config.py" something'},
        {"role": "assistant", "content": [
            {"type": "text", "text": 'Done. I also modified "tests/test_config.py". file:"README.md"'}
        ]},
    ]
    summary = _extract_structured_summary(messages)
    assert "src/core/config.py" in summary["files_seen"]
    assert "tests/test_config.py" in summary["files_seen"]
    assert "README.md" in summary["files_seen"]


def test_extract_structured_summary_finds_symbols():
    messages = [
        {"role": "assistant", "content": "```python\nclass Foo:\n    pass\n\ndef bar():\n    pass\n```"},
    ]
    summary = _extract_structured_summary(messages)
    assert "class Foo" in summary["symbols_seen"]
    assert "def bar" in summary["symbols_seen"]


def test_materialise_large_tool_results_without_store():
    # When store is None, nothing should happen
    messages = [
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "tu1", "content": "x" * 10_000}
        ]},
    ]
    handles = _materialise_large_tool_results(messages, None)  # type: ignore[arg-type]
    assert handles == []
    # Content should be untouched
    assert len(messages[0]["content"][0]["content"]) == 10_000
