from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any


# ---------------------------------------------------------------------------
# VerificationSpec
# ---------------------------------------------------------------------------

@dataclass
class VerificationSpec:
    """Describes how a TaskSpec is verified."""

    kind: str  # command | artifact | manual | contract
    command: list[str] = field(default_factory=list)
    expected_exit_code: int = 0
    timeout_seconds: int = 30
    expected_artifacts: list[str] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> list[str]:
        """Return a list of validation errors (empty if valid)."""
        errors: list[str] = []
        if self.kind not in {"command", "artifact", "manual", "contract"}:
            errors.append(f"Invalid verification kind: {self.kind}")
        if self.kind == "command" and not self.command:
            errors.append("kind='command' requires non-empty command list")
        if self.kind == "artifact" and not self.expected_artifacts:
            errors.append("kind='artifact' requires non-empty expected_artifacts")
        if self.kind == "manual" and not self.notes:
            errors.append("kind='manual' requires non-empty notes")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "command": list(self.command),
            "expected_exit_code": self.expected_exit_code,
            "timeout_seconds": self.timeout_seconds,
            "expected_artifacts": list(self.expected_artifacts),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationSpec:
        return cls(
            kind=str(data.get("kind", "contract")),
            command=list(data.get("command", [])),
            expected_exit_code=int(data.get("expected_exit_code", 0)),
            timeout_seconds=int(data.get("timeout_seconds", 30)),
            expected_artifacts=list(data.get("expected_artifacts", [])),
            notes=str(data.get("notes", "")),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> VerificationSpec:
        return cls.from_dict(json.loads(text))


# ---------------------------------------------------------------------------
# TaskSpec
# ---------------------------------------------------------------------------

@dataclass
class TaskSpec:
    """An executable or planning task definition."""

    id: str
    goal: str = ""
    task_kind: str = ""  # planning | coding | verification | review
    task_type: str = ""  # intake | plan | scaffold | create | modify | fix | test | review
    executable: bool = False
    planning_required: bool = False
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    context_budget: int = 0
    max_files_to_read: int = 0
    max_files_to_edit: int = 0
    verification: VerificationSpec = field(
        default_factory=lambda: VerificationSpec(kind="contract")
    )
    done_definition: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    source_plan_id: str = ""
    run_id: str = ""
    risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def validate(self) -> list[str]:
        """Return a list of validation errors (empty if valid)."""
        errors: list[str] = []

        if self.context_budget <= 0:
            errors.append(f"context_budget must be > 0, got {self.context_budget}")

        if not (0.0 <= self.confidence <= 1.0):
            errors.append(f"confidence must be in [0, 1], got {self.confidence}")

        if self.planning_required and self.executable:
            errors.append("planning_required=True requires executable=False")

        if self.executable:
            verif_errors = self.verification.validate()
            if verif_errors:
                errors.extend(verif_errors)

            if self.verification.kind == "manual":
                errors.append("executable task cannot use verification kind='manual'")
            if self.task_kind == "coding" and self.verification.kind == "contract":
                errors.append("coding task cannot use verification kind='contract'")

            if self.task_kind == "coding" and not self.allowed_files:
                has_boundary_risk = any(
                    "boundary" in r.lower() or "boundaries" in r.lower()
                    for r in self.risks
                )
                if not has_boundary_risk:
                    errors.append(
                        "executable coding task must have allowed_files or a risk noting unknown file boundaries"
                    )

        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "task_kind": self.task_kind,
            "task_type": self.task_type,
            "executable": self.executable,
            "planning_required": self.planning_required,
            "allowed_files": list(self.allowed_files),
            "forbidden_files": list(self.forbidden_files),
            "context_budget": self.context_budget,
            "max_files_to_read": self.max_files_to_read,
            "max_files_to_edit": self.max_files_to_edit,
            "verification": self.verification.to_dict(),
            "done_definition": list(self.done_definition),
            "depends_on": list(self.depends_on),
            "source_plan_id": self.source_plan_id,
            "run_id": self.run_id,
            "risks": list(self.risks),
            "assumptions": list(self.assumptions),
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskSpec:
        return cls(
            id=str(data["id"]),
            goal=str(data.get("goal", "")),
            task_kind=str(data.get("task_kind", "")),
            task_type=str(data.get("task_type", "")),
            executable=bool(data.get("executable", False)),
            planning_required=bool(data.get("planning_required", False)),
            allowed_files=list(data.get("allowed_files", [])),
            forbidden_files=list(data.get("forbidden_files", [])),
            context_budget=int(data.get("context_budget", 0)),
            max_files_to_read=int(data.get("max_files_to_read", 0)),
            max_files_to_edit=int(data.get("max_files_to_edit", 0)),
            verification=VerificationSpec.from_dict(
                data.get("verification", {"kind": "contract"})
            ),
            done_definition=list(data.get("done_definition", [])),
            depends_on=list(data.get("depends_on", [])),
            source_plan_id=str(data.get("source_plan_id", "")),
            run_id=str(data.get("run_id", "")),
            risks=list(data.get("risks", [])),
            assumptions=list(data.get("assumptions", [])),
            confidence=float(data.get("confidence", 0.0)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> TaskSpec:
        return cls.from_dict(json.loads(text))


# ---------------------------------------------------------------------------
# TaskResult
# ---------------------------------------------------------------------------

@dataclass
class TaskResult:
    """Outcome of executing a TaskSpec."""

    task_id: str
    status: str = ""  # passed | failed | blocked | split | needs_planning
    changed_files: list[str] = field(default_factory=list)
    verification_command: list[str] = field(default_factory=list)
    verification_passed: bool = False
    artifact_paths: list[str] = field(default_factory=list)
    next_action: str = ""
    risks: list[str] = field(default_factory=list)
    notes: str = ""
    # Retry / review / worklog metadata (Task 078)
    attempts: int = 1
    retry_count: int = 0
    final_test_passed: bool = False
    review_decision: str = ""  # pass | revise | blocked
    can_finish: bool = False
    requires_user_commit: bool = False
    worklog_path: str | None = None
    test_result_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "changed_files": list(self.changed_files),
            "verification_command": list(self.verification_command),
            "verification_passed": self.verification_passed,
            "artifact_paths": list(self.artifact_paths),
            "next_action": self.next_action,
            "risks": list(self.risks),
            "notes": self.notes,
            "attempts": self.attempts,
            "retry_count": self.retry_count,
            "final_test_passed": self.final_test_passed,
            "review_decision": self.review_decision,
            "can_finish": self.can_finish,
            "requires_user_commit": self.requires_user_commit,
            "worklog_path": self.worklog_path,
            "test_result_paths": list(self.test_result_paths),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskResult:
        return cls(
            task_id=str(data["task_id"]),
            status=str(data.get("status", "")),
            changed_files=list(data.get("changed_files", [])),
            verification_command=list(data.get("verification_command", [])),
            verification_passed=bool(data.get("verification_passed", False)),
            artifact_paths=list(data.get("artifact_paths", [])),
            next_action=str(data.get("next_action", "")),
            risks=list(data.get("risks", [])),
            notes=str(data.get("notes", "")),
            attempts=int(data.get("attempts", 1)),
            retry_count=int(data.get("retry_count", 0)),
            final_test_passed=bool(data.get("final_test_passed", False)),
            review_decision=str(data.get("review_decision", "")),
            can_finish=bool(data.get("can_finish", False)),
            requires_user_commit=bool(data.get("requires_user_commit", False)),
            worklog_path=data.get("worklog_path"),
            test_result_paths=list(data.get("test_result_paths", [])),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> TaskResult:
        return cls.from_dict(json.loads(text))


# ---------------------------------------------------------------------------
# DevReviewResult
# ---------------------------------------------------------------------------

@dataclass
class DevReviewResult:
    """Safe review decision produced after task execution.

    Does not represent a commit decision; it only tells the caller whether
    the task may finish and whether a human commit is required.
    """

    task_id: str
    review_decision: str = ""  # pass | revise | blocked
    can_finish: bool = False
    requires_user_commit: bool = False
    risks: list[str] = field(default_factory=list)
    next_action: str = ""
    worklog_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "review_decision": self.review_decision,
            "can_finish": self.can_finish,
            "requires_user_commit": self.requires_user_commit,
            "risks": list(self.risks),
            "next_action": self.next_action,
            "worklog_path": self.worklog_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DevReviewResult:
        return cls(
            task_id=str(data.get("task_id", "")),
            review_decision=str(data.get("review_decision", "")),
            can_finish=bool(data.get("can_finish", False)),
            requires_user_commit=bool(data.get("requires_user_commit", False)),
            risks=list(data.get("risks", [])),
            next_action=str(data.get("next_action", "")),
            worklog_path=data.get("worklog_path"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> DevReviewResult:
        return cls.from_dict(json.loads(text))
