from core.runtime_profile import (
    RuntimeProfile,
    build_runtime_profile,
    format_runtime_profile,
)


def test_local_mlx_defaults_to_32k_context():
    profile = build_runtime_profile(
        provider="openai",
        model="mlx-community/Mistral-7B-Instruct-v0.2-MLX",
    )
    assert profile.context_window == 32768
    assert profile.runtime_kind == "local_openai_compatible"
    assert profile.max_output_tokens == 2048
    assert profile.safety_margin_tokens >= 512


def test_local_qwen_defaults_to_32k_context():
    profile = build_runtime_profile(
        provider="openai",
        model="Qwen3.5-9B-MLX-4bit",
        base_url="http://localhost:8000/v1",
    )
    assert profile.context_window == 32768
    assert profile.runtime_kind == "local_openai_compatible"
    assert profile.max_output_tokens == 2048


def test_local_model_context_window_can_be_overridden():
    profile = build_runtime_profile(
        provider="openai",
        model="mlx-community/Mistral-7B",
        context_window=8192,
    )
    assert profile.context_window == 8192
    assert profile.max_output_tokens == 2048  # still conservative default


def test_local_model_max_output_can_be_overridden():
    profile = build_runtime_profile(
        provider="openai",
        model="mlx-community/Mistral-7B",
        max_output_tokens=4096,
    )
    assert profile.max_output_tokens == 4096


def test_local_model_safety_margin_can_be_overridden():
    profile = build_runtime_profile(
        provider="openai",
        model="mlx-community/Mistral-7B",
        safety_margin_tokens=1024,
    )
    assert profile.safety_margin_tokens == 1024


def test_cloud_openai_model_uses_known_context():
    profile = build_runtime_profile(
        provider="openai",
        model="gpt-4.1-mini",
    )
    assert profile.context_window == 128_000
    assert profile.runtime_kind == "openai"
    assert profile.max_output_tokens == 16_384


def test_cloud_anthropic_model_uses_known_context():
    profile = build_runtime_profile(
        provider="anthropic",
        model="claude-sonnet-4-6",
    )
    assert profile.context_window == 200_000
    assert profile.runtime_kind == "anthropic"
    assert profile.max_output_tokens == 32_000


def test_unknown_openai_model_gets_safe_fallback():
    profile = build_runtime_profile(
        provider="openai",
        model="some-unknown-model",
    )
    assert profile.context_window == 32_768  # safe fallback, not 200K
    assert profile.max_output_tokens == 8192


def test_unknown_anthropic_model_gets_safe_fallback():
    profile = build_runtime_profile(
        provider="anthropic",
        model="some-future-claude",
    )
    assert profile.context_window == 200_000  # anthropic fallback
    assert profile.max_output_tokens == 32_000


def test_available_input_tokens_computed_correctly():
    profile = build_runtime_profile(
        provider="openai",
        model="mlx-community/Mistral-7B",
        context_window=32768,
        max_output_tokens=2048,
        safety_margin_tokens=1024,
    )
    assert profile.available_input_tokens == 32768 - 2048 - 1024


def test_available_input_tokens_never_negative():
    profile = build_runtime_profile(
        provider="openai",
        model="tiny-model",
        context_window=1000,
        max_output_tokens=2000,
        safety_margin_tokens=500,
    )
    assert profile.available_input_tokens == 0


def test_supports_streaming_and_tool_calling_defaults():
    profile = build_runtime_profile(
        provider="openai",
        model="gpt-4.1",
    )
    assert profile.supports_streaming is True
    assert profile.supports_tool_calling == "auto"


def test_format_runtime_profile():
    profile = build_runtime_profile(
        provider="openai",
        model="gpt-4.1",
    )
    text = format_runtime_profile(profile)
    assert "openai:gpt-4.1" in text
    assert "context=128000" in text
    assert "output=16384" in text
    assert "kind=openai" in text
