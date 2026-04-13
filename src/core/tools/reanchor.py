"""
Re-anchor Loop implementation (Phase 4)
Handles path/symbol repeat failures and triggers ask_user fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..wiki.taskpack import MicroForkNote, TaskPackManager


@dataclass
class ReanchorContext:
    """Context for re-anchor decision"""
    error_type: str = ""
    error_message: str = ""
    file_path: str = ""
    line_number: int | None = None
    symbol: str = ""
    total_attempts: int = 0
    previous_patches: list[dict] = field(default_factory=list)


class ReanchorLoop:
    """
    Phase 4: Re-anchor Loop controller.
    - Detects repeated failures
    - Triggers re-anchor analysis
    - Falls back to ask_user after threshold
    """

    # Thresholds
    MAX_PATCH_ATTEMPTS = 3
    MAX_PATH_ATTEMPTS = 3
    MAX_SYMBOL_ATTEMPTS = 3

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root)
        self.manager = TaskPackManager(workspace_root)
        self.failure_history: list[ReanchorContext] = []

    def should_reanchor(self, context: ReanchorContext) -> tuple[bool, str]:
        """
        Determine if we need to re-anchor (re-analyze) the problem.
        Returns: (should_reanchor, reason)
        """
        self.failure_history.append(context)

        # Check for repeated path failures
        path_failures = [c for c in self.failure_history if c.file_path == context.file_path]
        if len(path_failures) >= self.MAX_PATH_ATTEMPTS:
            return True, f"Path '{context.file_path}' failed {len(path_failures)} times"

        # Check for repeated symbol failures
        symbol_failures = [c for c in self.failure_history if c.symbol == context.symbol and c.symbol]
        if len(symbol_failures) >= self.MAX_SYMBOL_ATTEMPTS:
            return True, f"Symbol '{context.symbol}' failed {len(symbol_failures)} times"

        # Check for repeated patch failures
        if context.total_attempts >= self.MAX_PATCH_ATTEMPTS:
            return True, f"Patch failed {context.total_attempts} times"

        return False, ""

    def generate_reanchor_questions(self, context: ReanchorContext) -> list[str]:
        """
        Phase 4: Generate the "Six Questions" for re-anchor analysis.
        Based on goal_policy.md Re-anchor Loop.
        """
        questions = [
            f"1. What was the original intent for modifying {context.file_path or 'the target'}?",
            f"2. Has the file structure changed? (Error: {context.error_type})",
            f"3. Is the symbol '{context.symbol}' still at the expected location?",
            f"4. Are there conflicting changes in the codebase?",
            f"5. Should we broaden or narrow the search scope?",
            f"6. What alternative approaches exist to achieve the same goal?",
        ]
        return questions

    def create_micro_fork(self, task_id: str, original_goal: str, forked_goal: str, reason: str) -> MicroForkNote:
        """
        Create a Micro-Fork Note when re-anchor leads to a different approach.
        """
        fork = MicroForkNote(
            parent_task_id=task_id,
            original_goal=original_goal,
            forked_goal=forked_goal,
            branch_reason=reason,
        )
        self.manager.save_micro_fork(fork)
        return fork

    def check_ask_user_fallback(self, context: ReanchorContext) -> tuple[bool, str]:
        """
        Check if we should fall back to ask_user.
        Returns: (should_fallback, reason)
        """
        total_failures = len(self.failure_history)

        if total_failures >= 6:  # After 2 complete re-anchor cycles (3x2)
            return True, f"Total failures ({total_failures}) exceeded threshold. Human intervention required."

        if context.total_attempts >= self.MAX_PATCH_ATTEMPTS * 2:
            return True, f"Multiple re-anchor attempts failed. Human intervention required."

        return False, ""

    def format_reanchor_report(self, context: ReanchorContext, questions: list[str]) -> str:
        """Format re-anchor analysis for output"""
        lines = [
            "=" * 50,
            "RE-ANCHOR REQUIRED",
            "=" * 50,
            f"",
            f"Context:",
            f"  Error: {context.error_type}",
            f"  File: {context.file_path or 'unknown'}",
            f"  Line: {context.line_number or 'unknown'}",
            f"  Symbol: {context.symbol or 'unknown'}",
            f"  Attempts: {context.total_attempts}",
            f"",
            f"Re-anchor Questions:",
        ]
        for q in questions:
            lines.append(f"  {q}")
        lines.append("")
        lines.append("=" * 50)
        return "\n".join(lines)


def execute_with_reanchor(
    func,
    reanchor: ReanchorLoop,
    task_id: str,
    original_goal: str,
    *args,
    on_reanchor: callable | None = None,
    on_ask_user: callable | None = None,
    **kwargs
):
    """
    Phase 4: Execute function with re-anchor loop.

    Example:
        reanchor = ReanchorLoop("/workspace")
        result = execute_with_reanchor(
            tool.execute,
            reanchor,
            "task-001",
            "Fix bug in parser",
            file_path="parser.py",
            old_string="...",
            new_string="..."
        )
    """
    from .error_handler import RetryLoop

    retry = RetryLoop(max_retries=3)

    while True:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Build re-anchor context
            context = ReanchorContext(
                error_type=type(e).__name__,
                error_message=str(e),
                total_attempts=len(retry.attempts) + 1,
            )

            # Check if we should re-anchor
            should_reanchor, reason = reanchor.should_reanchor(context)

            if should_reanchor:
                questions = reanchor.generate_reanchor_questions(context)
                report = reanchor.format_reanchor_report(context, questions)

                if on_reanchor:
                    on_reanchor(reanchor, context, questions)

                # Check for ask_user fallback
                should_fallback, fallback_reason = reanchor.check_ask_user_fallback(context)

                if should_fallback:
                    if on_ask_user:
                        on_ask_user(reanchor, context, fallback_reason)
                    raise RuntimeError(f"{fallback_reason}\n{report}") from e

                # Log micro-fork
                reanchor.create_micro_fork(
                    task_id=task_id,
                    original_goal=original_goal,
                    forked_goal=f"{original_goal} (re-anchored: {reason})",
                    reason=reason,
                )

            # Check retry
            should_retry, retry_reason = retry.should_retry(e)
            if not should_retry:
                raise
