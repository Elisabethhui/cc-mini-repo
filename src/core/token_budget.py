from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable


class BudgetState(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    COMPACT = "compact"
    CHECKPOINT = "checkpoint"
    HARD_STOP = "hard_stop"


@dataclass
class BudgetThresholds:
    # 针对 32K 模型的保守设置，预留 8K 用于模型输出和安全缓冲
    soft_limit: int = 16_000      # 触发脱水
    compact_limit: int = 20_000   # 触发摘要压缩
    checkpoint_limit: int = 24_000 # 触发快照截断
    hard_stop_limit: int = 26_000 # 绝对死线
    max_context: int = 32_768

@dataclass
class BudgetDecision:
    state: BudgetState
    token_estimate: int
    should_dehydrate: bool = False
    should_compact: bool = False
    should_checkpoint: bool = False
    should_stop: bool = False
    reason: str = ""


class TokenBudgetManager:
    def __init__(self, thresholds: BudgetThresholds | None = None) -> None:
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

    def decide(self, token_count: int) -> BudgetDecision:
        t = self.thresholds

        if token_count >= t.hard_stop_limit:
            return BudgetDecision(
                state=BudgetState.HARD_STOP,
                token_estimate=token_count,
                should_dehydrate=True,
                should_compact=True,
                should_checkpoint=True,
                should_stop=True,
                reason="token_count exceeds hard stop limit",
            )

        if token_count >= t.checkpoint_limit:
            return BudgetDecision(
                state=BudgetState.CHECKPOINT,
                token_estimate=token_count,
                should_dehydrate=True,
                should_compact=True,
                should_checkpoint=True,
                should_stop=True,
                reason="token_count exceeds checkpoint limit",
            )

        if token_count >= t.compact_limit:
            return BudgetDecision(
                state=BudgetState.COMPACT,
                token_estimate=token_count,
                should_dehydrate=True,
                should_compact=True,
                reason="token_count exceeds compact limit",
            )

        if token_count >= t.soft_limit:
            return BudgetDecision(
                state=BudgetState.WARNING,
                token_estimate=token_count,
                should_dehydrate=True,
                reason="token_count exceeds soft limit",
            )

        return BudgetDecision(
            state=BudgetState.NORMAL,
            token_estimate=token_count,
            reason="token_count within safe range",
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