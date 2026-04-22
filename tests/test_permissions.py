from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import os

from core.permissions import PermissionChecker, _plan_write_allowed
from core.plan import PlanModeManager
from core.tools.file_read import FileReadTool
from core.tools.bash import BashTool
from core.tools.file_edit_strict import FileEditTool


def test_read_only_tool_always_allowed():
    checker = PermissionChecker()
    result = checker.check(FileReadTool(), {"file_path": "/tmp/test.txt"})
    assert result == "allow"


def test_auto_approve_allows_everything():
    checker = PermissionChecker(auto_approve=True)
    assert checker.check(BashTool(), {"command": "rm -rf /"}) == "allow"
    assert checker.check(FileEditTool(), {"file_path": "/etc/passwd", "old_string": "x", "new_string": "y"}) == "allow"


def _mock_prompt_user(checker, response: str):
    """Patch _prompt_user to return a canned response without touching stdin."""
    def fake_prompt(tool, inputs):
        if response == "a":
            checker._always_allow.add(tool.name)
            return "allow"
        return "allow" if response == "y" else "deny"
    return patch.object(checker, "_prompt_user", side_effect=fake_prompt)


def test_bash_prompts_user_and_allows_on_y():
    checker = PermissionChecker()
    with _mock_prompt_user(checker, "y"):
        result = checker.check(BashTool(), {"command": "echo hello"})
    assert result == "allow"


def test_bash_prompts_user_and_denies_on_n():
    checker = PermissionChecker()
    with _mock_prompt_user(checker, "n"):
        result = checker.check(BashTool(), {"command": "rm something"})
    assert result == "deny"


def test_always_caches_approval():
    checker = PermissionChecker()
    with _mock_prompt_user(checker, "a"):
        checker.check(BashTool(), {"command": "echo first"})
    # Second call should NOT prompt — already cached via _always_allow
    result = checker.check(BashTool(), {"command": "echo second"})
    assert result == "allow"


def test_plan_mode_allows_only_the_plan_file(tmp_path: Path):
    checker = PermissionChecker()
    manager = PlanModeManager()
    plan_path = tmp_path / ".claude" / "plans" / "calm-forest.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("# draft\n", encoding="utf-8")
    manager._plan_file = plan_path
    manager._active = True
    checker.set_plan_manager(manager)

    write_tool = SimpleNamespace(name="Write")
    edit_tool = SimpleNamespace(name="Edit")
    bash_tool = SimpleNamespace(name="Bash")

    assert checker.check(write_tool, {"file_path": str(tmp_path / "other.md")}) == "deny"
    assert checker.check(edit_tool, {"file_path": str(tmp_path / "other.md")}) == "deny"
    assert checker.check(write_tool, {"file_path": str(plan_path)}) == "allow"
    assert checker.check(edit_tool, {"file_path": str(plan_path)}) == "allow"
    assert checker.check(bash_tool, {"command": "touch other.md"}) == "deny"


def test_plan_write_allowed_helper_matches_plan_path():
    assert _plan_write_allowed(
        "/tmp/.claude/plans/calm-forest.md",
        "/tmp/.claude/plans/calm-forest.md",
    )
    assert not _plan_write_allowed(
        "/tmp/.claude/plans/calm-forest.md",
        "/tmp/.claude/plans/other.md",
    )


def test_permission_checker_records_run_mode():
    checker = PermissionChecker()
    assert checker.get_run_mode() is None

    checker.set_run_mode("wiki_strict")
    assert checker.get_run_mode() == "wiki_strict"
