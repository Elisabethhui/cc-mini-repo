from __future__ import annotations

from core.workflow_doctor import DoctorCheck, WorkflowDoctorReport
from core.workflow_next import WorkflowTaskArtifacts, format_workflow_next, recommend_workflow_next
from core.workflow_status import CheckResult, GitSummary, WorkflowStatus


def _status(
    *,
    required_ok: bool = True,
    git_available: bool = True,
    git_clean: bool = True,
    git_entries: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
) -> WorkflowStatus:
    required = (
        CheckResult("AGENTS.md", required_ok, "file present" if required_ok else "file missing"),
        CheckResult(".ai-dev/README.md", required_ok, "file present" if required_ok else "file missing"),
    )
    git_summary = GitSummary(
        available=git_available,
        clean=git_clean,
        entries=git_entries,
        error="" if git_available else "git unavailable",
    )
    return WorkflowStatus(
        required_files=required,
        ignored_paths=(CheckResult(".ai-dev/tmp/", True, "directory present"),),
        codegraph=(CheckResult("codegraph command", False, "not installed"),),
        git=(CheckResult("git status", git_clean if git_available else False, "clean" if git_clean else "dirty"),),
        warnings=warnings,
        git_summary=git_summary,
    )


def _doctor(decision: str = "ok") -> WorkflowDoctorReport:
    return WorkflowDoctorReport(
        required_files=(DoctorCheck("AGENTS.md", "ok", "file present"),),
        local_artifacts=(DoctorCheck("git artifacts", "ok", "no tracked or staged local artifacts"),),
        markdown=(DoctorCheck("markdown files", "ok", "code fences closed"),),
        codegraph=(DoctorCheck("codegraph command", "warn", "not installed"),),
        decision=decision,
    )


def test_recommend_workflow_next_blocks_on_doctor_blocked():
    recommendation = recommend_workflow_next(
        status=_status(),
        doctor=_doctor("blocked"),
        artifacts=WorkflowTaskArtifacts(task_goal="Ship task"),
    )

    assert recommendation.state == "blocked"
    assert "Resolve blocked workflow doctor findings" in recommendation.next_action
    assert recommendation.requires_confirmation is False


def test_recommend_workflow_next_blocks_on_missing_required_files():
    recommendation = recommend_workflow_next(
        status=_status(required_ok=False),
        doctor=_doctor(),
        artifacts=WorkflowTaskArtifacts(task_goal="Ship task"),
    )

    assert recommendation.state == "blocked"
    assert "missing workflow scaffold" in recommendation.next_action.lower()
    assert "required workflow files" in recommendation.stop_condition.lower()


def test_recommend_workflow_next_requests_test_gate_for_dirty_worktree():
    recommendation = recommend_workflow_next(
        status=_status(git_clean=False, git_entries=(" M src/core/commands.py",)),
        doctor=_doctor(),
        artifacts=WorkflowTaskArtifacts(task_goal="Add command", tests_recorded=False),
    )

    assert recommendation.state == "needs_test_gate"
    assert "smallest useful verification" in recommendation.next_action
    assert recommendation.requires_confirmation is False


def test_recommend_workflow_next_requests_fresh_review_after_tests():
    recommendation = recommend_workflow_next(
        status=_status(git_clean=False, git_entries=(" M src/core/commands.py",)),
        doctor=_doctor(),
        artifacts=WorkflowTaskArtifacts(
            task_goal="Add command",
            tests_recorded=True,
            fresh_review_done=False,
        ),
    )

    assert recommendation.state == "needs_fresh_review"
    assert "fresh review" in recommendation.next_action.lower()


def test_recommend_workflow_next_requires_confirmation_for_commit():
    recommendation = recommend_workflow_next(
        status=_status(git_clean=False, git_entries=(" M src/core/commands.py",)),
        doctor=_doctor(),
        artifacts=WorkflowTaskArtifacts(
            task_goal="Add command",
            tests_recorded=True,
            fresh_review_done=True,
            review_decision="commit",
            work_log_written=True,
        ),
    )

    assert recommendation.state == "ready_to_commit"
    assert recommendation.requires_confirmation is True
    assert "confirm" in recommendation.stop_condition.lower()


def test_recommend_workflow_next_marks_done_when_clean_after_commit_decision():
    recommendation = recommend_workflow_next(
        status=_status(git_clean=True),
        doctor=_doctor(),
        artifacts=WorkflowTaskArtifacts(
            task_goal="Add command",
            tests_recorded=True,
            fresh_review_done=True,
            review_decision="commit",
            work_log_written=True,
        ),
    )

    assert recommendation.state == "done"
    assert recommendation.requires_confirmation is False


def test_format_workflow_next_is_stable():
    recommendation = recommend_workflow_next(
        status=_status(git_clean=False, git_entries=(" M src/core/commands.py",), warnings=("cache artifact visible in git status: pkg/__pycache__/x.pyc",)),
        doctor=_doctor(),
        artifacts=WorkflowTaskArtifacts(
            task_goal="Add command",
            tests_recorded=True,
            fresh_review_done=True,
            review_decision="commit",
            work_log_written=True,
        ),
    )

    text = format_workflow_next(recommendation)

    assert "Workflow Next" in text
    assert "State: ready_to_commit" in text
    assert "Next action:" in text
    assert "Stop condition:" in text
    assert "Requires confirmation: yes" in text
    assert "Reasons:" in text
    assert "Warnings:" in text
