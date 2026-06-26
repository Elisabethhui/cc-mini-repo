from core.local_model import (
    LocalModelProfile,
    detect_local_model_profile,
    is_local_model,
    format_local_model_profile,
)


def test_detect_local_model_from_localhost_base_url():
    profile = detect_local_model_profile("http://localhost:1234/v1", "gpt-4")
    assert profile is not None
    assert profile.kind == "openai-compatible"
    assert profile.base_url == "http://localhost:1234/v1"
    assert profile.context_window == 32768
    assert profile.recommended_max_output_tokens == 32000
    assert profile.supports_streaming is True


def test_detect_local_model_from_127_0_0_1():
    profile = detect_local_model_profile("http://127.0.0.1:8080", "some-model")
    assert profile is not None
    assert profile.kind == "openai-compatible"


def test_detect_mlx_from_model_name():
    profile = detect_local_model_profile(None, "mlx-community/Mistral-7B-Instruct-v0.2-MLX")
    assert profile is not None
    assert profile.kind == "mlx"
    assert profile.base_url is None


def test_detect_local_model_from_0_0_0_0():
    profile = detect_local_model_profile("http://0.0.0.0:5000", "mymodel")
    assert profile is not None


def test_cloud_openai_returns_none():
    profile = detect_local_model_profile("https://api.openai.com/v1", "gpt-4")
    assert profile is None


def test_no_base_url_no_model_returns_none():
    profile = detect_local_model_profile(None, None)
    assert profile is None


def test_is_local_model_predicate():
    assert is_local_model("http://localhost:8080", "mymodel") is True
    assert is_local_model("https://api.openai.com/v1", "gpt-4") is False
    assert is_local_model(None, None) is False


def test_format_local_model_profile():
    profile = LocalModelProfile(
        kind="mlx",
        base_url="http://localhost:1234",
        context_window=32768,
        recommended_max_output_tokens=32000,
        supports_streaming=True,
        supports_tool_calling="auto",
    )
    text = format_local_model_profile(profile)
    assert "Kind: mlx" in text
    assert "Base URL: http://localhost:1234" in text
    assert "32,768" in text
    assert "Streaming: yes" in text
    assert "Tool calling: auto" in text
