from pathlib import Path

import pytest

from core.runtime_state import RuntimeStateStore, PathTraversalError, _generate_run_id


def test_default_state_has_required_keys(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="test-run")
    state = store.default_state()
    assert state["run_id"] == "test-run"
    assert state["phase"] == "intake"
    assert state["current_step"] == ""
    assert state["goal"] == ""
    assert state["decisions"] == []
    assert state["open_questions"] == []
    assert state["artifacts"] == []
    assert state["budget_reports"] == []
    assert state["next_action"] == ""
    assert "created_at" in state
    assert "updated_at" in state


def test_load_state_returns_default_when_missing(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="missing")
    state = store.load_state()
    assert state["run_id"] == "missing"
    assert state["phase"] == "intake"


def test_save_and_load_state_round_trip(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="round-trip")
    data = {
        "run_id": "round-trip",
        "phase": "implement",
        "current_step": "step-3",
        "goal": "Add feature X",
        "decisions": ["Use dataclasses"],
        "open_questions": ["How to handle errors?"],
        "artifacts": ["src/core/feature.py"],
        "budget_reports": [],
        "next_action": "Run tests",
    }
    store.save_state(data)
    loaded = store.load_state()
    assert loaded["phase"] == "implement"
    assert loaded["current_step"] == "step-3"
    assert loaded["goal"] == "Add feature X"
    assert loaded["decisions"] == ["Use dataclasses"]
    assert loaded["open_questions"] == ["How to handle errors?"]
    assert loaded["artifacts"] == ["src/core/feature.py"]
    assert loaded["next_action"] == "Run tests"
    # File should exist under .ai-dev/runtime/<run-id>/
    assert (tmp_path / ".ai-dev" / "runtime" / "round-trip" / "state.json").exists()


def test_patch_state_merges_updates(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="patch")
    store.patch_state(phase="test", current_step="step-2")
    state = store.load_state()
    assert state["phase"] == "test"
    assert state["current_step"] == "step-2"
    assert state["goal"] == ""  # default preserved


def test_append_budget_report(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="budget")
    store.append_budget_report({"projected_total": 1000, "state": "ok"})
    store.append_budget_report({"projected_total": 5000, "state": "warning"})
    reports = store.list_budget_reports()
    assert len(reports) == 2
    assert reports[0]["state"] == "ok"
    assert reports[1]["state"] == "warning"


def test_list_budget_reports_empty_when_none(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="empty-budget")
    assert store.list_budget_reports() == []


def test_write_and_read_step_log(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="steps")
    path = store.write_step_log("step-001", "# Step 1\n\nDid something.\n")
    assert path.name == "step-001.md"
    content = store.read_step_log("step-001")
    assert "Did something." in content


def test_list_steps_returns_sorted_names(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="step-list")
    store.write_step_log("step-002", "content B")
    store.write_step_log("step-001", "content A")
    assert store.list_steps() == ["step-001.md", "step-002.md"]


def test_step_log_sanitises_unsafe_names(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="sanitise")
    path = store.write_step_log("../../etc/passwd", "evil")
    assert path.name == "etc_passwd.md"
    assert "etc_passwd.md" in store.list_steps()


def test_write_and_read_artifact(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="artifacts")
    path = store.write_artifact("summary.txt", "This is a summary.")
    assert path.name == "summary.txt"
    assert store.read_artifact("summary.txt") == "This is a summary."


def test_list_artifacts_returns_sorted_names(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="artifact-list")
    store.write_artifact("b.txt", "B")
    store.write_artifact("a.txt", "A")
    assert store.list_artifacts() == ["a.txt", "b.txt"]


def test_artifact_sanitises_unsafe_names(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="sanitise-artifact")
    # "../secret.txt" becomes ".._secret.txt" after sub, then falls back to
    # "artifact" because it starts with a dot — hidden files are not allowed.
    path = store.write_artifact("../secret.txt", "evil")
    assert path.name == "artifact"
    # Slashes are replaced with underscores; dots inside the name are kept.
    path2 = store.write_artifact("foo/../secret.txt", "evil")
    assert path2.name == "foo_.._secret.txt"


def test_path_traversal_dot_dot_rejected(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="traversal")
    with pytest.raises(PathTraversalError):
        store._validate_within_base("../outside.txt")
    with pytest.raises(PathTraversalError):
        store._validate_within_base("foo/../../outside.txt")


def test_path_traversal_absolute_rejected(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="absolute")
    with pytest.raises(PathTraversalError):
        store._validate_within_base("/etc/passwd")


def test_generate_run_id_format():
    rid = _generate_run_id()
    assert len(rid) == 15  # YYYYMMDD-HHMMSS
    assert rid[8] == "-"


def test_store_uses_provided_run_id(tmp_path: Path):
    store = RuntimeStateStore(tmp_path, run_id="custom-123")
    assert store.run_id == "custom-123"
    assert store.base_dir.name == "custom-123"


def test_store_generates_run_id_when_none(tmp_path: Path):
    store = RuntimeStateStore(tmp_path)
    assert store.run_id
    assert len(store.run_id) == 15


def test_list_runs_returns_sorted_run_ids_with_state_json(tmp_path: Path):
    # Create two runs with state.json
    store_a = RuntimeStateStore(tmp_path, run_id="run-a")
    store_a.save_state(store_a.default_state())

    store_b = RuntimeStateStore(tmp_path, run_id="run-b")
    store_b.save_state(store_b.default_state())

    # Create a directory without state.json (should be ignored)
    (tmp_path / ".ai-dev" / "runtime" / "empty-run").mkdir(parents=True)

    runs = RuntimeStateStore.list_runs(tmp_path)
    assert runs == ["run-a", "run-b"]


def test_list_runs_returns_empty_when_no_runtime_dir(tmp_path: Path):
    runs = RuntimeStateStore.list_runs(tmp_path)
    assert runs == []
