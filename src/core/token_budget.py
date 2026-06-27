from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class BudgetState(str, Enum):
    OK = "ok"
    WARNING = "warning"
    PRESERVE = "preserve"
    SPLIT = "split"
    HARD_STOP = "hard_stop"


@dataclass
class BudgetThresholds:
    """Ratio-based thresholds relative to context_window."""

    warning_ratio: float = 0.65
    preserve_ratio: float = 0.75
    split_ratio: float = 0.85
    hard_stop_ratio: float = 0.92


@dataclass
class BudgetDecision:
    state: BudgetState
    token_estimate: int
    projected_total_tokens: int = 0
    should_dehydrate: bool = False
    should_compact: bool = False
    should_checkpoint: bool = False
    should_stop: bool = False
    reason: str = ""


class TokenBudgetManager:
    def __init__(
        self,
        context_window: int = 32_768,
        max_output_tokens: int = 2_048,
        safety_margin_tokens: int = 1_024,
        thresholds: BudgetThresholds | None = None,
    ) -> None:
        self.context_window = context_window
        self.safety_margin_tokens = safety_margin_tokens
        # Sanity cap: output + safety must not exceed context_window
        max_allowed_output = max(1, context_window - safety_margin_tokens)
        self.max_output_tokens = min(max_output_tokens, max_allowed_output)
        self.thresholds = thresholds or BudgetThresholds()
        self._last_token_estimate = 0

    @property
    def last_token_estimate(self) -> int:
        return self._last_token_estimate

    def estimate_from_messages(self, messages: list[dict[str, Any]]) -> int:
        total_chars = 0
        for msg in messages:
            total_chars += self._count_message_chars(msg)
        # 中文和代码符号密度高，建议改为 // 1.5 或 // 2
        estimate = max(1, int(total_chars / 1.8))
        self._last_token_estimate = estimate
        return estimate

    def update_from_usage(self, usage: Any | None, fallback_messages: list[dict[str, Any]]) -> int:
        """
        优先用 provider usage；拿不到时回退到 estimate。
        """
        if usage is None:
            return self.estimate_from_messages(fallback_messages)

        # Anthropic / OpenAI 风格尽量兼容
        for attr in ("input_tokens", "prompt_tokens", "total_tokens"):
            if hasattr(usage, attr):
                val = getattr(usage, attr)
                if isinstance(val, int) and val > 0:
                    self._last_token_estimate = val
                    return val

        if isinstance(usage, dict):
            for key in ("input_tokens", "prompt_tokens", "total_tokens"):
                val = usage.get(key)
                if isinstance(val, int) and val > 0:
                    self._last_token_estimate = val
                    return val

        return self.estimate_from_messages(fallback_messages)

    def decide(self, message_tokens: int) -> BudgetDecision:
        """Compute budget decision from message tokens.

        projected_total = message_tokens + reserved_output + safety_margin
        """
        projected = message_tokens + self.max_output_tokens + self.safety_margin_tokens
        ratio = projected / self.context_window if self.context_window > 0 else 1.0
        self._last_token_estimate = projected

        t = self.thresholds

        if ratio >= t.hard_stop_ratio:
            return BudgetDecision(
                state=BudgetState.HARD_STOP,
                token_estimate=projected,
                projected_total_tokens=projected,
                should_stop=True,
                should_checkpoint=True,
                reason=f"projected_total={projected} exceeds hard_stop_ratio ({t.hard_stop_ratio:.0%})",
            )

        if ratio >= t.split_ratio:
            return BudgetDecision(
                state=BudgetState.SPLIT,
                token_estimate=projected,
                projected_total_tokens=projected,
                should_checkpoint=True,
                reason=f"projected_total={projected} exceeds split_ratio ({t.split_ratio:.0%})",
            )

        if ratio >= t.preserve_ratio:
            return BudgetDecision(
                state=BudgetState.PRESERVE,
                token_estimate=projected,
                projected_total_tokens=projected,
                should_compact=True,
                should_dehydrate=True,
                reason=f"projected_total={projected} exceeds preserve_ratio ({t.preserve_ratio:.0%})",
            )

        if ratio >= t.warning_ratio:
            return BudgetDecision(
                state=BudgetState.WARNING,
                token_estimate=projected,
                projected_total_tokens=projected,
                should_dehydrate=True,
                reason=f"projected_total={projected} exceeds warning_ratio ({t.warning_ratio:.0%})",
            )

        return BudgetDecision(
            state=BudgetState.OK,
            token_estimate=projected,
            projected_total_tokens=projected,
            reason="projected_total within safe range",
        )

    def _count_message_chars(self, msg: dict[str, Any]) -> int:
        role = str(msg.get("role", ""))
        content = msg.get("content", "")
        n = len(role)

        if isinstance(content, str):
            return n + len(content)

        if isinstance(content, list):
            for block in content:
                if isinstance(block, str):
                    n += len(block)
                elif isinstance(block, dict):
                    for v in block.values():
                        if isinstance(v, str):
                            n += len(v)
                        elif isinstance(v, list):
                            for item in v:
                                if isinstance(item, str):
                                    n += len(item)
        return n
