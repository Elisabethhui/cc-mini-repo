from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BudgetState(str, Enum):
    """Budget pressure states for the N-context runtime."""

    OK = "ok"
    WARNING = "warning"
    PRESERVE = "preserve"
    SPLIT = "split"
    HARD_STOP = "hard_stop"


@dataclass(frozen=True)
class BudgetThresholds:
    """Ratio-based thresholds relative to context_window.

    All ratios are in [0.0, 1.0].
    """

    warning_ratio: float = 0.65
    preserve_ratio: float = 0.75
    split_ratio: float = 0.85
    hard_stop_ratio: float = 0.92


@dataclass(frozen=True)
class BudgetReport:
    """Complete budget breakdown before a model call."""

    context_window: int
    system_prompt_tokens: int
    tool_schema_tokens: int
    message_tokens: int
    packed_context_tokens: int
    tool_result_tokens: int
    reserved_output_tokens: int
    safety_margin_tokens: int
    projected_total_tokens: int
    available_input_tokens: int
    state: BudgetState
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_window": self.context_window,
            "system_prompt_tokens": self.system_prompt_tokens,
            "tool_schema_tokens": self.tool_schema_tokens,
            "message_tokens": self.message_tokens,
            "packed_context_tokens": self.packed_context_tokens,
            "tool_result_tokens": self.tool_result_tokens,
            "reserved_output_tokens": self.reserved_output_tokens,
            "safety_margin_tokens": self.safety_margin_tokens,
            "projected_total_tokens": self.projected_total_tokens,
            "available_input_tokens": self.available_input_tokens,
            "state": self.state.value,
            "warnings": list(self.warnings),
        }

    @property
    def usage_ratio(self) -> float:
        """Fraction of context_window currently consumed."""
        if self.context_window <= 0:
            return 1.0
        return self.projected_total_tokens / self.context_window


def _infer_state(ratio: float, thresholds: BudgetThresholds) -> BudgetState:
    """Map a usage ratio to a BudgetState."""
    if ratio >= thresholds.hard_stop_ratio:
        return BudgetState.HARD_STOP
    if ratio >= thresholds.split_ratio:
        return BudgetState.SPLIT
    if ratio >= thresholds.preserve_ratio:
        return BudgetState.PRESERVE
    if ratio >= thresholds.warning_ratio:
        return BudgetState.WARNING
    return BudgetState.OK


def _collect_warnings(report: BudgetReport) -> tuple[str, ...]:
    """Build human-readable warnings from a report."""
    warnings: list[str] = []
    if report.available_input_tokens < 0:
        warnings.append(
            f"Projected total ({report.projected_total_tokens}) exceeds context window "
            f"({report.context_window})"
        )
    elif report.available_input_tokens == 0:
        warnings.append("No input token budget remaining")
    elif report.state == BudgetState.HARD_STOP:
        warnings.append(
            f"Usage ratio {report.usage_ratio:.2%} exceeds hard_stop threshold"
        )
    elif report.state == BudgetState.SPLIT:
        warnings.append(
            f"Usage ratio {report.usage_ratio:.2%} exceeds split threshold; "
            "consider breaking the task into smaller steps"
        )
    elif report.state == BudgetState.PRESERVE:
        warnings.append(
            f"Usage ratio {report.usage_ratio:.2%} exceeds preserve threshold; "
            "externalize state before continuing"
        )
    elif report.state == BudgetState.WARNING:
        warnings.append(
            f"Usage ratio {report.usage_ratio:.2%} exceeds warning threshold; "
            "light cleanup recommended"
        )
    return tuple(warnings)


# ---------------------------------------------------------------------------
# Public calculator
# ---------------------------------------------------------------------------

class ContextBudgetCalculator:
    """Calculate a BudgetReport from runtime profile and current token counts.

    All thresholds are ratio-based so the calculator works for any context_window.
    """

    def __init__(
        self,
        context_window: int,
        reserved_output_tokens: int,
        safety_margin_tokens: int,
        thresholds: BudgetThresholds | None = None,
    ):
        if context_window <= 0:
            raise ValueError("context_window must be positive")
        self.context_window = context_window
        self.reserved_output_tokens = reserved_output_tokens
        self.safety_margin_tokens = safety_margin_tokens
        self.thresholds = thresholds or BudgetThresholds()

    @classmethod
    def from_runtime_profile(
        cls,
        profile: Any,
        thresholds: BudgetThresholds | None = None,
    ) -> ContextBudgetCalculator:
        """Build a calculator from a RuntimeProfile-like object.

        *profile* must have ``context_window``, ``max_output_tokens``,
        and ``safety_margin_tokens`` attributes.
        """
        return cls(
            context_window=int(getattr(profile, "context_window", 32768)),
            reserved_output_tokens=int(getattr(profile, "max_output_tokens", 2048)),
            safety_margin_tokens=int(getattr(profile, "safety_margin_tokens", 1024)),
            thresholds=thresholds,
        )

    def calculate(
        self,
        *,
        system_prompt_tokens: int = 0,
        tool_schema_tokens: int = 0,
        message_tokens: int = 0,
        packed_context_tokens: int = 0,
        tool_result_tokens: int = 0,
    ) -> BudgetReport:
        """Compute a BudgetReport from the current token counts.

        No LLM is called; all inputs are plain integers.
        """
        projected_total = (
            system_prompt_tokens
            + tool_schema_tokens
            + message_tokens
            + packed_context_tokens
            + tool_result_tokens
            + self.reserved_output_tokens
            + self.safety_margin_tokens
        )
        available_input = max(0, self.context_window - projected_total)
        ratio = projected_total / self.context_window if self.context_window > 0 else 1.0
        state = _infer_state(ratio, self.thresholds)

        report = BudgetReport(
            context_window=self.context_window,
            system_prompt_tokens=system_prompt_tokens,
            tool_schema_tokens=tool_schema_tokens,
            message_tokens=message_tokens,
            packed_context_tokens=packed_context_tokens,
            tool_result_tokens=tool_result_tokens,
            reserved_output_tokens=self.reserved_output_tokens,
            safety_margin_tokens=self.safety_margin_tokens,
            projected_total_tokens=projected_total,
            available_input_tokens=available_input,
            state=state,
            warnings=(),
        )
        # Attach warnings after construction so we can read the state
        object.__setattr__(report, "warnings", _collect_warnings(report))
        return report

    def estimate_message_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Rough token estimate for a list of messages (char-count heuristic).

        No tokenizer or LLM is used.
        """
        total_chars = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, str):
                        total_chars += len(block)
                    elif isinstance(block, dict):
                        for v in block.values():
                            if isinstance(v, str):
                                total_chars += len(v)
                            elif isinstance(v, list):
                                for item in v:
                                    if isinstance(item, str):
                                        total_chars += len(item)
        return max(1, int(total_chars / 1.8))


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def format_budget_report(report: BudgetReport) -> str:
    """Compact single-line summary of a budget report."""
    return (
        f"[{report.state.upper()}] "
        f"used={report.projected_total_tokens}/{report.context_window} "
        f"({report.usage_ratio:.1%}) "
        f"avail_input={report.available_input_tokens} "
        f"reserved_out={report.reserved_output_tokens}"
    )


def format_budget_report_verbose(report: BudgetReport) -> str:
    """Multi-line detailed budget report."""
    lines = [
        f"Budget State: {report.state.upper()}",
        f"  Context window:        {report.context_window:,}",
        f"  System prompt:         {report.system_prompt_tokens:,}",
        f"  Tool schema:           {report.tool_schema_tokens:,}",
        f"  Messages:              {report.message_tokens:,}",
        f"  Packed context:        {report.packed_context_tokens:,}",
        f"  Tool results:          {report.tool_result_tokens:,}",
        f"  Reserved output:       {report.reserved_output_tokens:,}",
        f"  Safety margin:         {report.safety_margin_tokens:,}",
        "  " + "-" * 30,
        f"  Projected total:       {report.projected_total_tokens:,}",
        f"  Available input:       {report.available_input_tokens:,}",
        f"  Usage ratio:           {report.usage_ratio:.1%}",
    ]
    if report.warnings:
        lines.append("  Warnings:")
        for w in report.warnings:
            lines.append(f"    - {w}")
    return "\n".join(lines)
