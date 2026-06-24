from __future__ import annotations

from pathlib import Path

from core.review_packet import GitCommandResult, build_review_packet, format_review_packet


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


def test_build_review_packet_collects_compact_review_inputs(tmp_path):
    runner = FakeGitRunner(
        {
            ("status", "--short"): GitCommandResult(
                returncode=0,
                stdout=" M src/core/commands.py\n?? tests/test_commands.py\n",
            ),
            ("diff", "--stat"): GitCommandResult(
                returncode=0,
                stdout=" src/core/commands.py | 12 +++++++++---\n tests/test_commands.py | 8 ++++++--\n 2 files changed, 14 insertions(+), 6 deletions(-)\n",
            ),
            ("diff", "--unified=0", "--no-ext-diff", "--", "src/core/commands.py", "tests/test_commands.py"): GitCommandResult(
                returncode=0,
                stdout="@@ -1 +1 @@\n-old\n+new\n",
            ),
        }
    )

    packet = build_review_packet(
        tmp_path,
        task_goal="Add workflow test command",
        test_summary="pytest tests/test_commands.py -v passed",
        focus_files=["src/core/commands.py", "tests/test_commands.py"],
        git_runner=runner,
    )

    assert packet.task_goal == "Add workflow test command"
    assert packet.changed_files == ("src/core/commands.py", "tests/test_commands.py")
    assert packet.diff_stat[-1] == " 2 files changed, 14 insertions(+), 6 deletions(-)"
    assert "pytest tests/test_commands.py -v passed" == packet.test_summary
    assert "@@ -1 +1 @@" in packet.focused_diff
    assert packet.risks == ()
    assert packet.warnings == ()
    assert packet.truncated is False
    assert runner.calls[0][1] == 2.0


def test_build_review_packet_flags_local_artifact_paths(tmp_path):
    runner = FakeGitRunner(
        {
            ("status", "--short"): GitCommandResult(
                returncode=0,
                stdout="?? .ai-dev/tmp/state.md\n M pkg/__pycache__/mod.pyc\n",
            ),
            ("diff", "--stat"): GitCommandResult(
                returncode=0,
                stdout=" .ai-dev/tmp/state.md | 1 +\n 1 file changed, 1 insertion(+)\n",
            ),
            ("diff", "--unified=0", "--no-ext-diff", "--", ".ai-dev/tmp/state.md", "pkg/__pycache__/mod.pyc"): GitCommandResult(
                returncode=0,
                stdout="",
            ),
        }
    )

    packet = build_review_packet(
        tmp_path,
        task_goal="Inspect risky artifacts",
        test_summary="not run",
        git_runner=runner,
    )

    assert any("local artifact path visible in git status" in risk for risk in packet.risks)
    assert any("cache artifact visible in git status" in risk for risk in packet.risks)


def test_build_review_packet_truncates_large_focused_diff(tmp_path):
    large_diff = "x" * 2000
    runner = FakeGitRunner(
        {
            ("status", "--short"): GitCommandResult(returncode=0, stdout=" M src/core/review_packet.py\n"),
            ("diff", "--stat"): GitCommandResult(returncode=0, stdout=" src/core/review_packet.py | 30 ++++++++++++++++++++++++++++++\n"),
            ("diff", "--unified=0", "--no-ext-diff", "--", "src/core/review_packet.py"): GitCommandResult(
                returncode=0,
                stdout=large_diff,
            ),
        }
    )

    packet = build_review_packet(
        tmp_path,
        task_goal="Build review packet",
        test_summary="pytest tests/test_review_packet.py -v passed",
        focus_files=["src/core/review_packet.py"],
        git_runner=runner,
        max_diff_chars=120,
    )

    assert packet.truncated is True
    assert len(packet.focused_diff) <= 120
    assert packet.focused_diff.endswith("…")


def test_build_review_packet_handles_git_failures_without_crashing(tmp_path):
    runner = FakeGitRunner(
        {
            ("status", "--short"): GitCommandResult(returncode=1, stdout="", stderr="git failed"),
            ("diff", "--stat"): GitCommandResult(returncode=1, stdout="", stderr="git failed"),
        }
    )

    packet = build_review_packet(
        tmp_path,
        task_goal="Build packet with missing git",
        test_summary="not run",
        git_runner=runner,
    )

    assert packet.changed_files == ()
    assert packet.diff_stat == ()
    assert "git status unavailable" in packet.warnings
    assert "git diff --stat unavailable" in packet.warnings
    assert "no changed files detected" in packet.warnings


def test_format_review_packet_is_stable(tmp_path):
    runner = FakeGitRunner(
        {
            ("status", "--short"): GitCommandResult(returncode=0, stdout=" M src/core/review_packet.py\n"),
            ("diff", "--stat"): GitCommandResult(returncode=0, stdout=" src/core/review_packet.py | 10 +++++++---\n"),
            ("diff", "--unified=0", "--no-ext-diff", "--", "src/core/review_packet.py"): GitCommandResult(
                returncode=0,
                stdout="password = 'redacted'\n",
            ),
        }
    )

    packet = build_review_packet(
        tmp_path,
        task_goal="Create compact review packet",
        test_summary="pytest tests/test_review_packet.py -v passed",
        focus_files=["src/core/review_packet.py"],
        git_runner=runner,
    )
    text = format_review_packet(packet)

    assert "Review Packet" in text
    assert "Task goal: Create compact review packet" in text
    assert "Files:" in text
    assert "- src/core/review_packet.py" in text
    assert "Diff stat:" in text
    assert "Focused diff:" in text
    assert "Risks:" in text
    assert "password-like text" in text
