from __future__ import annotations

import pytest

from core.dev_contract import TaskResult, TaskSpec, VerificationSpec
from core.runtime_state import RuntimeStateStore
from core.task_spec_store import TaskSpecStore


def _make_spec(task_id: str = "t1", **overrides) -> TaskSpec:
    defaults = {
        "id": task_id,
        "goal": "Add module",
        "task_kind": "coding",
        "task_type": "create",
        "executable": True,
        "planning_required": False,
        "allowed_files": ["src/mod.py"],
        "forbidden_files": [],
        "context_budget": 8000,
        "verification": VerificationSpec(kind="command", command=["echo", "ok"]),
        "confidence": 0.8,
    }
    defaults.update(overrides)
    return TaskSpec(**defaults)


def _make_store(tmp_path):
    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    return TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)


# ---------------------------------------------------------------------------
# TaskSpec persistence
# ---------------------------------------------------------------------------

def test_save_and_load_task_spec(tmp_path):
    store = _make_store(tmp_path)
    spec = _make_spec("task-001")

    path = store.save_task_spec(spec)

    assert path.exists()
    loaded = store.load_task_spec("task-001")
    assert loaded is not None
    assert loaded.id == "task-001"
    assert loaded.goal == spec.goal
    assert loaded.executable is True


def test_list_task_specs_sorted(tmp_path):
    store = _make_store(tmp_path)
    store.save_task_spec(_make_spec("task-c"))
    store.save_task_spec(_make_spec("task-a"))
    store.save_task_spec(_make_spec("task-b"))

    specs = store.list_task_specs()
    ids = [s.id for s in specs]
    assert ids == ["task-a", "task-b", "task-c"]


def test_existing_task_not_overwritten_by_default(tmp_path):
    store = _make_store(tmp_path)
    spec = _make_spec("task-001", goal="First")
    store.save_task_spec(spec)

    spec2 = _make_spec("task-001", goal="Second")
    with pytest.raises(FileExistsError):
        store.save_task_spec(spec2)

    loaded = store.load_task_spec("task-001")
    assert loaded.goal == "First"


def test_allow_overwrite_true_updates_task(tmp_path):
    store = _make_store(tmp_path)
    spec = _make_spec("task-001", goal="First")
    store.save_task_spec(spec)

    spec2 = _make_spec("task-001", goal="Second")
    store.save_task_spec(spec2, allow_overwrite=True)

    loaded = store.load_task_spec("task-001")
    assert loaded.goal == "Second"


@pytest.mark.parametrize(
    "bad_id",
    [
        "../task",
        "/tmp/task",
        ".git/config",
        "",
        "a/b",
    ],
)
def test_invalid_task_id_rejected_for_save(tmp_path, bad_id):
    store = _make_store(tmp_path)
    spec = _make_spec(bad_id)
    with pytest.raises(ValueError):
        store.save_task_spec(spec)


@pytest.mark.parametrize(
    "bad_id",
    [
        "../task",
        "/tmp/task",
        ".git/config",
        "",
        "a/b",
    ],
)
def test_invalid_task_id_rejected_for_load(tmp_path, bad_id):
    store = _make_store(tmp_path)
    with pytest.raises(ValueError):
        store.load_task_spec(bad_id)


# ---------------------------------------------------------------------------
# TaskResult persistence
# ---------------------------------------------------------------------------

def test_save_and_load_task_result(tmp_path):
    store = _make_store(tmp_path)
    result = TaskResult(
        task_id="task-001",
        status="passed",
        changed_files=["src/mod.py"],
        verification_passed=True,
    )

    path = store.save_task_result(result)

    assert path.exists()
    loaded = store.load_task_result("task-001")
    assert loaded is not None
    assert loaded.status == "passed"
    assert loaded.changed_files == ["src/mod.py"]


def test_list_task_results(tmp_path):
    store = _make_store(tmp_path)
    store.save_task_result(TaskResult(task_id="task-b", status="passed"))
    store.save_task_result(TaskResult(task_id="task-a", status="failed"))

    results = store.list_task_results()
    ids = [r.task_id for r in results]
    assert ids == ["task-a", "task-b"]


# ---------------------------------------------------------------------------
# Status queries
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "status",
    ["passed", "failed", "blocked", "split", "needs_planning"],
)
def test_get_task_status_returns_result_status(tmp_path, status):
    store = _make_store(tmp_path)
    store.save_task_result(TaskResult(task_id="task-001", status=status))

    assert store.get_task_status("task-001") == status


def test_get_task_status_pending_when_no_result(tmp_path):
    store = _make_store(tmp_path)
    assert store.get_task_status("task-001") == "pending"


# ---------------------------------------------------------------------------
# Ready / blocked task queries
# ---------------------------------------------------------------------------

def test_ready_task_no_dependencies(tmp_path):
    store = _make_store(tmp_path)
    store.save_task_spec(_make_spec("task-001"))

    ready = store.list_ready_tasks()
    assert len(ready) == 1
    assert ready[0].id == "task-001"


def test_ready_task_with_passed_dependency(tmp_path):
    store = _make_store(tmp_path)
    store.save_task_spec(_make_spec("task-001"))
    store.save_task_spec(_make_spec("task-002", depends_on=["task-001"]))
    store.save_task_result(TaskResult(task_id="task-001", status="passed"))

    ready = store.list_ready_tasks()
    ids = [s.id for s in ready]
    assert "task-002" in ids


def test_not_ready_when_dependency_pending(tmp_path):
    store = _make_store(tmp_path)
    store.save_task_spec(_make_spec("task-001"))
    store.save_task_spec(_make_spec("task-002", depends_on=["task-001"]))

    ready = store.list_ready_tasks()
    ids = [s.id for s in ready]
    assert "task-002" not in ids


def test_not_ready_when_dependency_failed(tmp_path):
    store = _make_store(tmp_path)
    store.save_task_spec(_make_spec("task-001"))
    store.save_task_spec(_make_spec("task-002", depends_on=["task-001"]))
    store.save_task_result(TaskResult(task_id="task-001", status="failed"))

    ready = store.list_ready_tasks()
    ids = [s.id for s in ready]
    assert "task-002" not in ids


def test_planning_required_not_ready(tmp_path):
    store = _make_store(tmp_path)
    store.save_task_spec(_make_spec("task-001", planning_required=True, executable=False))

    ready = store.list_ready_tasks()
    assert not ready


def test_not_executable_not_ready(tmp_path):
    store = _make_store(tmp_path)
    store.save_task_spec(_make_spec("task-001", executable=False))

    ready = store.list_ready_tasks()
    assert not ready


def test_terminal_result_not_ready(tmp_path):
    store = _make_store(tmp_path)
    store.save_task_spec(_make_spec("task-001"))
    store.save_task_result(TaskResult(task_id="task-001", status="passed"))

    ready = store.list_ready_tasks()
    assert not ready


def test_blocked_tasks_excludes_ready_and_terminal(tmp_path):
    store = _make_store(tmp_path)
    store.save_task_spec(_make_spec("task-ready"))
    store.save_task_spec(_make_spec("task-blocked", executable=False))
    store.save_task_spec(_make_spec("task-done"))
    store.save_task_result(TaskResult(task_id="task-done", status="passed"))

    blocked = store.list_blocked_tasks()
    ids = {s.id for s in blocked}
    assert "task-blocked" in ids
    assert "task-ready" not in ids
    assert "task-done" not in ids


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------

def test_all_paths_under_runtime_base(tmp_path):
    store = _make_store(tmp_path)
    store.save_task_spec(_make_spec("task-001"))
    store.save_task_result(TaskResult(task_id="task-001", status="passed"))

    base = store.base_dir.resolve()
    task_path = (store._tasks_dir / "task-001.json").resolve()
    result_path = (store._results_dir / "task-001" / "task-result.json").resolve()

    assert str(task_path).startswith(str(base))
    assert str(result_path).startswith(str(base))
