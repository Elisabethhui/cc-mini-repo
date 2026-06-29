from __future__ import annotations

import json
import subprocess
import time
import typing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from .context_budget import BudgetState, ContextBudgetCalculator
from .dev_contract import TaskResult, TaskSpec
from .plan_graph import PlanGraph
from .plan_task_bridge import PlanToTaskBridge
from .runtime_state import RuntimeStateStore
from .verification_runner import VerificationRunner, VerificationRunResult, _is_safe_path, _resolve_within_workspace

if typing.TYPE_CHECKING:
    from .step_artifact_store import StepArtifactStore
    from .task_spec_store import TaskSpecStore


# ---------------------------------------------------------------------------
# StepResult
# ---------------------------------------------------------------------------

@dataclass
class StepResult:
    """Detailed outcome of a single step execution."""

    step_id: str
    task_id: str
    status: str = ""
    prompt_path: str = ""
    engine_called: bool = False
    engine_event_count: int = 0
    assistant_text_summary: str = ""
    tool_calls_summary: list[dict] = field(default_factory=list)
    verification_result: dict = field(default_factory=dict)
    task_result: dict = field(default_factory=dict)
    budget_report: dict | None = None
    artifact_paths: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "task_id": self.task_id,
            "status": self.status,
            "prompt_path": self.prompt_path,
            "engine_called": self.engine_called,
            "engine_event_count": self.engine_event_count,
            "assistant_text_summary": self.assistant_text_summary,
            "tool_calls_summary": list(self.tool_calls_summary),
            "verification_result": dict(self.verification_result),
            "task_result": dict(self.task_result),
            "budget_report": dict(self.budget_report) if self.budget_report else None,
            "artifact_paths": list(self.artifact_paths),
            "risks": list(self.risks),
            "next_action": self.next_action,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StepResult:
        return cls(
            step_id=str(data.get("step_id", "")),
            task_id=str(data.get("task_id", "")),
            status=str(data.get("status", "")),
            prompt_path=str(data.get("prompt_path", "")),
            engine_called=bool(data.get("engine_called", False)),
            engine_event_count=int(data.get("engine_event_count", 0)),
            assistant_text_summary=str(data.get("assistant_text_summary", "")),
            tool_calls_summary=list(data.get("tool_calls_summary", [])),
            verification_result=dict(data.get("verification_result", {})),
            task_result=dict(data.get("task_result", {})),
            budget_report=dict(data.get("budget_report")) if data.get("budget_report") else None,
            artifact_paths=list(data.get("artifact_paths", [])),
            risks=list(data.get("risks", [])),
            next_action=str(data.get("next_action", "")),
        )


# ---------------------------------------------------------------------------
# StepExecutor
# ---------------------------------------------------------------------------

class StepExecutor:
    """Execute a single executable TaskSpec end-to-end.

    Guarantees:
    - At most one engine call per task.
    - changed_files are detected from git or filesystem, never from assistant text.
    - Forbidden file modifications block the task.
    - Budget hard-stop / split prevents the engine call.
    """

    def __init__(
        self,
        workspace: Path,
        runtime_store: RuntimeStateStore,
        context_window: int,
        reserved_output_tokens: int = 2048,
        safety_margin_tokens: int = 1024,
        verification_runner: VerificationRunner | None = None,
        task_store: TaskSpecStore | None = None,
        step_artifact_store: StepArtifactStore | None = None,
        max_retries: int = 1,
        retry_on_verification_failure: bool = True,
    ):
        self.workspace = workspace.resolve()
        self.runtime_store = runtime_store
        self.context_window = context_window
        self.reserved_output_tokens = reserved_output_tokens
        self.safety_margin_tokens = safety_margin_tokens
        self.verification_runner = verification_runner or VerificationRunner()
        self.task_store = task_store
        self.step_artifact_store = step_artifact_store
        # Task 078: bounded retry. Clamp to [0, 1] so the runner can never loop.
        self.max_retries = max(0, min(int(max_retries), 1))
        self.retry_on_verification_failure = bool(retry_on_verification_failure)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_task(
        self,
        task_spec: TaskSpec,
        engine: Any,
        plan_graph: PlanGraph | None = None,
    ) -> TaskResult:
        """Execute a TaskSpec with bounded retry and return a TaskResult."""
        if self.task_store is not None:
            self.task_store.save_task_spec(task_spec, allow_overwrite=True)

        # Initial validation / budget check on the original prompt.
        validation_errors = self._validate_task_spec(task_spec)
        if validation_errors:
            return self._blocked_result(
                step_id=f"step-{task_spec.id}-0-{int(time.time())}",
                task_spec=task_spec,
                risks=validation_errors,
                next_action="Fix TaskSpec validation errors",
                plan_graph=plan_graph,
            )

        prompt = self._build_prompt(task_spec)
        budget_report = self._check_budget(prompt)
        if budget_report.state == BudgetState.HARD_STOP:
            return self._blocked_result(
                step_id=f"step-{task_spec.id}-0-{int(time.time())}",
                task_spec=task_spec,
                risks=[f"Budget hard-stop: {budget_report.state.value}"],
                next_action="Reduce prompt size or increase context_window",
                budget_report=budget_report,
                plan_graph=plan_graph,
            )
        if budget_report.state == BudgetState.SPLIT:
            return self._blocked_result(
                step_id=f"step-{task_spec.id}-0-{int(time.time())}",
                task_spec=task_spec,
                risks=[f"Budget split: {budget_report.state.value}"],
                next_action="Split task into smaller steps",
                budget_report=budget_report,
                plan_graph=plan_graph,
            )

        attempts = 0
        retry_count = 0
        final_task_result: TaskResult | None = None
        final_verif_result: VerificationRunResult | None = None
        final_changed_files: tuple[str, ...] = ()

        while attempts <= self.max_retries:
            attempts += 1
            task_result, verif_result, changed_files = self._execute_single_attempt(
                task_spec=task_spec,
                engine=engine,
                prompt=prompt,
                attempt=attempts,
                plan_graph=plan_graph,
            )
            final_task_result = task_result
            final_verif_result = verif_result
            final_changed_files = changed_files

            # Only retry on genuine verification failures.
            if task_result.status != "failed" or not self.retry_on_verification_failure:
                break
            if attempts > self.max_retries:
                break
            prompt = self._build_retry_prompt(
                task_spec=task_spec,
                failed_result=task_result,
                failed_verif=verif_result,
                changed_files=changed_files,
            )
            retry_count += 1

        assert final_task_result is not None
        assert final_verif_result is not None
        final_task_result.attempts = attempts
        final_task_result.retry_count = retry_count
        final_task_result.final_test_passed = bool(final_verif_result.passed)
        final_task_result.changed_files = list(final_changed_files)
        return final_task_result

    def _execute_single_attempt(
        self,
        task_spec: TaskSpec,
        engine: Any,
        prompt: str,
        attempt: int,
        plan_graph: PlanGraph | None = None,
    ) -> tuple[TaskResult, VerificationRunResult, tuple[str, ...]]:
        """Run one execution attempt and return its result plus verification details."""
        step_id = f"step-{task_spec.id}-{attempt}-{int(time.time())}"

        # Budget check on the prompt (important for retry prompts).
        budget_report = self._check_budget(prompt)
        if budget_report.state == BudgetState.HARD_STOP:
            task_result = self._blocked_result(
                step_id=step_id,
                task_spec=task_spec,
                risks=[f"Budget hard-stop: {budget_report.state.value}"],
                next_action="Reduce prompt size or increase context_window",
                budget_report=budget_report,
                plan_graph=plan_graph,
            )
            return (
                task_result,
                VerificationRunResult(passed=False, skipped=True, risks=budget_report.warnings),
                (),
            )
        if budget_report.state == BudgetState.SPLIT:
            task_result = self._blocked_result(
                step_id=step_id,
                task_spec=task_spec,
                risks=[f"Budget split: {budget_report.state.value}"],
                next_action="Split task into smaller steps",
                budget_report=budget_report,
                plan_graph=plan_graph,
            )
            return (
                task_result,
                VerificationRunResult(passed=False, skipped=True, risks=budget_report.warnings),
                (),
            )

        # Engine call
        events: list[tuple] = []
        assistant_text = ""
        tool_calls: list[dict] = []
        try:
            for event in engine.submit(prompt):
                events.append(event)
                if len(event) >= 2 and event[0] == "text":
                    assistant_text += str(event[1])
                elif len(event) >= 2 and event[0] == "tool_call":
                    tool_calls.append({
                        "name": str(event[1]),
                        "input": event[2] if len(event) > 2 else {},
                    })
        except Exception as exc:
            task_result = self._blocked_result(
                step_id=step_id,
                task_spec=task_spec,
                risks=[f"Engine error: {exc}"],
                next_action="Check engine configuration and retry",
                budget_report=budget_report,
                plan_graph=plan_graph,
            )
            return (
                task_result,
                VerificationRunResult(passed=False, skipped=True, risks=[f"Engine error: {exc}"]),
                (),
            )

        # Detect changed files from git or filesystem, NOT assistant text.
        changed_files = self._detect_changed_files(task_spec.allowed_files)

        # Check forbidden / out-of-bounds modifications.
        scope_risks: list[str] = []
        forbidden_modified = [f for f in changed_files if f in task_spec.forbidden_files]
        if forbidden_modified:
            scope_risks.append(f"Forbidden files modified: {forbidden_modified}")

        out_of_bounds = [
            f for f in changed_files
            if f not in task_spec.allowed_files and f not in task_spec.forbidden_files
        ]
        if out_of_bounds:
            scope_risks.append(f"Out-of-bounds files modified: {out_of_bounds}")

        # Run verification
        verif_result = self.verification_runner.run(
            task_spec.verification,
            self.workspace,
        )

        # Determine status
        if forbidden_modified or out_of_bounds:
            status = "blocked"
        elif verif_result.passed:
            status = "passed"
        elif verif_result.skipped:
            status = "blocked"
        else:
            status = "failed"

        risks = list(scope_risks)
        if budget_report.warnings:
            risks.extend(budget_report.warnings)
        if verif_result.risks:
            risks.extend(verif_result.risks)

        next_action = ""
        if status == "passed":
            next_action = f"Task {task_spec.id} complete"
        elif status == "blocked":
            next_action = "Resolve scope or verification issues before continuing"
        elif status == "failed":
            next_action = f"Fix verification failures for {task_spec.id}"

        task_result = TaskResult(
            task_id=task_spec.id,
            status=status,
            changed_files=list(changed_files),
            verification_command=list(task_spec.verification.command),
            verification_passed=verif_result.passed,
            artifact_paths=list(verif_result.artifact_paths),
            next_action=next_action,
            risks=risks,
            notes=verif_result.summary,
        )

        step_result = StepResult(
            step_id=step_id,
            task_id=task_spec.id,
            status=status,
            engine_called=True,
            engine_event_count=len(events),
            assistant_text_summary=assistant_text[:500],
            tool_calls_summary=tool_calls,
            verification_result=verif_result.to_dict(),
            task_result=task_result.to_dict(),
            budget_report=budget_report.to_dict() if budget_report else None,
            risks=risks,
            next_action=next_action,
        )

        # Persist artifacts
        artifact_paths = self._persist_artifacts(
            step_id=step_id,
            prompt=prompt,
            events=events,
            verif_result=verif_result,
            step_result=step_result,
            task_result=task_result,
        )
        step_result.prompt_path = str(artifact_paths.get("prompt", ""))
        step_result.artifact_paths = [str(p) for p in artifact_paths.values()]
        task_result.artifact_paths = step_result.artifact_paths

        # Update runtime state
        self._update_runtime_state(
            step_id=step_id,
            artifact_paths=list(artifact_paths.values()),
            budget_report=budget_report,
            next_action=next_action,
        )

        # PlanGraph feedback
        if plan_graph is not None:
            PlanToTaskBridge.update_plan_with_task_results(plan_graph, [task_result])

        self._record_to_stores(
            task_id=task_spec.id,
            step_id=step_id,
            task_result=task_result,
            artifact_paths=list(artifact_paths.values()),
        )

        return task_result, verif_result, changed_files

    def _build_retry_prompt(
        self,
        task_spec: TaskSpec,
        failed_result: TaskResult,
        failed_verif: VerificationRunResult,
        changed_files: tuple[str, ...],
    ) -> str:
        """Build a bounded retry prompt from the previous failed attempt."""
        stdout_summary = failed_verif.stdout[:2000] if failed_verif.stdout else "(none)"
        stderr_summary = failed_verif.stderr[:2000] if failed_verif.stderr else "(none)"
        risks_text = "\n".join(f"- {r}" for r in failed_result.risks) or "- (none)"
        changed_text = "\n".join(f"- {f}" for f in changed_files) or "- (none)"
        allowed_text = "\n".join(f"- {f}" for f in task_spec.allowed_files) or "- (none)"
        forbidden_text = "\n".join(f"- {f}" for f in task_spec.forbidden_files) or "- (none)"

        verif_lines = [
            f"- kind: {task_spec.verification.kind}",
            f"- expected_exit_code: {task_spec.verification.expected_exit_code}",
        ]
        if task_spec.verification.command:
            verif_lines.append(f"- command: {' '.join(task_spec.verification.command)}")
        if task_spec.verification.expected_artifacts:
            verif_lines.append(
                f"- expected_artifacts: {', '.join(task_spec.verification.expected_artifacts)}"
            )

        lines = [
            "# Retry Task Execution",
            "",
            f"**Task ID:** {task_spec.id}",
            f"**Goal:** {task_spec.goal}",
            "",
            "## Allowed Files",
            allowed_text,
            "",
            "## Forbidden Files",
            forbidden_text,
            "",
            "## Verification Spec",
            *verif_lines,
            "",
            "## Previous Attempt Failure",
            f"- status: {failed_result.status}",
            f"- exit_code: {failed_verif.exit_code}",
            f"- verification_passed: {failed_verif.passed}",
            "",
            "### stdout summary",
            stdout_summary,
            "",
            "### stderr summary",
            stderr_summary,
            "",
            "### changed_files",
            changed_text,
            "",
            "### risks",
            risks_text,
            "",
            "## Instructions",
            "- Fix ONLY the failure reason shown above.",
            "- Do NOT perform unrelated refactoring.",
            "- Do NOT modify any file outside Allowed Files.",
            "- Do NOT modify any Forbidden Files.",
            "- After fixing, output a brief JSON summary with keys: status, changed_files, note.",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_task_spec(self, task_spec: TaskSpec) -> list[str]:
        errors: list[str] = []

        if not task_spec.executable:
            errors.append("TaskSpec is not executable")
        if task_spec.planning_required:
            errors.append("TaskSpec requires planning")

        verif_errors = task_spec.verification.validate()
        if verif_errors:
            errors.extend(verif_errors)

        if task_spec.context_budget <= 0:
            errors.append(f"context_budget must be > 0, got {task_spec.context_budget}")

        if not (0.0 <= task_spec.confidence <= 1.0):
            errors.append(f"confidence must be in [0, 1], got {task_spec.confidence}")

        if task_spec.confidence < 0.6:
            errors.append(f"confidence {task_spec.confidence} < 0.6; needs human confirmation")

        if task_spec.task_kind == "coding" and not task_spec.allowed_files:
            has_boundary_risk = any(
                "boundary" in r.lower() or "boundaries" in r.lower()
                for r in task_spec.risks
            )
            if not has_boundary_risk:
                errors.append("coding task missing allowed_files and no boundary risk")

        for f in task_spec.allowed_files + task_spec.forbidden_files:
            if not _is_safe_path(self.workspace, f):
                errors.append(f"Unsafe path: {f}")

        return errors

    def _build_prompt(self, task_spec: TaskSpec) -> str:
        lines = [
            "# Task Execution",
            "",
            f"**Task ID:** {task_spec.id}",
            f"**Goal:** {task_spec.goal}",
            f"**Kind:** {task_spec.task_kind} / {task_spec.task_type}",
            "",
            "## Allowed Files",
        ]
        for f in task_spec.allowed_files:
            lines.append(f"- {f}")
        if not task_spec.allowed_files:
            lines.append("- (none specified)")
        lines.append("")
        lines.append("## Forbidden Files")
        for f in task_spec.forbidden_files:
            lines.append(f"- {f}")
        if not task_spec.forbidden_files:
            lines.append("- (none specified)")
        lines.append("")
        lines.append("## Limits")
        lines.append(f"- Max files to read: {task_spec.max_files_to_read}")
        lines.append(f"- Max files to edit: {task_spec.max_files_to_edit}")
        lines.append(f"- Context budget: {task_spec.context_budget} tokens")
        lines.append("")
        lines.append("## Verification")
        lines.append(f"- kind: {task_spec.verification.kind}")
        if task_spec.verification.command:
            lines.append(f"- command: {' '.join(task_spec.verification.command)}")
        if task_spec.verification.expected_artifacts:
            lines.append(f"- expected artifacts: {', '.join(task_spec.verification.expected_artifacts)}")
        lines.append("")
        lines.append("## Done Definition")
        for d in task_spec.done_definition:
            lines.append(f"- {d}")
        if not task_spec.done_definition:
            lines.append("- (none specified)")
        lines.append("")
        lines.append("## Constraints")
        lines.append("- Do NOT modify any file outside Allowed Files.")
        lines.append("- Do NOT modify any Forbidden Files.")
        lines.append("- Do NOT perform unrelated refactoring.")
        lines.append("- Complete ONLY this task; do not start additional work.")
        lines.append("- Output a brief JSON summary of changed files and status.")
        return "\n".join(lines)

    def _check_budget(self, prompt: str) -> Any:
        calculator = ContextBudgetCalculator(
            context_window=self.context_window,
            reserved_output_tokens=self.reserved_output_tokens,
            safety_margin_tokens=self.safety_margin_tokens,
        )
        prompt_tokens = max(1, int(len(prompt) / 1.8))
        return calculator.calculate(
            system_prompt_tokens=0,
            tool_schema_tokens=0,
            message_tokens=prompt_tokens,
            packed_context_tokens=0,
        )

    def _detect_changed_files(self, allowed_files: list[str]) -> tuple[str, ...]:
        """Detect changed files from git status, or fallback to existing allowed files."""
        try:
            proc = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                check=False,
                timeout=5.0,
            )
            if proc.returncode == 0:
                files: list[str] = []
                for line in proc.stdout.splitlines():
                    if not line.strip():
                        continue
                    payload = line[3:] if len(line) > 3 else line
                    if " -> " in payload:
                        payload = payload.split(" -> ", 1)[1]
                    files.append(payload.strip())
                return tuple(files)
        except (OSError, subprocess.TimeoutExpired):
            pass

        # Fallback: check which allowed_files exist on disk
        existing: list[str] = []
        for f in allowed_files:
            target = _resolve_within_workspace(self.workspace, f)
            if target is not None and target.exists():
                existing.append(f)
        return tuple(existing)

    def _blocked_result(
        self,
        step_id: str,
        task_spec: TaskSpec,
        risks: list[str],
        next_action: str,
        budget_report: Any | None = None,
        plan_graph: PlanGraph | None = None,
    ) -> TaskResult:
        task_result = TaskResult(
            task_id=task_spec.id,
            status="blocked",
            risks=risks,
            next_action=next_action,
            notes="Task blocked before engine call",
        )
        step_result = StepResult(
            step_id=step_id,
            task_id=task_spec.id,
            status="blocked",
            engine_called=False,
            task_result=task_result.to_dict(),
            budget_report=budget_report.to_dict() if budget_report else None,
            risks=risks,
            next_action=next_action,
        )
        artifact_paths = self._persist_artifacts(
            step_id=step_id,
            prompt="",
            events=[],
            verif_result=None,
            step_result=step_result,
            task_result=task_result,
        )
        self._update_runtime_state(
            step_id=step_id,
            artifact_paths=[],
            budget_report=budget_report,
            next_action=next_action,
        )
        if plan_graph is not None:
            PlanToTaskBridge.update_plan_with_task_results(plan_graph, [task_result])
        self._record_to_stores(
            task_id=task_spec.id,
            step_id=step_id,
            task_result=task_result,
            artifact_paths=list(artifact_paths.values()),
        )
        return task_result

    def _persist_artifacts(
        self,
        step_id: str,
        prompt: str,
        events: list[tuple],
        verif_result: Any | None,
        step_result: StepResult,
        task_result: TaskResult,
    ) -> dict[str, Path]:
        paths: dict[str, Path] = {}
        if prompt:
            paths["prompt"] = self.runtime_store.write_artifact(
                f"{step_id}-prompt.md", prompt
            )
        events_data = [{"event": list(e)} for e in events]
        paths["engine-events"] = self.runtime_store.write_artifact(
            f"{step_id}-engine-events.json",
            json.dumps(events_data, ensure_ascii=False, indent=2),
        )
        if verif_result is not None:
            paths["verification-result"] = self.runtime_store.write_artifact(
                f"{step_id}-verification-result.json",
                json.dumps(verif_result.to_dict(), ensure_ascii=False, indent=2),
            )
        paths["step-result"] = self.runtime_store.write_artifact(
            f"{step_id}-step-result.json",
            json.dumps(step_result.to_dict(), ensure_ascii=False, indent=2),
        )
        paths["task-result"] = self.runtime_store.write_artifact(
            f"{step_id}-task-result.json",
            json.dumps(task_result.to_dict(), ensure_ascii=False, indent=2),
        )
        return paths

    def _update_runtime_state(
        self,
        step_id: str,
        artifact_paths: list[Path],
        budget_report: Any | None,
        next_action: str,
    ) -> None:
        state = self.runtime_store.load_state()
        state["current_step"] = step_id
        existing_artifacts = list(state.get("artifacts", []))
        existing_artifacts.extend(str(p) for p in artifact_paths)
        state["artifacts"] = existing_artifacts
        if budget_report is not None:
            reports = list(state.get("budget_reports", []))
            reports.append(budget_report.to_dict())
            state["budget_reports"] = reports
        state["next_action"] = next_action
        self.runtime_store.save_state(state)

    def _record_to_stores(
        self,
        task_id: str,
        step_id: str,
        task_result: TaskResult,
        artifact_paths: list[Path],
    ) -> None:
        """Save task result and record step artifacts when stores are attached."""
        if self.step_artifact_store is not None:
            self.step_artifact_store.record_step(
                task_id=task_id,
                step_id=step_id,
                artifact_paths=artifact_paths,
                task_result=task_result,
            )
        if self.task_store is not None:
            self.task_store.save_task_result(task_result)
