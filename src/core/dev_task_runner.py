from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .dev_contract import TaskResult, TaskSpec
from .plan_graph import PlanGraph
from .runtime_state import RuntimeStateStore
from .step_artifact_store import StepArtifactStore
from .step_executor import StepExecutor
from .task_spec_store import TaskSpecStore


# ---------------------------------------------------------------------------
# DevRunResult
# ---------------------------------------------------------------------------

@dataclass
class DevRunResult:
    """Outcome of a DevTaskRunner run.

    This is a runner-level status summary.  It is intentionally richer than
    ``TaskResult.status`` because it must report why the runner stopped
    (``max_steps_reached``, ``no_ready_tasks``, etc.) even when no single
    task failed.
    """

    run_id: str
    status: str = ""
    executed_task_ids: list[str] = field(default_factory=list)
    skipped_task_ids: list[str] = field(default_factory=list)
    ready_task_ids: list[str] = field(default_factory=list)
    terminal_task_id: str | None = None
    terminal_status: str | None = None
    task_results: list[TaskResult] = field(default_factory=list)
    step_artifacts: list[str] = field(default_factory=list)
    run_summary_path: str | None = None
    next_action: str = ""
    risks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    _TERMINAL_TASK_STATUSES = {"passed", "failed", "blocked", "split", "needs_planning"}
    _TERMINAL_RUN_STATUSES = {
        "completed",
        "stopped",
        "blocked",
        "split",
        "needs_planning",
        "failed",
        "no_ready_tasks",
        "max_steps_reached",
    }

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "executed_task_ids": list(self.executed_task_ids),
            "skipped_task_ids": list(self.skipped_task_ids),
            "ready_task_ids": list(self.ready_task_ids),
            "terminal_task_id": self.terminal_task_id,
            "terminal_status": self.terminal_status,
            "task_results": [r.to_dict() for r in self.task_results],
            "step_artifacts": list(self.step_artifacts),
            "run_summary_path": self.run_summary_path,
            "next_action": self.next_action,
            "risks": list(self.risks),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DevRunResult:
        return cls(
            run_id=str(data.get("run_id", "")),
            status=str(data.get("status", "")),
            executed_task_ids=list(data.get("executed_task_ids", [])),
            skipped_task_ids=list(data.get("skipped_task_ids", [])),
            ready_task_ids=list(data.get("ready_task_ids", [])),
            terminal_task_id=data.get("terminal_task_id"),
            terminal_status=data.get("terminal_status"),
            task_results=[
                TaskResult.from_dict(r) for r in data.get("task_results", [])
            ],
            step_artifacts=list(data.get("step_artifacts", [])),
            run_summary_path=data.get("run_summary_path"),
            next_action=str(data.get("next_action", "")),
            risks=list(data.get("risks", [])),
            warnings=list(data.get("warnings", [])),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> DevRunResult:
        return cls.from_dict(json.loads(text))


# ---------------------------------------------------------------------------
# DevTaskRunner
# ---------------------------------------------------------------------------

class DevTaskRunner:
    """Execute ready TaskSpecs one at a time until a terminal condition.

    Guarantees:
    - Uses ``TaskSpecStore.list_ready_tasks()`` to discover work.
    - Calls ``StepExecutor.execute_task()`` for every execution.
    - Does not re-run tasks that already have a terminal result.
    - Stops on failed/blocked/split/needs_planning or when max_steps is hit.
    - Writes a ``run-summary.json`` under ``.ai-dev/runtime/<run-id>/``.
    - Updates runtime state with phase, next_action, and artifact list.
    """

    def __init__(
        self,
        workspace: Path,
        task_store: TaskSpecStore,
        step_executor: StepExecutor,
        step_artifact_store: StepArtifactStore | None = None,
        runtime_store: RuntimeStateStore | None = None,
        plan_graph: PlanGraph | None = None,
        max_steps: int = 10,
    ):
        self.workspace = Path(workspace).expanduser().resolve()
        self.task_store = task_store
        self.step_executor = step_executor
        self.step_artifact_store = step_artifact_store
        self.runtime_store = runtime_store
        self.plan_graph = plan_graph
        self.max_steps = max(1, int(max_steps))
        self.run_id = self._resolve_run_id()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_ready_tasks(self, engine: Any) -> DevRunResult:
        """Run ready tasks one at a time until a terminal condition."""
        result = DevRunResult(run_id=self.run_id)
        started_at = time.monotonic()

        for _ in range(self.max_steps):
            ready = self._list_ready_tasks_sorted()
            result.ready_task_ids = [s.id for s in ready]

            if not ready:
                self._finalize_no_ready_tasks(result)
                break

            task_spec = ready[0]
            task_result = self._execute_one(task_spec, engine)
            result.executed_task_ids.append(task_spec.id)
            result.task_results.append(task_result)

            if task_result.status == "passed":
                continue

            if task_result.status in {"failed", "blocked", "split", "needs_planning"}:
                self._finalize_terminal_task(result, task_spec.id, task_result)
                break

            # Unknown task status — treat as blocked to be safe.
            self._finalize_terminal_task(
                result,
                task_spec.id,
                task_result,
                run_status="blocked",
                next_action=f"Unknown status '{task_result.status}' for {task_spec.id}",
            )
            break
        else:
            # Loop exhausted without breaking -> max_steps reached.
            result.status = "max_steps_reached"
            result.next_action = (
                f"Reached max_steps ({self.max_steps}); review run summary before continuing"
            )
            result.warnings.append(
                f"Runner stopped after {self.max_steps} steps without reaching a task terminal state"
            )

        self._collect_step_artifacts(result)
        self._update_runtime_state(result)
        self._update_plan_graph(result)
        summary_path = self.write_run_summary(result)
        result.run_summary_path = str(summary_path)

        elapsed = time.monotonic() - started_at
        if "run-summary.json" not in result.step_artifacts:
            result.step_artifacts.append("run-summary.json")
        result.risks.append(f"Runner finished in {elapsed:.3f}s with status {result.status}")
        return result

    def run_task(
        self,
        task_id: str,
        engine: Any,
        allow_rerun: bool = False,
    ) -> DevRunResult:
        """Run a single task by id after checking dependencies."""
        result = DevRunResult(run_id=self.run_id)

        task_spec = self.task_store.load_task_spec(task_id)
        if task_spec is None:
            result.status = "no_ready_tasks"
            result.next_action = f"Task {task_id} not found"
            result.risks.append(f"Requested task {task_id} does not exist")
            self._update_runtime_state(result)
            self.write_run_summary(result)
            return result

        existing = self.task_store.load_task_result(task_id)
        if existing is not None and existing.status in DevRunResult._TERMINAL_TASK_STATUSES:
            if not allow_rerun:
                result.skipped_task_ids.append(task_id)
                result.status = existing.status if existing.status != "passed" else "completed"
                result.next_action = f"Task {task_id} already has terminal result: {existing.status}"
                result.warnings.append(
                    f"Skipping {task_id}; pass allow_rerun=True to execute again"
                )
                self._update_runtime_state(result)
                self.write_run_summary(result)
                return result

        missing_deps = self._missing_dependencies(task_spec)
        if missing_deps:
            result.status = "blocked"
            result.terminal_task_id = task_id
            result.terminal_status = "blocked"
            result.next_action = f"Resolve dependencies for {task_id}: {missing_deps}"
            result.risks.append(
                f"Task {task_id} blocked; missing or non-passed dependencies: {missing_deps}"
            )
            self._update_runtime_state(result)
            self.write_run_summary(result)
            return result

        if not task_spec.executable or task_spec.planning_required:
            result.status = "needs_planning"
            result.terminal_task_id = task_id
            result.terminal_status = "needs_planning"
            result.next_action = f"Task {task_id} is not executable; refine or replan"
            result.risks.append(
                f"Task {task_id} executable={task_spec.executable} planning_required={task_spec.planning_required}"
            )
            self._update_runtime_state(result)
            self.write_run_summary(result)
            return result

        task_result = self._execute_one(task_spec, engine)
        result.executed_task_ids.append(task_id)
        result.task_results.append(task_result)

        if task_result.status == "passed":
            result.status = "completed"
            result.next_action = f"Task {task_id} passed"
        else:
            self._finalize_terminal_task(result, task_id, task_result)

        self._collect_step_artifacts(result)
        self._update_runtime_state(result)
        self._update_plan_graph(result)
        summary_path = self.write_run_summary(result)
        result.run_summary_path = str(summary_path)
        return result

    def preview_ready_tasks(self) -> dict[str, Any]:
        """Return a snapshot of task states without calling the engine."""
        all_specs = self.task_store.list_task_specs()
        all_results = {r.task_id: r for r in self.task_store.list_task_results()}
        ready = self._list_ready_tasks_sorted()
        ready_ids = {s.id for s in ready}

        preview: dict[str, Any] = {
            "run_id": self.run_id,
            "ready": [],
            "blocked": [],
            "passed": [],
            "failed": [],
            "pending": [],
            "planning_required": [],
            "not_executable": [],
            "unknown": [],
        }

        for spec in all_specs:
            result = all_results.get(spec.id)
            status = result.status if result else "pending"

            if status == "passed":
                preview["passed"].append(spec.id)
            elif status == "failed":
                preview["failed"].append(spec.id)
            elif status in {"blocked", "split", "needs_planning"}:
                # Terminal but not passed/failed: treat as blocked for preview.
                preview["blocked"].append({"task_id": spec.id, "status": status})
            elif spec.id in ready_ids:
                preview["ready"].append(spec.id)
            elif not spec.executable:
                preview["not_executable"].append(spec.id)
            elif spec.planning_required:
                preview["planning_required"].append(spec.id)
            elif status == "pending":
                blocked_by = self._blocked_by(spec, all_results)
                preview["pending"].append(
                    {"task_id": spec.id, "blocked_by": blocked_by}
                )
            else:
                preview["unknown"].append(spec.id)

        return preview

    def write_run_summary(self, result: DevRunResult) -> Path:
        """Write ``run-summary.json`` under the runtime run directory."""
        base = self._runtime_base_dir()
        base.mkdir(parents=True, exist_ok=True)
        path = base / "run-summary.json"
        summary = {
            "run_id": result.run_id,
            "status": result.status,
            "executed_task_ids": list(result.executed_task_ids),
            "skipped_task_ids": list(result.skipped_task_ids),
            "terminal_task_id": result.terminal_task_id,
            "terminal_status": result.terminal_status,
            "task_results_summary": [
                {"task_id": r.task_id, "status": r.status}
                for r in result.task_results
            ],
            "next_action": result.next_action,
            "risks": list(result.risks),
            "warnings": list(result.warnings),
            "step_artifacts": list(result.step_artifacts),
        }
        path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_run_id(self) -> str:
        if self.runtime_store is not None:
            return self.runtime_store.run_id
        return self.task_store.base_dir.name

    def _runtime_base_dir(self) -> Path:
        if self.runtime_store is not None:
            return self.runtime_store.base_dir
        return self.task_store.base_dir

    def _list_ready_tasks_sorted(self) -> list[TaskSpec]:
        ready = self.task_store.list_ready_tasks()
        return sorted(ready, key=lambda s: s.id)

    def _execute_one(self, task_spec: TaskSpec, engine: Any) -> TaskResult:
        """Execute a single task and ensure its result is persisted."""
        task_result = self.step_executor.execute_task(
            task_spec,
            engine,
            plan_graph=self.plan_graph,
        )
        # Confirm the result is in the store even if the executor was not
        # configured with a task store.
        self.task_store.save_task_result(task_result)
        return task_result

    def _missing_dependencies(self, task_spec: TaskSpec) -> list[str]:
        missing: list[str] = []
        for dep in task_spec.depends_on:
            dep_result = self.task_store.load_task_result(dep)
            if dep_result is None or dep_result.status != "passed":
                missing.append(dep)
        return missing

    def _blocked_by(
        self,
        task_spec: TaskSpec,
        all_results: dict[str, TaskResult],
    ) -> list[dict[str, str]]:
        blocked: list[dict[str, str]] = []
        for dep in task_spec.depends_on:
            dep_result = all_results.get(dep)
            if dep_result is None:
                blocked.append({"task_id": dep, "status": "missing"})
            elif dep_result.status != "passed":
                blocked.append({"task_id": dep, "status": dep_result.status})
        return blocked

    def _finalize_no_ready_tasks(self, result: DevRunResult) -> None:
        all_specs = self.task_store.list_task_specs()
        results = {r.task_id: r for r in self.task_store.list_task_results()}

        executable_specs = [
            s for s in all_specs if s.executable and not s.planning_required
        ]
        if not executable_specs:
            result.status = "needs_planning"
            result.next_action = "No executable tasks; create or refine TaskSpecs"
            result.warnings.append("No executable tasks found in store")
            return

        all_passed = all(
            results.get(s.id) is not None and results[s.id].status == "passed"
            for s in executable_specs
        )
        if all_passed:
            result.status = "completed"
            result.next_action = "All executable tasks passed"
            return

        # There are executable tasks but none are ready -> dependencies blocked.
        result.status = "no_ready_tasks"
        result.next_action = "Dependencies not satisfied; review blocked tasks"
        for spec in executable_specs:
            blocked_by = self._blocked_by(spec, results)
            if blocked_by:
                result.warnings.append(
                    f"Task {spec.id} blocked by: {blocked_by}"
                )

    def _finalize_terminal_task(
        self,
        result: DevRunResult,
        task_id: str,
        task_result: TaskResult,
        run_status: str | None = None,
        next_action: str | None = None,
    ) -> None:
        status = run_status or task_result.status
        result.status = status
        result.terminal_task_id = task_id
        result.terminal_status = task_result.status
        result.next_action = next_action or task_result.next_action
        if task_result.risks:
            for risk in task_result.risks:
                result.risks.append(f"Task {task_id}: {risk}")

    def _collect_step_artifacts(self, result: DevRunResult) -> None:
        if self.step_artifact_store is None:
            return
        for task_id in result.executed_task_ids:
            latest = self.step_artifact_store.latest_step(task_id)
            if latest is not None:
                rel_paths = latest.get("artifact_paths", [])
                for p in rel_paths:
                    if p not in result.step_artifacts:
                        result.step_artifacts.append(p)

    def _update_runtime_state(self, result: DevRunResult) -> None:
        if self.runtime_store is None:
            return
        state = self.runtime_store.load_state()
        state["phase"] = self._phase_from_status(result.status)
        state["next_action"] = result.next_action
        if result.task_results:
            state["current_step"] = f"run-{result.run_id}-{result.status}"
        if self.step_artifact_store is not None:
            existing_artifacts = set(state.get("artifacts", []))
            for p in result.step_artifacts:
                existing_artifacts.add(p)
            state["artifacts"] = sorted(existing_artifacts)
        self.runtime_store.save_state(state)

    def _phase_from_status(self, status: str) -> str:
        mapping = {
            "completed": "done",
            "failed": "blocked",
            "blocked": "blocked",
            "split": "split",
            "needs_planning": "plan",
            "no_ready_tasks": "blocked",
            "max_steps_reached": "preserve",
            "stopped": "blocked",
        }
        return mapping.get(status, "implement")

    def _update_plan_graph(self, result: DevRunResult) -> None:
        if self.plan_graph is None:
            return

        # StepExecutor already calls update_plan_with_task_results for each
        # individual task result.  Here we add runner-level feedback only.
        if result.status == "completed":
            self.plan_graph.add_decision(
                f"Run {result.run_id} completed; executable tasks passed"
            )
            self.plan_graph.set_next_action(result.next_action)
        elif result.status == "max_steps_reached":
            self.plan_graph.add_risk(
                f"Run {result.run_id} stopped after {self.max_steps} steps"
            )
            self.plan_graph.set_next_action(result.next_action)
        elif result.status in {"failed", "blocked", "split", "needs_planning"}:
            # next_action is already set by the terminal task via StepExecutor,
            # but ensure it is captured if run_task set it directly.
            if result.next_action:
                self.plan_graph.set_next_action(result.next_action)

        # Never remove task_dag or pretend the whole graph is done.
