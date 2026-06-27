from argparse import Namespace
from pathlib import Path

import pytest

from core.config import (
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
    default_max_tokens_for_model,
    load_app_config,
    resolve_run_mode,
    resolve_model,
)


def _args(**overrides):
    values = {
        "prompt": None,
        "print": False,
        "auto_approve": False,
        "config": None,
        "provider": None,
        "api_key": None,
        "base_url": None,
        "model": None,
        "max_tokens": None,
        "effort": None,
        "buddy_model": None,
        "memory_dir": None,
        "no_auto_dream": False,
        "dream_interval": None,
        "dream_min_sessions": None,
    }
    values.update(overrides)
    return Namespace(**values)


def test_resolve_model_keeps_full_model_name():
    assert resolve_model("claude-sonnet-4-20250514") == "claude-sonnet-4-20250514"


def test_default_max_tokens_follow_model_family():
    # Matches official getModelMaxOutputTokens() in context.ts
    assert default_max_tokens_for_model("claude-sonnet-4") == 32000
    assert default_max_tokens_for_model("claude-opus-4-6") == 64000
    assert default_max_tokens_for_model("claude-opus-4-1-20250805") == 32000
    assert default_max_tokens_for_model("claude-3-5-haiku-20241022") == 8192


def test_load_app_config_reads_anthropic_section(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("CC_MINI_MODEL", raising=False)
    monkeypatch.delenv("CC_MINI_MAX_TOKENS", raising=False)

    config_path = tmp_path / "cc-mini.toml"
    config_path.write_text(
        '[anthropic]\n'
        'api_key = "config-key"\n'
        'base_url = "https://example.test"\n'
        'model = "claude-3.7-sonnet"\n',
        encoding="utf-8",
    )

    config = load_app_config(_args(config=str(config_path)))

    assert config.provider == DEFAULT_PROVIDER
    assert config.api_key == "config-key"
    assert config.base_url == "https://example.test"
    assert config.model == "claude-3-7-sonnet"
    assert config.max_tokens == 32000  # 3-7-sonnet: 32k per official context.ts


def test_load_app_config_cli_overrides_env_and_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_path = tmp_path / "cc-mini.toml"
    config_path.write_text(
        'api_key = "file-key"\n'
        'base_url = "https://file.test"\n'
        'model = "claude-3-5-haiku"\n'
        'max_tokens = 2048\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://env.test")
    monkeypatch.setenv("CC_MINI_MODEL", "claude-opus-4")
    monkeypatch.setenv("CC_MINI_MAX_TOKENS", "1234")

    config = load_app_config(
        _args(
            config=str(config_path),
            api_key="cli-key",
            base_url="https://cli.test",
            model="claude-sonnet-4",
            max_tokens=999,
        )
    )

    assert config.api_key == "cli-key"
    assert config.base_url == "https://cli.test"
    assert config.model == "claude-sonnet-4"
    assert config.max_tokens == 999


def test_load_app_config_uses_defaults_when_nothing_is_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("CC_MINI_MODEL", raising=False)
    monkeypatch.delenv("CC_MINI_MAX_TOKENS", raising=False)

    config = load_app_config(_args())

    assert config.provider == DEFAULT_PROVIDER
    assert config.api_key is None
    assert config.base_url is None
    assert config.model == DEFAULT_MODEL
    assert config.max_tokens == default_max_tokens_for_model(DEFAULT_MODEL)


def test_load_app_config_rejects_invalid_max_tokens(tmp_path: Path):
    config_path = tmp_path / "cc-mini.toml"
    config_path.write_text('max_tokens = "abc"\n', encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid max_tokens"):
        load_app_config(_args(config=str(config_path)))


def test_load_app_config_reads_openai_section(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CC_MINI_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    config_path = tmp_path / "cc-mini.toml"
    config_path.write_text(
        'provider = "openai"\n'
        '[openai]\n'
        'api_key = "openai-key"\n'
        'base_url = "https://openai.test"\n'
        'model = "gpt-4.1-mini"\n'
        'max_tokens = 4096\n'
        'effort = "low"\n'
        'buddy_model = "gpt-4.1-nano"\n',
        encoding="utf-8",
    )

    config = load_app_config(_args(config=str(config_path)))

    assert config.provider == "openai"
    assert config.api_key == "openai-key"
    assert config.base_url == "https://openai.test"
    assert config.model == "gpt-4.1-mini"
    assert config.max_tokens == 4096
    assert config.effort == "low"
    assert config.buddy_model == "gpt-4.1-nano"


def test_openai_env_wins_when_provider_is_openai(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CC_MINI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-env-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openai.env")
    monkeypatch.setenv("CC_MINI_MODEL", "gpt-4.1")
    monkeypatch.setenv("CC_MINI_BUDDY_MODEL", "gpt-4.1-mini")

    config = load_app_config(_args())

    assert config.provider == "openai"
    assert config.api_key == "openai-env-key"
    assert config.base_url == "https://openai.env"
    assert config.model == "gpt-4.1"
    assert config.buddy_model == "gpt-4.1-mini"


def test_resolve_run_mode_prefers_cli_choice_over_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CC_MINI_MODE", "standard")

    assert resolve_run_mode("wiki_strict") == "wiki_strict"


def test_default_max_tokens_for_local_model():
    # Local models should lock to 32K
    assert default_max_tokens_for_model("mymodel", provider="openai", base_url="http://localhost:1234") == 32000
    assert default_max_tokens_for_model("mlx-community/Mistral-7B", provider="openai") == 32000
    # Cloud OpenAI should not be affected
    assert default_max_tokens_for_model("gpt-4.1", provider="openai", base_url="https://api.openai.com/v1") == 16384


def test_load_app_config_detects_local_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    config_path = tmp_path / "cc-mini.toml"
    config_path.write_text(
        'provider = "openai"\n'
        '[openai]\n'
        'base_url = "http://127.0.0.1:1234/v1"\n'
        'model = "mlx-community/Qwen2.5-7B-Instruct"\n',
        encoding="utf-8",
    )

    config = load_app_config(_args(config=str(config_path)))

    assert config.provider == "openai"
    assert config.base_url == "http://127.0.0.1:1234/v1"
    assert config.local_profile is not None
    assert config.local_profile.kind == "mlx"
    assert config.local_profile.context_window == 32768
    assert config.max_tokens == 32000

    # RuntimeProfile should also be built
    assert config.runtime_profile is not None
    assert config.runtime_profile.context_window == 32768
    # Sanity check: output is capped so output + safety <= context_window
    assert config.runtime_profile.max_output_tokens <= 32000
    assert config.runtime_profile.max_output_tokens + config.runtime_profile.safety_margin_tokens <= 32768
    assert config.runtime_profile.runtime_kind == "local_openai_compatible"
    assert config.runtime_profile.available_input_tokens >= 0


def test_load_app_config_builds_runtime_profile_for_cloud(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("CC_MINI_MODEL", raising=False)
    monkeypatch.delenv("CC_MINI_MAX_TOKENS", raising=False)

    config_path = tmp_path / "cc-mini.toml"
    config_path.write_text(
        '[anthropic]\n'
        'model = "claude-sonnet-4-6"\n',
        encoding="utf-8",
    )

    config = load_app_config(_args(config=str(config_path)))

    assert config.runtime_profile is not None
    assert config.runtime_profile.provider == "anthropic"
    assert config.runtime_profile.model == "claude-sonnet-4-6"
    assert config.runtime_profile.context_window == 200_000
    assert config.runtime_profile.max_output_tokens == 32_000
    assert config.runtime_profile.runtime_kind == "anthropic"
    assert config.runtime_profile.available_input_tokens > 0


def test_load_app_config_reads_context_env_vars(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CC_MINI_CONTEXT_WINDOW", "64000")
    monkeypatch.setenv("CC_MINI_MAX_OUTPUT_TOKENS", "4096")
    monkeypatch.setenv("CC_MINI_SAFETY_MARGIN_TOKENS", "1024")
    monkeypatch.setenv("CC_MINI_AUTO_COMPACT", "true")
    monkeypatch.setenv("CC_MINI_AUTO_APPROVE", "1")

    config = load_app_config(_args())

    assert config.context_window == 64000
    assert config.max_output_tokens == 4096
    assert config.safety_margin_tokens == 1024
    assert config.auto_compact is True
    assert config.auto_approve is True


def test_load_app_config_reads_context_toml_section(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CC_MINI_CONTEXT_WINDOW", raising=False)
    monkeypatch.delenv("CC_MINI_MAX_OUTPUT_TOKENS", raising=False)
    monkeypatch.delenv("CC_MINI_SAFETY_MARGIN_TOKENS", raising=False)
    monkeypatch.delenv("CC_MINI_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("CC_MINI_AUTO_APPROVE", raising=False)
    monkeypatch.delenv("CC_MINI_MAX_TOKENS", raising=False)

    config_path = tmp_path / "cc-mini.toml"
    config_path.write_text(
        '[context]\n'
        'window = 48000\n'
        'max_output_tokens = 8192\n'
        'safety_margin_tokens = 2048\n'
        'auto_compact = true\n',
        encoding="utf-8",
    )

    config = load_app_config(_args(config=str(config_path)))

    assert config.context_window == 48000
    assert config.max_output_tokens == 8192
    assert config.safety_margin_tokens == 2048
    assert config.auto_compact is True


def test_load_app_config_max_output_tokens_env_overrides_max_tokens(monkeypatch: pytest.MonkeyPatch):
    """CC_MINI_MAX_OUTPUT_TOKENS takes priority over CC_MINI_MAX_TOKENS."""
    monkeypatch.setenv("CC_MINI_MAX_OUTPUT_TOKENS", "2048")
    monkeypatch.setenv("CC_MINI_MAX_TOKENS", "8192")

    config = load_app_config(_args())

    assert config.max_tokens == 2048
    assert config.max_output_tokens == 2048


def test_load_app_config_max_tokens_backward_compatible(monkeypatch: pytest.MonkeyPatch):
    """CC_MINI_MAX_TOKENS still works when CC_MINI_MAX_OUTPUT_TOKENS is absent."""
    monkeypatch.delenv("CC_MINI_MAX_OUTPUT_TOKENS", raising=False)
    monkeypatch.setenv("CC_MINI_MAX_TOKENS", "4096")

    config = load_app_config(_args())

    assert config.max_tokens == 4096


def test_load_app_config_auto_compact_false_values(monkeypatch: pytest.MonkeyPatch):
    for false_val in ("false", "0", "no", "FALSE", "No"):
        monkeypatch.setenv("CC_MINI_AUTO_COMPACT", false_val)
        config = load_app_config(_args())
        assert config.auto_compact is False, f"expected False for {false_val!r}"


def test_load_app_config_auto_approve_false_values(monkeypatch: pytest.MonkeyPatch):
    for false_val in ("false", "0", "no", "FALSE", "No"):
        monkeypatch.setenv("CC_MINI_AUTO_APPROVE", false_val)
        config = load_app_config(_args())
        assert config.auto_approve is False, f"expected False for {false_val!r}"
