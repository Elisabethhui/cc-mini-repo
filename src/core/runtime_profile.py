from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeProfile:
    """Complete runtime profile for a model endpoint.

    Separates the *total context window* from the *output token budget*.
    """

    provider: str
    model: str
    base_url: str | None
    context_window: int
    max_output_tokens: int
    safety_margin_tokens: int
    runtime_kind: str
    supports_streaming: bool
    supports_tool_calling: str  # "true", "false", "auto"

    @property
    def available_input_tokens(self) -> int:
        """Tokens left for input after reserving output + safety margin."""
        return max(0, self.context_window - self.max_output_tokens - self.safety_margin_tokens)


# ---------------------------------------------------------------------------
# Heuristic defaults
# ---------------------------------------------------------------------------

_DEFAULT_SAFETY_MARGIN_RATIO = 0.05  # 5% of context window
_MIN_SAFETY_MARGIN = 512

# Known cloud model context windows (prefix match)
_KNOWN_CONTEXT_WINDOWS: tuple[tuple[str, int], ...] = (
    # Anthropic
    ("claude-opus-4-6", 200_000),
    ("claude-opus-4-5", 200_000),
    ("claude-opus-4-1", 200_000),
    ("claude-opus-4", 200_000),
    ("claude-sonnet-4-6", 200_000),
    ("claude-sonnet-4-5", 200_000),
    ("claude-sonnet-4", 200_000),
    ("claude-haiku-4", 200_000),
    ("claude-3-7-sonnet", 200_000),
    ("claude-3-5-sonnet", 200_000),
    ("claude-3-5-haiku", 200_000),
    ("claude-3-haiku", 200_000),
    # OpenAI
    ("gpt-5", 128_000),
    ("gpt-4.1", 128_000),
    ("gpt-4o", 128_000),
    ("o1", 128_000),
    ("o3", 128_000),
    ("o4", 128_000),
)

# Default output token budgets for cloud models (prefix match)
_KNOWN_MAX_OUTPUT_TOKENS: tuple[tuple[str, int], ...] = (
    ("claude-opus-4-6", 64_000),
    ("claude-sonnet-4-6", 32_000),
    ("claude-opus-4-5", 32_000),
    ("claude-sonnet-4-5", 32_000),
    ("claude-sonnet-4", 32_000),
    ("claude-haiku-4", 32_000),
    ("claude-opus-4-1", 32_000),
    ("claude-opus-4", 32_000),
    ("claude-3-7-sonnet", 32_000),
    ("claude-3-5-sonnet", 8192),
    ("claude-3-5-haiku", 8192),
    ("claude-3-haiku", 4096),
    ("gpt-5", 8192),
    ("gpt-4.1", 16_384),
    ("gpt-4o", 16_384),
    ("o1", 32_768),
    ("o3", 32_768),
    ("o4", 32_768),
)

_LOCAL_KEYWORDS = ("mlx", "qwen", "local")
_LOCAL_PATTERNS = ("localhost", "127.0.0.1", "0.0.0.0", "::1", ".local")


def _is_local_endpoint(base_url: str | None, model: str) -> bool:
    """Return True if the endpoint looks like a local model."""
    if base_url:
        lowered = base_url.lower()
        if any(pat in lowered for pat in _LOCAL_PATTERNS):
            return True
    model_lower = model.lower()
    return any(kw in model_lower for kw in _LOCAL_KEYWORDS)


def _prefix_match(
    model: str,
    table: tuple[tuple[str, int], ...],
    default: int,
) -> int:
    """Find the first prefix match in *table* and return its value."""
    for prefix, value in table:
        if model.startswith(prefix):
            return value
    return default


def _default_context_window(
    provider: str,
    model: str,
    base_url: str | None,
) -> int:
    """Return a heuristic default context window.

    Local models default to 32K.  Cloud models use known tables.
    Unknown models get a safe fallback.
    """
    if _is_local_endpoint(base_url, model):
        return 32_768

    known = _prefix_match(model.lower(), _KNOWN_CONTEXT_WINDOWS, default=0)
    if known:
        return known

    # Safe fallback: do not assume 200K for unknown models
    if provider == "openai":
        return 32_768
    return 200_000


def _default_max_output_tokens(
    provider: str,
    model: str,
    base_url: str | None,
) -> int:
    """Return a heuristic default max output token budget.

    Local / openai-compatible models get a conservative 2048 default.
    Cloud models use known tables.
    """
    if _is_local_endpoint(base_url, model):
        return 2048

    known = _prefix_match(model.lower(), _KNOWN_MAX_OUTPUT_TOKENS, default=0)
    if known:
        return known

    if provider == "openai":
        return 8192
    return 32_000


def _default_safety_margin(context_window: int) -> int:
    return max(_MIN_SAFETY_MARGIN, int(context_window * _DEFAULT_SAFETY_MARGIN_RATIO))


def _infer_runtime_kind(
    provider: str,
    base_url: str | None,
    model: str,
) -> str:
    if _is_local_endpoint(base_url, model):
        return "local_openai_compatible"
    if provider == "openai":
        return "openai"
    return "anthropic"


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def build_runtime_profile(
    *,
    provider: str,
    model: str,
    base_url: str | None = None,
    context_window: int | None = None,
    max_output_tokens: int | None = None,
    safety_margin_tokens: int | None = None,
    supports_streaming: bool = True,
    supports_tool_calling: str = "auto",
) -> RuntimeProfile:
    """Build a RuntimeProfile from explicit values or heuristics.

    *context_window*, *max_output_tokens*, and *safety_margin_tokens* are all
    optional.  When omitted, safe defaults are inferred from provider/model/base_url.
    """
    resolved_context = context_window if context_window is not None else _default_context_window(
        provider, model, base_url
    )
    resolved_output = max_output_tokens if max_output_tokens is not None else _default_max_output_tokens(
        provider, model, base_url
    )
    resolved_safety = safety_margin_tokens if safety_margin_tokens is not None else _default_safety_margin(
        resolved_context
    )

    # Sanity check: output + safety must not exceed total context window
    max_allowed_output = max(1, resolved_context - resolved_safety)
    if resolved_output > max_allowed_output:
        resolved_output = max_allowed_output

    return RuntimeProfile(
        provider=provider,
        model=model,
        base_url=base_url,
        context_window=resolved_context,
        max_output_tokens=resolved_output,
        safety_margin_tokens=resolved_safety,
        runtime_kind=_infer_runtime_kind(provider, base_url, model),
        supports_streaming=supports_streaming,
        supports_tool_calling=supports_tool_calling,
    )


def format_runtime_profile(profile: RuntimeProfile) -> str:
    """Human-readable one-line summary."""
    return (
        f"{profile.provider}:{profile.model} "
        f"context={profile.context_window} "
        f"output={profile.max_output_tokens} "
        f"safety={profile.safety_margin_tokens} "
        f"kind={profile.runtime_kind}"
    )
