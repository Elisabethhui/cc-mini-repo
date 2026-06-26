from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LocalModelProfile:
    """Profile for a locally-hosted OpenAI-compatible model."""

    kind: str  # "mlx", "openai-compatible", "unknown"
    base_url: str | None
    context_window: int = 32768
    recommended_max_output_tokens: int = 32000
    supports_streaming: bool = True
    supports_tool_calling: str = "auto"  # "true", "false", "auto"


def _is_local_url(base_url: str | None) -> bool:
    """Return True if base_url points to a local endpoint."""
    if not base_url:
        return False
    lowered = base_url.lower()
    local_patterns = (
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        ".local",
    )
    return any(pat in lowered for pat in local_patterns)


def detect_local_model_profile(
    base_url: str | None,
    model: str | None,
) -> LocalModelProfile | None:
    """Detect whether the current config targets a local model.

    Returns *None* for cloud OpenAI/Anthropic endpoints.
    """
    if not base_url and not model:
        return None

    is_local = _is_local_url(base_url)
    model_lower = (model or "").lower()

    # Heuristic: model name hints
    if "mlx" in model_lower:
        is_local = True

    if not is_local:
        return None

    kind = "unknown"
    if "mlx" in model_lower:
        kind = "mlx"
    elif base_url:
        kind = "openai-compatible"

    # Default 32K context window for local small-context models
    context_window = 32768
    recommended_max_output_tokens = 32000

    # MLX through lmstudio or similar typically advertises 32K context
    if kind == "mlx":
        context_window = 32768
        recommended_max_output_tokens = 32000

    supports_streaming = True
    supports_tool_calling = "auto"

    return LocalModelProfile(
        kind=kind,
        base_url=base_url,
        context_window=context_window,
        recommended_max_output_tokens=recommended_max_output_tokens,
        supports_streaming=supports_streaming,
        supports_tool_calling=supports_tool_calling,
    )


def is_local_model(base_url: str | None, model: str | None) -> bool:
    """Quick predicate: does the config look like a local model setup?"""
    return detect_local_model_profile(base_url, model) is not None


def format_local_model_profile(profile: LocalModelProfile) -> str:
    """Human-readable summary of a local model profile."""
    lines = [
        f"Kind: {profile.kind}",
        f"Base URL: {profile.base_url or '(default)'}",
        f"Context window: {profile.context_window:,}",
        f"Recommended max output tokens: {profile.recommended_max_output_tokens:,}",
        f"Streaming: {'yes' if profile.supports_streaming else 'no'}",
        f"Tool calling: {profile.supports_tool_calling}",
    ]
    return "\n".join(lines)
