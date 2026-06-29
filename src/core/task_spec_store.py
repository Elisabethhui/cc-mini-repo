from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dev_contract import TaskResult, TaskSpec
from .runtime_state import RuntimeStateStore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskSpecStore:
    """Persistent store for TaskSpecs and TaskResults within a runtime run.

    Directory layout (under ``.ai-dev/runtime/<run-id>/``):

    .. code-block:: text

        tasks/
            <task-id>.json
        task-index.json
        results/
            <task-id>/
                task-result.json
        task-results-index.json
    """

    def __init__(
        self,
        workspace: Path,
        runtime_store: RuntimeStateStore | None = None,
    ):
        self.workspace = workspace.resolve()
        if runtime_store is not None:
            self.base_dir = runtime_store.base_dir
        else:
            self.base_dir = self.workspace / ".ai-dev" / "runtime" / "default"
        self._tasks_dir = self.base_dir / "tasks"
        self._results_dir = self.base_dir / "results"
        self._task_index_path = self.base_dir / "task-index.json"
        self._task_results_index_path = self.base_dir / "task-results-index.json"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_dirs(self) -> None:
        self._tasks_dir.mkdir(parents=True, exist_ok=True)
        self._results_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_task_id(task_id: str) -> None:
        if not task_id:
            raise ValueError("task_id must not be empty")
        if task_id.startswith("/"):
            raise ValueError(f"task_id must not be absolute: {task_id!r}")
        if ".." in task_id.split("/") or ".." in task_id.split("\\"):
            raise ValueError(f"task_id must not contain '..': {task_id!r}")
        if "/" in task_id or "\\" in task_id:
            raise ValueError(f"task_id must not contain path separators: {task_id!r}")

    def _load_task_index(self) -> dict[str, Any]:
        if not self._task_index_path.exists():
            return {"tasks": []}
        try:
            return json.loads(self._task_index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"tasks": []}

    def _save_task_index(self, index: dict[str, Any]) -> None:
        self._task_index_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _load_task_results_index(self) -> dict[str, Any]:
        if not self._task_results_index_path.exists():
            return {"results": []}
        try:
            return json.loads(self._task_results_index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"results": []}

    def _save_task_results_index(self, index: dict[str, Any]) -> None:
        self._task_results_index_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # TaskSpec
    # ------------------------------------------------------------------

    def save_task_spec(self, task_spec: TaskSpec, allow_overwrite: bool = False) -> Path:
        """Save a TaskSpec to ``tasks/<task-id>.json`` and update the index."""
        self._validate_task_id(task_spec.id)
        self._ensure_dirs()
        path = self._tasks_dir / f"{task_spec.id}.json"
        if path.exists() and not allow_overwrite:
            raise FileExistsError(f"TaskSpec already exists: {path}")
        path.write_text(task_spec.to_json(), encoding="utf-8")

        index = self._load_task_index()
        entry = {
            "task_id": task_spec.id,
            "path": str(Path("tasks") / f"{task_spec.id}.json"),
            "executable": task_spec.executable,
            "planning_required": task_spec.planning_required,
            "depends_on": list(task_spec.depends_on),
            "updated_at": _now_iso(),
        }
        index["tasks"] = [e for e in index["tasks"] if e["task_id"] != task_spec.id]
        index["tasks"].append(entry)
        index["tasks"].sort(key=lambda e: e["task_id"])
        self._save_task_index(index)
        return path

    def load_task_spec(self, task_id: str) -> TaskSpec | None:
        """Load a TaskSpec by *task_id*.  Returns ``None`` if missing."""
        self._validate_task_id(task_id)
        path = self._tasks_dir / f"{task_id}.json"
        if not path.exists():
            return None
        try:
            return TaskSpec.from_json(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, KeyError):
            return None

    def list_task_specs(self) -> list[TaskSpec]:
        """Return all stored TaskSpecs, sorted by *task_id*."""
        self._ensure_dirs()
        specs: list[TaskSpec] = []
        for path in sorted(self._tasks_dir.glob("*.json")):
            try:
                specs.append(TaskSpec.from_json(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError, KeyError):
                continue
        return specs

    # ------------------------------------------------------------------
    # TaskResult
    # ------------------------------------------------------------------

    def save_task_result(self, task_result: TaskResult) -> Path:
        """Save a TaskResult to ``results/<task-id>/task-result.json``."""
        self._validate_task_id(task_result.task_id)
        self._ensure_dirs()
        result_dir = self._results_dir / task_result.task_id
        result_dir.mkdir(parents=True, exist_ok=True)
        path = result_dir / "task-result.json"
        path.write_text(task_result.to_json(), encoding="utf-8")

        index = self._load_task_results_index()
        entry = {
            "task_id": task_result.task_id,
            "status": task_result.status,
            "path": str(Path("results") / task_result.task_id / "task-result.json"),
            "updated_at": _now_iso(),
        }
        index["results"] = [e for e in index["results"] if e["task_id"] != task_result.task_id]
        index["results"].append(entry)
        index["results"].sort(key=lambda e: e["task_id"])
        self._save_task_results_index(index)
        return path

    def load_task_result(self, task_id: str) -> TaskResult | None:
        """Load a TaskResult by *task_id*."""
        self._validate_task_id(task_id)
        path = self._results_dir / task_id / "task-result.json"
        if not path.exists():
            return None
        try:
            return TaskResult.from_json(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, KeyError):
            return None

    def list_task_results(self) -> list[TaskResult]:
        """Return all stored TaskResults."""
        self._ensure_dirs()
        results: list[TaskResult] = []
        for result_dir in sorted(self._results_dir.iterdir()):
            if not result_dir.is_dir():
                continue
            path = result_dir / "task-result.json"
            if path.exists():
                try:
                    results.append(TaskResult.from_json(path.read_text(encoding="utf-8")))
                except (json.JSONDecodeError, OSError, KeyError):
                    continue
        return results

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_task_status(self, task_id: str) -> str:
        """Return TaskResult status, or ``"pending"`` if no result exists."""
        result = self.load_task_result(task_id)
        if result is not None and result.status:
            return result.status
        return "pending"

    def list_ready_tasks(self) -> list[TaskSpec]:
        """Return executable tasks whose dependencies are all *passed*."""
        all_specs = self.list_task_specs()
        ready: list[TaskSpec] = []
        for spec in all_specs:
            if not spec.executable or spec.planning_required:
                continue
            if self.has_terminal_result(spec.id):
                continue
            deps_ok = True
            for dep in spec.depends_on:
                dep_result = self.load_task_result(dep)
                if dep_result is None or dep_result.status != "passed":
                    deps_ok = False
                    break
            if deps_ok:
                ready.append(spec)
        return ready

    def list_blocked_tasks(self) -> list[TaskSpec]:
        """Return tasks that are not *ready* and have no terminal result."""
        all_specs = self.list_task_specs()
        ready_ids = {s.id for s in self.list_ready_tasks()}
        blocked: list[TaskSpec] = []
        for spec in all_specs:
            if spec.id in ready_ids:
                continue
            if self.has_terminal_result(spec.id):
                continue
            blocked.append(spec)
        return blocked

    def has_terminal_result(self, task_id: str) -> bool:
        """Return ``True`` if the task has a terminal status result."""
        result = self.load_task_result(task_id)
        if result is None:
            return False
        return result.status in {"passed", "failed", "blocked", "split", "needs_planning"}
