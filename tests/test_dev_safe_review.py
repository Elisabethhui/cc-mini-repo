from __future__ import annotations

import pytest

from core.dev_contract import DevReviewResult, TaskResult
from core.dev_review import review_task_result


def test_passed_no_risk_review_decision_pass():
    task_result = TaskResult(
        task_id="t1",
        status="passed",
        verification_passed=True,
        risks=["low risk"],
    )
    review = review_task_result(task_result)

    assert review.review_decision == "pass"
    assert review.can_finish is True
    assert review.requires_user_commit is True


def test_failed_review_decision_revise():
    task_result = TaskResult(
        task_id="t1",
        status="failed",
        verification_passed=False,
        risks=["exit code mismatch"],
    )
    review = review_task_result(task_result)

    assert review.review_decision == "revise"
    assert review.can_finish is False
    assert review.requires_user_commit is False


def test_blocked_forbidden_review_decision_blocked():
    task_result = TaskResult(
        task_id="t1",
        status="blocked",
        verification_passed=False,
        risks=["Forbidden files modified: ['src/core/engine.py']"],
    )
    review = review_task_result(task_result)

    assert review.review_decision == "blocked"
    assert review.can_finish is False
    assert review.requires_user_commit is False


def test_blocked_scope_review_decision_blocked():
    task_result = TaskResult(
        task_id="t1",
        status="blocked",
        verification_passed=False,
        risks=["Out-of-bounds files modified: ['src/unexpected.py']"],
    )
    review = review_task_result(task_result)

    assert review.review_decision == "blocked"
    assert review.can_finish is False
    assert review.requires_user_commit is False


def test_split_review_decision_blocked():
    task_result = TaskResult(
        task_id="t1",
        status="split",
        next_action="Split task",
    )
    review = review_task_result(task_result)

    assert review.review_decision == "blocked"
    assert review.can_finish is False


def test_needs_planning_review_decision_blocked():
    task_result = TaskResult(
        task_id="t1",
        status="needs_planning",
        next_action="Refine plan",
    )
    review = review_task_result(task_result)

    assert review.review_decision == "blocked"
    assert review.can_finish is False


def test_review_decision_never_commit():
    cases = [
        TaskResult(task_id="t1", status="passed", verification_passed=True),
        TaskResult(task_id="t1", status="failed", verification_passed=False),
        TaskResult(
            task_id="t1",
            status="blocked",
            risks=["Forbidden files modified: []"],
        ),
        TaskResult(task_id="t1", status="split"),
        TaskResult(task_id="t1", status="needs_planning"),
    ]
    for task_result in cases:
        review = review_task_result(task_result)
        assert review.review_decision != "commit"
        assert review.review_decision in {"pass", "revise", "blocked"}


def test_passed_with_scope_risk_is_blocked():
    task_result = TaskResult(
        task_id="t1",
        status="passed",
        verification_passed=True,
        risks=["Out-of-bounds files modified: ['src/other.py']"],
    )
    review = review_task_result(task_result)

    assert review.review_decision == "blocked"
    assert review.can_finish is False


def test_dev_review_result_round_trip():
    review = DevReviewResult(
        task_id="t1",
        review_decision="pass",
        can_finish=True,
        requires_user_commit=True,
        worklog_path=".ai-dev/worklogs/run.md",
    )
    restored = DevReviewResult.from_json(review.to_json())
    assert restored.task_id == "t1"
    assert restored.review_decision == "pass"
    assert restored.can_finish is True
    assert restored.worklog_path == ".ai-dev/worklogs/run.md"
