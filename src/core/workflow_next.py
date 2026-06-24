from __future__ import annotations

from dataclasses import dataclass

from .workflow_doctor import WorkflowDoctorReport
from .workflow_status import WorkflowStatus


@dataclass(frozen=True)
class WorkflowTaskArtifacts:
    task_goal: str = ""
    codeintel_used: bool = False
    tests_recorded: bool = False
    fresh_review_done: bool = False
    review_decision: str = ""
    work_log_written: bool = False


@dataclass(frozen=True)
class WorkflowNextRecommendation:
    state: str
    next_action: str
    stop_condition: str
    requires_confirmation: bool
    reasons: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def recommend_workflow_next(
    *,
    status: WorkflowStatus,
    doctor: WorkflowDoctorReport,
    artifacts: WorkflowTaskArtifacts,
) -> WorkflowNextRecommendation:
    reasons: list[str] = []
    warnings: list[str] = list(status.warnings) + list(doctor_warning_text(doctor))

    missing_required = tuple(item.name for item in status.required_files if not item.ok)
    git_summary = status.git_summary
    git_dirty = git_summary is not None and git_summary.available and not git_summary.clean
    git_unavailable = git_summary is None or not git_summary.available
    review_decision = artifacts.review_decision.strip().lower()

    if doctor.decision == "blocked":
        reasons.append("workflow doctor reported blocked findings")
        return WorkflowNextRecommendation(
            state="blocked",
            next_action="Resolve blocked workflow doctor findings before any further workflow action.",
            stop_condition="Stop until blocked workflow doctor findings are cleared.",
            requires_confirmation=False,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    if missing_required:
        reasons.append(f"required workflow files are missing: {', '.join(missing_required)}")
        return WorkflowNextRecommendation(
            state="blocked",
            next_action="Create the missing workflow scaffold before continuing implementation.",
            stop_condition="Stop until required workflow files are present.",
            requires_confirmation=False,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    if not artifacts.task_goal.strip():
        reasons.append("task goal is not recorded")
        return WorkflowNextRecommendation(
            state="needs_task_slice",
            next_action="Record a concrete task goal and narrow the scope before proceeding.",
            stop_condition="Stop if the task goal is still ambiguous.",
            requires_confirmation=False,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    if git_unavailable:
        reasons.append("git state is unavailable")
        warnings.append("confirm git state manually before trusting any commit-oriented next step")
        return WorkflowNextRecommendation(
            state="blocked",
            next_action="Verify git state manually before choosing the next workflow step.",
            stop_condition="Stop until git status can be confirmed.",
            requires_confirmation=False,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    if git_dirty and not artifacts.tests_recorded:
        reasons.append("worktree has changes but no test evidence is recorded")
        return WorkflowNextRecommendation(
            state="needs_test_gate",
            next_action="Run the smallest useful verification and record the result before review.",
            stop_condition="Stop before review or commit until tests or verification are recorded.",
            requires_confirmation=False,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    if artifacts.tests_recorded and not artifacts.fresh_review_done:
        reasons.append("verification exists but fresh review has not been recorded")
        return WorkflowNextRecommendation(
            state="needs_fresh_review",
            next_action="Perform a fresh review using the compact task packet before deciding commit or revise.",
            stop_condition="Stop before commit until a fresh review is complete.",
            requires_confirmation=False,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    if artifacts.fresh_review_done and not review_decision:
        reasons.append("fresh review is complete but no review decision is recorded")
        return WorkflowNextRecommendation(
            state="needs_review_decision",
            next_action="Record a review decision such as commit, revise, rollback, reslice, or hold.",
            stop_condition="Stop until the review decision is explicit.",
            requires_confirmation=False,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    if review_decision in {"revise", "rollback", "reslice", "hold"}:
        reasons.append(f"review decision is {review_decision}")
        return WorkflowNextRecommendation(
            state="blocked",
            next_action=f"Follow the recorded review decision: {review_decision}.",
            stop_condition="Stop before commit; the current review decision does not allow commit.",
            requires_confirmation=review_decision == "rollback",
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    if review_decision == "commit" and not artifacts.work_log_written:
        reasons.append("review decision is commit but no work log is recorded")
        return WorkflowNextRecommendation(
            state="needs_work_log",
            next_action="Write the local work log before final commit handling.",
            stop_condition="Stop before commit until the work log is written.",
            requires_confirmation=False,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    if review_decision == "commit" and git_dirty:
        reasons.append("review decision is commit and the worktree still contains changes")
        return WorkflowNextRecommendation(
            state="ready_to_commit",
            next_action="Prepare the exact commit scope and ask for explicit user confirmation before committing.",
            stop_condition="Stop until the user confirms the commit scope.",
            requires_confirmation=True,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    reasons.append("review decision is commit and no pending worktree changes remain")
    return WorkflowNextRecommendation(
        state="done",
        next_action="No further workflow action is required for this task.",
        stop_condition="Stop unless a new task or follow-up change appears.",
        requires_confirmation=False,
        reasons=tuple(reasons),
        warnings=tuple(warnings),
    )


def format_workflow_next(recommendation: WorkflowNextRecommendation) -> str:
    lines = [
        "Workflow Next",
        f"State: {recommendation.state}",
        f"Next action: {recommendation.next_action}",
        f"Stop condition: {recommendation.stop_condition}",
        f"Requires confirmation: {'yes' if recommendation.requires_confirmation else 'no'}",
        "",
        "Reasons:",
    ]
    lines.extend(f"- {reason}" for reason in recommendation.reasons)
    if recommendation.warnings:
        lines.extend(("", "Warnings:"))
        lines.extend(f"- {warning}" for warning in recommendation.warnings)
    return "\n".join(lines).rstrip()


def doctor_warning_text(doctor: WorkflowDoctorReport) -> tuple[str, ...]:
    warnings: list[str] = []
    for group in (doctor.required_files, doctor.local_artifacts, doctor.markdown, doctor.codegraph):
        for check in group:
            if check.severity == "warn":
                warnings.append(f"{check.name}: {check.detail}")
    return tuple(warnings)
