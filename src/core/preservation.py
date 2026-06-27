from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .context_budget import BudgetState, BudgetReport
from .runtime_state import RuntimeStateStore


MAX_TOOL_RESULT_CHARS = 8_000  # threshold for externalising a tool result


@dataclass
class PreservationResult:
    """Outcome of the preservation pipeline."""

    next_action: str = ""
    saved_paths: list[str] = field(default_factory=list)
    state_snapshot: dict[str, Any] = field(default_factory=dict)
    artifact_handles: list[str] = field(default_factory=list)


class PreservationPipeline:
    """N-context preservation pipeline.

    Handles *warning*, *preserve*, *split*, and *hard_stop* states by
    extracting structured state, materialising large artifacts, and
    persisting everything to the local runtime store.

    No LLM is called.
    """

    def __init__(self, state_store: RuntimeStateStore | None = None):
        self.state_store = state_store

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(
        self,
        budget_state: BudgetState,
        messages: list[dict],
        *,
        goal: str = "",
        phase: str = "",
        current_step: str = "",
        decisions: list[str] | None = None,
        open_questions: list[str] | None = None,
        artifacts: list[str] | None = None,
        budget_report: BudgetReport | None = None,
    ) -> PreservationResult:
        """Execute the pipeline for *budget_state*.

        Returns a ``PreservationResult`` containing the recommended
        ``next_action`` and a list of paths that were written.
        """
        if budget_state == BudgetState.WARNING:
            return self._handle_warning(
                messages, current_step=current_step, budget_report=budget_report
            )
        if budget_state == BudgetState.PRESERVE:
            return self._handle_preserve(
                messages,
                goal=goal,
                phase=phase,
                current_step=current_step,
                decisions=decisions,
                open_questions=open_questions,
                artifacts=artifacts,
                budget_report=budget_report,
            )
        if budget_state == BudgetState.SPLIT:
            return self._handle_split(
                messages,
                goal=goal,
                phase=phase,
                current_step=current_step,
                budget_report=budget_report,
            )
        if budget_state == BudgetState.HARD_STOP:
            return self._handle_hard_stop(
                messages,
                goal=goal,
                phase=phase,
                current_step=current_step,
                budget_report=budget_report,
            )
        # OK — nothing to do
        return PreservationResult(next_action="Continue normally.")

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------

    def _handle_warning(
        self,
        messages: list[dict],
        *,
        current_step: str = "",
        budget_report: BudgetReport | None = None,
    ) -> PreservationResult:
        """Light cleanup: drop low-value history, truncate old tool outputs."""
        _prune_old_tool_results(messages)
        if self.state_store and budget_report:
            self.state_store.append_budget_report(_budget_report_to_dict(budget_report))
        return PreservationResult(
            next_action="Light cleanup applied. Continue with reduced context."
        )

    def _handle_preserve(
        self,
        messages: list[dict],
        *,
        goal: str = "",
        phase: str = "",
        current_step: str = "",
        decisions: list[str] | None = None,
        open_questions: list[str] | None = None,
        artifacts: list[str] | None = None,
        budget_report: BudgetReport | None = None,
    ) -> PreservationResult:
        """Extract structured state, materialise artifacts, persist."""
        summary = _extract_structured_summary(messages)
        summary["goal"] = goal or summary.get("goal", "")
        summary["phase"] = phase or summary.get("phase", "")
        summary["current_step"] = current_step or summary.get("current_step", "")
        summary["decisions"] = list(decisions or summary.get("decisions", []))
        summary["open_questions"] = list(open_questions or summary.get("open_questions", []))
        summary["artifacts"] = list(artifacts or summary.get("artifacts", []))

        # Materialise large tool results as artifacts
        artifact_handles: list[str] = []
        if self.state_store:
            artifact_handles = _materialise_large_tool_results(
                messages, self.state_store
            )

        saved_paths: list[str] = []
        if self.state_store:
            # Persist structured state
            self.state_store.patch_state(
                phase=summary["phase"],
                current_step=summary["current_step"],
                goal=summary["goal"],
                decisions=summary["decisions"],
                open_questions=summary["open_questions"],
                artifacts=summary["artifacts"],
                next_action="Review preserved state and continue with narrower scope.",
            )
            saved_paths.append(str(self.state_store._state_path))

            # Budget report
            if budget_report:
                self.state_store.append_budget_report(
                    _budget_report_to_dict(budget_report)
                )
                saved_paths.append(str(self.state_store._budget_reports_path))

            # Step log
            step_path = self.state_store.write_step_log(
                f"preserve-{summary['current_step']}",
                _format_preserve_step(summary, artifact_handles),
            )
            saved_paths.append(str(step_path))

        return PreservationResult(
            next_action="Review preserved state and continue with narrower scope.",
            saved_paths=saved_paths,
            state_snapshot=summary,
            artifact_handles=artifact_handles,
        )

    def _handle_split(
        self,
        messages: list[dict],
        *,
        goal: str = "",
        phase: str = "",
        current_step: str = "",
        budget_report: BudgetReport | None = None,
    ) -> PreservationResult:
        """Mark the current task as too large and recommend splitting."""
        saved_paths: list[str] = []
        if self.state_store:
            self.state_store.patch_state(
                phase=phase,
                current_step=current_step,
                goal=goal,
                next_action="Split current task into smaller executable batches.",
            )
            saved_paths.append(str(self.state_store._state_path))

            if budget_report:
                self.state_store.append_budget_report(
                    _budget_report_to_dict(budget_report)
                )
                saved_paths.append(str(self.state_store._budget_reports_path))

            step_path = self.state_store.write_step_log(
                f"split-{current_step}",
                f"# Split Required\n\n"
                f"Current step **{current_step}** exceeds the safe context budget.\n\n"
                f"**Goal:** {goal}\n\n"
                f"**Next action:** Break this step into smaller executable batches.\n",
            )
            saved_paths.append(str(step_path))

        return PreservationResult(
            next_action="Split current task into smaller executable batches.",
            saved_paths=saved_paths,
            state_snapshot={"goal": goal, "phase": phase, "current_step": current_step},
        )

    def _handle_hard_stop(
        self,
        messages: list[dict],
        *,
        goal: str = "",
        phase: str = "",
        current_step: str = "",
        budget_report: BudgetReport | None = None,
    ) -> PreservationResult:
        """Final fallback: save state and require human decision."""
        saved_paths: list[str] = []
        if self.state_store:
            self.state_store.patch_state(
                phase=phase,
                current_step=current_step,
                goal=goal,
                next_action="HARD_STOP: Human decision required. Narrow scope or run /resume-from-checkpoint.",
            )
            saved_paths.append(str(self.state_store._state_path))

            if budget_report:
                self.state_store.append_budget_report(
                    _budget_report_to_dict(budget_report)
                )
                saved_paths.append(str(self.state_store._budget_reports_path))

            step_path = self.state_store.write_step_log(
                f"hard-stop-{current_step}",
                f"# Hard Stop\n\n"
                f"Context budget exceeded hard-stop threshold at step **{current_step}**.\n\n"
                f"**Goal:** {goal}\n\n"
                f"**Next action:** Narrow scope or run `/resume-from-checkpoint`.\n",
            )
            saved_paths.append(str(step_path))

        return PreservationResult(
            next_action="HARD_STOP: Human decision required. Narrow scope or run /resume-from-checkpoint.",
            saved_paths=saved_paths,
            state_snapshot={"goal": goal, "phase": phase, "current_step": current_step},
        )


# ---------------------------------------------------------------------------
# Helpers (no LLM, deterministic)
# ---------------------------------------------------------------------------

def _extract_structured_summary(messages: list[dict]) -> dict[str, Any]:
    """Extract a structured summary from the message list."""
    files_seen: list[str] = []
    symbols_seen: list[str] = []
    test_evidence: list[str] = []
    risks: list[str] = []
    decisions: list[str] = []
    open_questions: list[str] = []

    for msg in messages:
        content = msg.get("content", "")
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text += block.get("text", "")
                elif isinstance(block, dict) and block.get("type") == "tool_result":
                    tc = block.get("content", "")
                    if isinstance(tc, str):
                        text += tc

        # Simple heuristic extraction
        lower = text.lower()
        if "file_path" in text or "file:" in lower:
            # Try to extract file paths
            import re
            for m in re.finditer(r'["\']([^"\']*\.(?:py|md|toml|json|yaml|yml))["\']', text):
                fp = m.group(1)
                if fp not in files_seen:
                    files_seen.append(fp)
        if "def " in text or "class " in text:
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("def ") or stripped.startswith("class "):
                    symbol = stripped.split("(")[0].split(":")[0].strip()
                    if symbol not in symbols_seen:
                        symbols_seen.append(symbol)
        if "test_" in lower or "pytest" in lower:
            test_evidence.append("Tests mentioned in conversation.")
        if "error" in lower or "fail" in lower or "exception" in lower:
            risks.append("Errors or failures observed.")
        if "decision" in lower:
            for line in text.splitlines():
                if "decision" in line.lower():
                    decisions.append(line.strip("- *").strip())
        if "?" in text:
            for line in text.splitlines():
                if "?" in line and len(line) < 200:
                    open_questions.append(line.strip("- *").strip())

    return {
        "goal": "",
        "phase": "",
        "current_step": "",
        "decisions": decisions[:10],
        "open_questions": open_questions[:10],
        "files_seen": files_seen[:20],
        "symbols_seen": symbols_seen[:20],
        "test_evidence": test_evidence[:5],
        "risks": risks[:5],
        "next_action": "",
    }


def _prune_old_tool_results(messages: list[dict]) -> None:
    """In-place truncation of tool_result blocks in older messages."""
    for i, msg in enumerate(messages[:-2]):  # keep last two messages intact
        content = msg.get("content", "")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    tc = block.get("content", "")
                    if isinstance(tc, str) and len(tc) > MAX_TOOL_RESULT_CHARS:
                        block["content"] = (
                            tc[:MAX_TOOL_RESULT_CHARS]
                            + f"\n\n[...truncated from {len(tc)} chars]"
                        )


def _materialise_large_tool_results(
    messages: list[dict], store: RuntimeStateStore | None
) -> list[str]:
    if store is None:
        return []
    """Save oversized tool results as artifacts and replace with handles.

    Returns a list of artifact handles written.
    """
    handles: list[str] = []
    for msg in messages:
        content = msg.get("content", "")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                tc = block.get("content", "")
                tool_use_id = block.get("tool_use_id", "unknown")
                if isinstance(tc, str) and len(tc) > MAX_TOOL_RESULT_CHARS:
                    artifact_name = f"tool_result_{tool_use_id}.txt"
                    store.write_artifact(artifact_name, tc)
                    handle = f"[artifact: {artifact_name}]"
                    block["content"] = (
                        f"{handle}\n\n"
                        f"[Original output was {len(tc)} chars; saved to artifact.]"
                    )
                    handles.append(handle)
    return handles


def _budget_report_to_dict(report: BudgetReport) -> dict[str, Any]:
    return {
        "context_window": report.context_window,
        "projected_total_tokens": report.projected_total_tokens,
        "available_input_tokens": report.available_input_tokens,
        "state": report.state.value,
        "usage_ratio": report.usage_ratio,
        "warnings": list(report.warnings),
    }


def _format_preserve_step(summary: dict, artifact_handles: list[str]) -> str:
    lines = [
        "# Preserve Step",
        "",
        f"**Goal:** {summary.get('goal', '')}",
        f"**Phase:** {summary.get('phase', '')}",
        f"**Current Step:** {summary.get('current_step', '')}",
        "",
        "## Decisions",
    ]
    for d in summary.get("decisions", []):
        lines.append(f"- {d}")
    if not summary.get("decisions"):
        lines.append("_None recorded._")

    lines.extend(["", "## Open Questions"])
    for q in summary.get("open_questions", []):
        lines.append(f"- {q}")
    if not summary.get("open_questions"):
        lines.append("_None recorded._")

    lines.extend(["", "## Files Seen"])
    for f in summary.get("files_seen", []):
        lines.append(f"- `{f}`")

    lines.extend(["", "## Artifact Handles"])
    for h in artifact_handles:
        lines.append(f"- {h}")
    if not artifact_handles:
        lines.append("_No large tool results externalised._")

    lines.extend(["", f"**Next action:** {summary.get('next_action', '')}"])
    return "\n".join(lines) + "\n"
