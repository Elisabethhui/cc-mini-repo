from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dev_contract import TaskResult
from .runtime_state import RuntimeStateStore
from .step_executor import StepResult
from .verification_runner import VerificationRunResult


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StepArtifactStore:
    """Index and read step artifacts produced by StepExecutor.

    Does **not** re-run StepExecutor or VerificationRunner.
    Only records, indexes, and retrieves artifacts that already exist.

    Directory layout (under ``.ai-dev/runtime/<run-id>/``):

    .. code-block:: text

        artifacts/
            step-<id>-prompt.md
            step-<id>-engine-events.json
            step-<id>-verification-result.json
            step-<id>-step-result.json
            step-<id>-task-result.json
        step-index.json
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
        self._artifacts_dir = self.base_dir / "artifacts"
        self._step_index_path = self.base_dir / "step-index.json"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_dirs(self) -> None:
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)

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

    def _to_runtime_relative(self, path: Path) -> str:
        resolved = path.resolve()
        base = self.base_dir.resolve()
        try:
            return str(resolved.relative_to(base))
        except ValueError as exc:
            raise ValueError(f"Path not within runtime base: {path}") from exc

    def _load_step_index(self) -> dict[str, Any]:
        if not self._step_index_path.exists():
            return {"steps": []}
        try:
            return json.loads(self._step_index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"steps": []}

    def _save_step_index(self, index: dict[str, Any]) -> None:
        self._step_index_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_step(
        self,
        task_id: str,
        step_id: str,
        artifact_paths: list[Path],
        task_result: TaskResult | None = None,
    ) -> Path:
        """Record a step entry in ``step-index.json``.

        *artifact_paths* are converted to runtime-relative paths.
        Raises ``ValueError`` if any path escapes the runtime base.
        """
        self._validate_task_id(task_id)
        self._ensure_dirs()

        rel_paths: list[str] = []
        for p in artifact_paths:
            rel_paths.append(self._to_runtime_relative(p))

        index = self._load_step_index()
        entry = {
            "task_id": task_id,
            "step_id": step_id,
            "status": task_result.status if task_result else "",
            "artifact_paths": rel_paths,
            "created_at": _now_iso(),
        }
        # Remove any existing entry with the same task_id + step_id
        index["steps"] = [
            s for s in index["steps"]
            if not (s["task_id"] == task_id and s["step_id"] == step_id)
        ]
        index["steps"].append(entry)
        self._save_step_index(index)
        return self._step_index_path

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list_steps(self, task_id: str | None = None) -> list[dict[str, Any]]:
        """Return step entries, optionally filtered by *task_id*."""
        index = self._load_step_index()
        steps = list(index.get("steps", []))
        if task_id is not None:
            self._validate_task_id(task_id)
            steps = [s for s in steps if s["task_id"] == task_id]
        return sorted(steps, key=lambda s: s.get("created_at", ""))

    def latest_step(self, task_id: str) -> dict[str, Any] | None:
        """Return the most recent step for *task_id*, or ``None``."""
        steps = self.list_steps(task_id)
        if not steps:
            return None
        return steps[-1]

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_step_result(self, step_id: str) -> StepResult | None:
        """Read ``step-<id>-step-result.json``."""
        path = self._artifacts_dir / f"{step_id}-step-result.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return StepResult.from_dict(data)
        except (json.JSONDecodeError, OSError, KeyError):
            return None

    def load_verification_result(self, step_id: str) -> VerificationRunResult | dict | None:
        """Read ``step-<id>-verification-result.json``.

        Returns a ``VerificationRunResult`` dataclass when possible,
        falling back to a plain ``dict``.
        """
        path = self._artifacts_dir / f"{step_id}-verification-result.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return VerificationRunResult.from_dict(data)
        except (json.JSONDecodeError, OSError, KeyError, TypeError):
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return None

    def load_task_result_from_step(self, step_id: str) -> TaskResult | None:
        """Read ``step-<id>-task-result.json``."""
        path = self._artifacts_dir / f"{step_id}-task-result.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return TaskResult.from_dict(data)
        except (json.JSONDecodeError, OSError, KeyError):
            return None

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_expected_artifacts(self, step_id: str) -> tuple[bool, list[str]]:
        """Check whether the five standard artifacts exist for *step_id*.

        Returns ``(ok, missing_names)``.
        """
        expected = [
            f"{step_id}-prompt.md",
            f"{step_id}-engine-events.json",
            f"{step_id}-verification-result.json",
            f"{step_id}-step-result.json",
            f"{step_id}-task-result.json",
        ]
        missing: list[str] = []
        for name in expected:
            if not (self._artifacts_dir / name).exists():
                missing.append(name)
        return (not missing, missing)
