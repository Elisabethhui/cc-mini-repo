"""Tests for review_packet.py — uses fake git runners, no real git required."""

from __future__ import annotations

import pytest

from core.review_packet import (
    _changed_files_from_stat,
    _changed_files_from_status,
    _is_local_artifact_path,
    _truncate_diff,
    build_review_packet,
)


def _make_runner(outputs: dict[tuple[str, ...], str]) -> callable:
    """Return a fake git runner that looks up stdout by argument tuple."""
    def runner(args: list[str]) -> str:
        return outputs.get(tuple(args), "")
    return runner


# ---------------------------------------------------------------------------
# _changed_files_from_stat
# ---------------------------------------------------------------------------

def test_changed_files_from_stat_basic() -> None:
    stat = (
        " src/core/review_packet.py | 12 +++++++++---\n"
        " tests/test_review_packet.py | 45 ++++++++++++++++++++++++++++++\n"
    )
    assert _changed_files_from_stat(stat) == [
        "src/core/review_packet.py",
        "tests/test_review_packet.py",
    ]


def test_changed_files_from_stat_ignores_blank_and_indented() -> None:
    stat = (
        " src/core/foo.py | 3 +++\n"
        " \n"
        " 2 files changed, 3 insertions(+)\n"
    )
    assert _changed_files_from_stat(stat) == ["src/core/foo.py"]


# ---------------------------------------------------------------------------
# _changed_files_from_status
# ---------------------------------------------------------------------------

def test_changed_files_from_status_basic() -> None:
    status = (
        " M src/core/review_packet.py\n"
        "?? tests/test_review_packet.py\n"
        "R  old.py -> new.py\n"
    )
    assert _changed_files_from_status(status) == [
        "src/core/review_packet.py",
        "tests/test_review_packet.py",
        "new.py",
    ]


# ---------------------------------------------------------------------------
# _is_local_artifact_path
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "path,expected",
    [
        (".ai-dev/tasks/039.md", True),
        (".ai-dev/tmp/foo.txt", True),
        (".codegraph/index.json", True),
        (".codebase-memory/cache.db", True),
        ("src/core/review_packet.py", False),
        ("tests/test_review_packet.py", False),
        ("foo/.ai-dev/tasks/x.md", True),
    ],
)
def test_is_local_artifact_path(path: str, expected: bool) -> None:
    assert _is_local_artifact_path(path) is expected


# ---------------------------------------------------------------------------
# _truncate_diff
# ---------------------------------------------------------------------------

def test_truncate_diff_under_limits() -> None:
    diff = "line1\nline2\n"
    result, truncated = _truncate_diff(diff, max_lines=10, max_bytes=1_000)
    assert result == diff
    assert truncated is False


def test_truncate_diff_by_lines() -> None:
    diff = "\n".join(f"line{i}" for i in range(100)) + "\n"
    result, truncated = _truncate_diff(diff, max_lines=10, max_bytes=1_000_000)
    assert truncated is True
    assert "... [truncated]" in result
    assert result.count("\n") == 11  # 10 lines + truncation marker line


def test_truncate_diff_by_bytes() -> None:
    diff = "A" * 10_000 + "\n"
    result, truncated = _truncate_diff(diff, max_lines=10_000, max_bytes=100)
    assert truncated is True
    assert "... [truncated]" in result
    assert len(result.encode("utf-8")) <= 150  # rough bound


# ---------------------------------------------------------------------------
# build_review_packet — basic (no diff)
# ---------------------------------------------------------------------------

def test_build_review_packet_basic_no_diff() -> None:
    runner = _make_runner({
        ("diff", "--stat"): " src/core/foo.py | 3 +++\n",
    })
    packet = build_review_packet("Implement foo", runner)
    assert packet.task_goal == "Implement foo"
    assert packet.changed_files == ["src/core/foo.py"]
    assert packet.diff_stat == "src/core/foo.py | 3 +++"
    assert packet.test_summary is None
    assert packet.truncated is False
    assert packet.local_artifact_flags == []
    assert packet.risk_notes == []


def test_build_review_packet_uses_status_fallback() -> None:
    runner = _make_runner({
        ("diff", "--stat"): "",  # empty — no unstaged changes
        ("status", "--short"): "M  src/core/bar.py\n",
    })
    packet = build_review_packet("Implement bar", runner)
    assert packet.changed_files == ["src/core/bar.py"]


def test_build_review_packet_flags_local_artifacts() -> None:
    runner = _make_runner({
        ("diff", "--stat"): " .ai-dev/tasks/039.md | 2 ++\n src/core/foo.py | 3 +++\n",
    })
    packet = build_review_packet("Task 039", runner)
    assert ".ai-dev/tasks/039.md" in packet.local_artifact_flags
    assert len(packet.risk_notes) == 1


# ---------------------------------------------------------------------------
# build_review_packet — with focused diffs
# ---------------------------------------------------------------------------

def test_build_review_packet_with_focused_diff() -> None:
    runner = _make_runner({
        ("diff", "--stat"): " src/core/foo.py | 3 +++\n",
        ("diff", "--", "src/core/foo.py"): "+added line\n",
    })
    packet = build_review_packet(
        "Implement foo", runner, include_diff=True, max_diff_lines=10, max_diff_bytes=1_000
    )
    assert "src/core/foo.py" in packet.focused_diffs
    assert packet.focused_diffs["src/core/foo.py"] == "+added line\n"
    assert packet.truncated is False


def test_build_review_packet_truncates_large_diff() -> None:
    long_diff = "\n".join(f"+line{i}" for i in range(200)) + "\n"
    runner = _make_runner({
        ("diff", "--stat"): " src/core/foo.py | 200 +++\n",
        ("diff", "--", "src/core/foo.py"): long_diff,
    })
    packet = build_review_packet(
        "Implement foo", runner, include_diff=True, max_diff_lines=10, max_diff_bytes=1_000_000
    )
    assert packet.truncated is True
    assert "... [truncated]" in packet.focused_diffs["src/core/foo.py"]


def test_build_review_packet_fallback_to_staged_diff() -> None:
    """When unstaged diff for a file is empty, try staged diff."""
    runner = _make_runner({
        ("diff", "--stat"): " src/core/foo.py | 3 +++\n",
        ("diff", "--", "src/core/foo.py"): "",  # empty unstaged
        ("diff", "--staged", "--", "src/core/foo.py"): "+staged line\n",
    })
    packet = build_review_packet(
        "Implement foo", runner, include_diff=True
    )
    assert packet.focused_diffs["src/core/foo.py"] == "+staged line\n"


# ---------------------------------------------------------------------------
# build_review_packet — test summary
# ---------------------------------------------------------------------------

def test_build_review_packet_with_test_summary() -> None:
    runner = _make_runner({("diff", "--stat"): ""})
    packet = build_review_packet(
        "Implement foo", runner, test_summary="3 passed, 0 failed"
    )
    assert packet.test_summary == "3 passed, 0 failed"


# ---------------------------------------------------------------------------
# Error resilience
# ---------------------------------------------------------------------------

def test_build_review_packet_git_runner_raises() -> None:
    def bad_runner(_args: list[str]) -> str:
        raise RuntimeError("git not found")
    packet = build_review_packet("Implement foo", bad_runner)
    assert packet.changed_files == []
    assert packet.diff_stat == ""


# ---------------------------------------------------------------------------
# Empty / edge cases
# ---------------------------------------------------------------------------

def test_build_review_packet_no_changes() -> None:
    runner = _make_runner({
        ("diff", "--stat"): "",
        ("status", "--short"): "",
    })
    packet = build_review_packet("Implement foo", runner)
    assert packet.changed_files == []
    assert packet.diff_stat == ""
