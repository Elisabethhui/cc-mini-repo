from __future__ import annotations

from core.work_log import build_work_log_entry, render_work_log, write_work_log


def test_render_work_log_is_compact():
    entry = build_work_log_entry(
        task_id="task-040",
        goal="Implement local ignored work log generator",
        changed_files=["src/core/work_log.py", "tests/test_work_log.py"],
        tests=["pytest tests/test_work_log.py -v"],
        review_result="hold until targeted tests pass",
        risks=["manual review still needed"],
        next_step="Wire command surface in a later task",
    )

    text = render_work_log(entry)

    assert "# Work Log: task-040" in text
    assert "## Goal" in text
    assert "- src/core/work_log.py" in text
    assert "pytest tests/test_work_log.py -v" in text
    assert "hold until targeted tests pass" in text
    assert "Wire command surface in a later task" in text


def test_write_work_log_creates_parent_directory(tmp_path):
    entry = build_work_log_entry(
        task_id="task-040",
        goal="Generate work log",
        changed_files=["src/core/work_log.py"],
        tests=["pytest tests/test_work_log.py -v"],
        review_result="commit",
        risks=[],
        next_step="Task 041",
    )

    path = write_work_log(tmp_path, entry)

    assert path == tmp_path / ".ai-dev" / "worklogs" / "task-040.md"
    assert path.exists()
    assert "Generate work log" in path.read_text(encoding="utf-8")


def test_write_work_log_blocks_escape_from_worklog_directory(tmp_path):
    entry = build_work_log_entry(
        task_id="../../secrets",
        goal="bad path",
        changed_files=[],
        tests=[],
        review_result="hold",
        risks=[],
        next_step="none",
    )

    path = write_work_log(tmp_path, entry)

    assert path == tmp_path / ".ai-dev" / "worklogs" / "secrets.md"
    assert path.exists()
    assert tmp_path.joinpath("secrets.md").exists() is False


def test_build_work_log_entry_redacts_secrets_and_truncates():
    long_text = "password=abc123 " + ("x" * 400)
    entry = build_work_log_entry(
        task_id="task-040",
        goal=long_text,
        changed_files=[f"src/core/file_{index}.py" for index in range(20)],
        tests=[f"pytest tests/test_{index}.py -v" for index in range(10)],
        review_result="secret=visible should be redacted",
        risks=["token=abcd", "normal risk"],
        next_step="next " + ("y" * 400),
    )

    assert "[redacted]" in entry.goal
    assert "abc123" not in entry.goal
    assert "[redacted]" in entry.review_result
    assert entry.truncated is True
    assert len(entry.changed_files) == 12
    assert len(entry.tests) == 6
    assert entry.next_step.endswith("…")


def test_render_work_log_marks_truncated_note():
    entry = build_work_log_entry(
        task_id="task-040",
        goal="g" * 500,
        changed_files=[],
        tests=[],
        review_result="hold",
        risks=[],
        next_step="next",
    )

    text = render_work_log(entry)

    assert "## Note" in text
    assert "- truncated for safety" in text
