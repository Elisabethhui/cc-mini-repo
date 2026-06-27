from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


class PathTraversalError(ValueError):
    """Raised when a path escapes the runtime directory."""


class RuntimeStateStore:
    """Local filesystem store for N-context runtime state.

    All writes are confined to ``.ai-dev/runtime/<run_id>/`` under the
    workspace root.  Paths containing ``..`` or absolute components are
    rejected.
    """

    def __init__(self, workspace_root: str | Path, run_id: str | None = None):
        self.workspace = Path(workspace_root).expanduser().resolve()
        self.run_id = run_id or _generate_run_id()
        self.base_dir = self.workspace / ".ai-dev" / "runtime" / self.run_id
        self._state_path = self.base_dir / "state.json"
        self._budget_reports_path = self.base_dir / "budget-reports.jsonl"
        self._steps_dir = self.base_dir / "steps"
        self._artifacts_dir = self.base_dir / "artifacts"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_dirs(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._steps_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _validate_within_base(self, relative_path: str) -> Path:
        """Return an absolute Path that is guaranteed to be inside *base_dir*.

        Raises PathTraversalError on escape attempts.
        """
        if ".." in relative_path.split("/") or ".." in relative_path.split("\\"):
            raise PathTraversalError(f"Path contains '..' : {relative_path!r}")
        if relative_path.startswith("/"):
            raise PathTraversalError(f"Absolute path not allowed: {relative_path!r}")

        target = (self.base_dir / relative_path).resolve()
        # Ensure resolved path is still under base_dir
        try:
            target.relative_to(self.base_dir)
        except ValueError as exc:
            raise PathTraversalError(
                f"Path escapes runtime directory: {relative_path!r}"
            ) from exc
        return target

    # ------------------------------------------------------------------
    # State JSON
    # ------------------------------------------------------------------

    def default_state(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "phase": "intake",
            "current_step": "",
            "goal": "",
            "decisions": [],
            "open_questions": [],
            "artifacts": [],
            "budget_reports": [],
            "next_action": "",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }

    def load_state(self) -> dict[str, Any]:
        """Load *state.json*.  Returns a default dict if the file does not exist."""
        if not self._state_path.exists():
            return self.default_state()
        try:
            with self._state_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            return self.default_state()
        # Ensure required keys are present
        for key, value in self.default_state().items():
            data.setdefault(key, value)
        return data

    def save_state(self, data: dict[str, Any]) -> None:
        """Atomically write *state.json* after adding ``updated_at``."""
        self._ensure_dirs()
        data["updated_at"] = _now_iso()
        tmp_path = self._state_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        tmp_path.replace(self._state_path)

    def patch_state(self, **kwargs: Any) -> dict[str, Any]:
        """Load current state, update with *kwargs*, and save back."""
        state = self.load_state()
        for key, value in kwargs.items():
            state[key] = value
        self.save_state(state)
        return state

    # ------------------------------------------------------------------
    # Budget reports (JSONL)
    # ------------------------------------------------------------------

    def append_budget_report(self, report: dict[str, Any]) -> None:
        """Append a single budget report line to *budget-reports.jsonl*."""
        self._ensure_dirs()
        line = json.dumps(report, ensure_ascii=False)
        with self._budget_reports_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def list_budget_reports(self) -> list[dict[str, Any]]:
        """Read all budget reports from the JSONL file."""
        if not self._budget_reports_path.exists():
            return []
        reports: list[dict[str, Any]] = []
        with self._budget_reports_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    reports.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return reports

    # ------------------------------------------------------------------
    # Step logs (Markdown)
    # ------------------------------------------------------------------

    def write_step_log(self, step_name: str, content: str) -> Path:
        """Write a markdown step log.

        *step_name* may contain alphanumeric characters, hyphens, and underscores.
        It is sanitised to prevent directory traversal.
        """
        safe_name = re.sub(r"[^\w\-]+", "_", step_name).strip("_")
        if not safe_name:
            safe_name = "untitled"
        target = self._validate_within_base(f"steps/{safe_name}.md")
        self._ensure_dirs()
        target.write_text(content, encoding="utf-8")
        return target

    def read_step_log(self, step_name: str) -> str:
        """Read a previously written step log."""
        safe_name = re.sub(r"[^\w\-]+", "_", step_name).strip("_")
        target = self._validate_within_base(f"steps/{safe_name}.md")
        if not target.exists():
            return ""
        return target.read_text(encoding="utf-8")

    def list_steps(self) -> list[str]:
        """Return a sorted list of step file names (without directory)."""
        if not self._steps_dir.exists():
            return []
        return sorted(p.name for p in self._steps_dir.iterdir() if p.is_file())

    # ------------------------------------------------------------------
    # Artifacts
    # ------------------------------------------------------------------

    def write_artifact(self, name: str, content: str) -> Path:
        """Write an arbitrary artifact file under *artifacts/*."""
        safe_name = re.sub(r"[^\w.\-]+", "_", name).strip("_")
        if not safe_name or safe_name.startswith("."):
            safe_name = "artifact"
        target = self._validate_within_base(f"artifacts/{safe_name}")
        self._ensure_dirs()
        target.write_text(content, encoding="utf-8")
        return target

    def read_artifact(self, name: str) -> str:
        """Read an artifact by name."""
        safe_name = re.sub(r"[^\w.\-]+", "_", name).strip("_")
        target = self._validate_within_base(f"artifacts/{safe_name}")
        if not target.exists():
            return ""
        return target.read_text(encoding="utf-8")

    def list_artifacts(self) -> list[str]:
        """Return a sorted list of artifact file names."""
        if not self._artifacts_dir.exists():
            return []
        return sorted(p.name for p in self._artifacts_dir.iterdir() if p.is_file())
