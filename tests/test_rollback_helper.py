from __future__ import annotations

from pathlib import Path

from core.rollback_helper import GitCommandResult, collect_rollback_report, format_rollback_report


class FakeGitRunner:
    def __init__(self, mapping: dict[tuple[str, ...], GitCommandResult]) -> None:
        self.mapping = mapping
        self.calls: list[tuple[tuple[str, ...], float]] = []

    def __call__(self, root: Path, args: list[str], timeout_seconds: float) -> GitCommandResult:
        key = tuple(args)
        self.calls.append((key, timeout_seconds))
        if key not in self.mapping:
            return GitCommandResult(returncode=1, stdout="", stderr="missing fake result")
        return self.mapping[key]


def test_collect_rollback_report_handles_missing_git_gracefully(tmp_path):
    runner = FakeGitRunner({})

    report = collect_rollback_report(tmp_path, git_runner=runner)

    assert report.git_available is False
    assert report.suggestions == ()
    assert report.warnings == ("git status unavailable",)


def test_collect_rollback_report_recommends_unstaged_and_committed_actions(tmp_path):
    runner = FakeGitRunner(
        {
            ("status", "--short"): GitCommandResult(
                returncode=0,
                stdout=" M src/core/commands.py\n?? tests/test_commands.py\n",
            ),
            ("rev-parse", "--verify", "HEAD"): GitCommandResult(
                returncode=0,
                stdout="1234567890abcdef1234567890abcdef12345678\n",
            ),
        }
    )

    report = collect_rollback_report(tmp_path, git_runner=runner)

    assert report.git_available is True
    assert report.unstaged_paths == ("src/core/commands.py",)
    assert report.staged_paths == ()
    assert report.head_commit == "1234567890abcdef1234567890abcdef12345678"
    assert report.suggestions[0].command == "git restore -- src/core/commands.py"
    assert report.suggestions[-1].command == "git revert 1234567890ab"
    assert report.warnings == ()


def test_collect_rollback_report_recommends_staged_actions_separately(tmp_path):
    runner = FakeGitRunner(
        {
            ("status", "--short"): GitCommandResult(
                returncode=0,
                stdout="M  src/core/workflow_doctor.py\nA  tests/test_workflow_doctor.py\n",
            ),
            ("rev-parse", "--verify", "HEAD"): GitCommandResult(
                returncode=0,
                stdout="abcdefabcdefabcdefabcdefabcdefabcdefabcd\n",
            ),
        }
    )

    report = collect_rollback_report(tmp_path, git_runner=runner)

    assert report.unstaged_paths == ()
    assert report.staged_paths == (
        "src/core/workflow_doctor.py",
        "tests/test_workflow_doctor.py",
    )
    commands = [item.command for item in report.suggestions]
    assert "git restore --staged -- src/core/workflow_doctor.py tests/test_workflow_doctor.py" in commands
    assert "git restore --worktree -- src/core/workflow_doctor.py tests/test_workflow_doctor.py" in commands
    assert "git revert abcdefabcdef" in commands


def test_collect_rollback_report_warns_when_head_is_unavailable(tmp_path):
    runner = FakeGitRunner(
        {
            ("status", "--short"): GitCommandResult(returncode=0, stdout=""),
        }
    )

    report = collect_rollback_report(tmp_path, git_runner=runner)

    assert report.unstaged_paths == ()
    assert report.staged_paths == ()
    assert "head commit unavailable" in report.warnings
    assert "cannot suggest committed rollback without a resolved HEAD commit" in report.warnings
    assert "worktree is clean; committed rollback may be the only relevant option" in report.warnings


def test_format_rollback_report_is_stable(tmp_path):
    runner = FakeGitRunner(
        {
            ("status", "--short"): GitCommandResult(returncode=0, stdout=" M src/core/rollback_helper.py\n"),
            ("rev-parse", "--verify", "HEAD"): GitCommandResult(
                returncode=0,
                stdout="fedcba9876543210fedcba9876543210fedcba98\n",
            ),
        }
    )

    report = collect_rollback_report(tmp_path, git_runner=runner)
    text = format_rollback_report(report)

    assert "Rollback Helper" in text
    assert "Git available: yes" in text
    assert "Unstaged paths: 1" in text
    assert "Staged paths: 0" in text
    assert "Head commit: fedcba987654" in text
    assert "git restore -- src/core/rollback_helper.py" in text
    assert "git revert fedcba987654" in text
