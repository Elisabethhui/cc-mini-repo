import pytest

from core.context_budget import (
    BudgetReport,
    BudgetState,
    BudgetThresholds,
    ContextBudgetCalculator,
    format_budget_report,
    format_budget_report_verbose,
)
from core.runtime_profile import build_runtime_profile


def test_ok_state_at_low_usage():
    calc = ContextBudgetCalculator(
        context_window=10_000,
        reserved_output_tokens=1000,
        safety_margin_tokens=500,
    )
    report = calc.calculate(
        system_prompt_tokens=100,
        message_tokens=1000,
    )
    assert report.state == BudgetState.OK
    assert report.usage_ratio < 0.65
    assert report.available_input_tokens > 0


def test_warning_state_near_threshold():
    calc = ContextBudgetCalculator(
        context_window=10_000,
        reserved_output_tokens=1000,
        safety_margin_tokens=500,
    )
    # warning_ratio = 0.65  →  need ~6500 projected total
    report = calc.calculate(message_tokens=5000)
    assert report.state == BudgetState.WARNING
    assert report.usage_ratio >= 0.65


def test_preserve_state():
    calc = ContextBudgetCalculator(
        context_window=10_000,
        reserved_output_tokens=1000,
        safety_margin_tokens=500,
    )
    # preserve_ratio = 0.75  →  need ~7500 projected total
    report = calc.calculate(message_tokens=6000)
    assert report.state == BudgetState.PRESERVE
    assert report.usage_ratio >= 0.75


def test_split_state():
    calc = ContextBudgetCalculator(
        context_window=10_000,
        reserved_output_tokens=1000,
        safety_margin_tokens=500,
    )
    # split_ratio = 0.85  →  need ~8500 projected total
    report = calc.calculate(message_tokens=7000)
    assert report.state == BudgetState.SPLIT
    assert report.usage_ratio >= 0.85


def test_hard_stop_state():
    calc = ContextBudgetCalculator(
        context_window=10_000,
        reserved_output_tokens=1000,
        safety_margin_tokens=500,
    )
    # hard_stop_ratio = 0.92  →  need ~9200 projected total
    report = calc.calculate(message_tokens=8000)
    assert report.state == BudgetState.HARD_STOP
    assert report.usage_ratio >= 0.92


def test_custom_thresholds():
    calc = ContextBudgetCalculator(
        context_window=10_000,
        reserved_output_tokens=1000,
        safety_margin_tokens=500,
        thresholds=BudgetThresholds(
            warning_ratio=0.5,
            preserve_ratio=0.6,
            split_ratio=0.7,
            hard_stop_ratio=0.8,
        ),
    )
    # projected_total = 4500 + 1000 + 500 = 6000 → ratio = 0.60 → preserve
    report = calc.calculate(message_tokens=4500)
    assert report.state == BudgetState.PRESERVE
    assert report.usage_ratio >= 0.6


def test_available_input_tokens_never_negative():
    calc = ContextBudgetCalculator(
        context_window=1000,
        reserved_output_tokens=500,
        safety_margin_tokens=500,
    )
    report = calc.calculate(message_tokens=1000)
    assert report.available_input_tokens == 0
    assert report.state == BudgetState.HARD_STOP


def test_negative_context_window_raises():
    with pytest.raises(ValueError, match="context_window must be positive"):
        ContextBudgetCalculator(context_window=0, reserved_output_tokens=100, safety_margin_tokens=50)


def test_from_runtime_profile_cloud():
    profile = build_runtime_profile(
        provider="anthropic",
        model="claude-sonnet-4-6",
    )
    calc = ContextBudgetCalculator.from_runtime_profile(profile)
    assert calc.context_window == 200_000
    assert calc.reserved_output_tokens == 32_000
    assert calc.safety_margin_tokens > 0


def test_from_runtime_profile_local():
    profile = build_runtime_profile(
        provider="openai",
        model="mlx-community/Mistral-7B-Instruct",
        base_url="http://localhost:8080/v1",
    )
    calc = ContextBudgetCalculator.from_runtime_profile(profile)
    assert calc.context_window == 32_768
    assert calc.reserved_output_tokens == 2048


def test_format_budget_report_compact():
    calc = ContextBudgetCalculator(
        context_window=10_000,
        reserved_output_tokens=1000,
        safety_margin_tokens=500,
    )
    report = calc.calculate(message_tokens=5000)
    text = format_budget_report(report)
    assert "WARNING" in text
    assert "used=" in text
    assert "avail_input=" in text


def test_format_budget_report_verbose():
    calc = ContextBudgetCalculator(
        context_window=10_000,
        reserved_output_tokens=1000,
        safety_margin_tokens=500,
    )
    report = calc.calculate(message_tokens=5000)
    text = format_budget_report_verbose(report)
    assert "Budget State: WARNING" in text
    assert "Context window:" in text
    assert "Warnings:" in text


def test_estimate_message_tokens():
    calc = ContextBudgetCalculator(
        context_window=10_000,
        reserved_output_tokens=1000,
        safety_margin_tokens=500,
    )
    messages = [
        {"role": "user", "content": "a" * 400},
        {"role": "assistant", "content": [{"type": "text", "text": "b" * 400}]},
    ]
    estimate = calc.estimate_message_tokens(messages)
    assert estimate >= 200


def test_full_budget_report_fields():
    calc = ContextBudgetCalculator(
        context_window=32_768,
        reserved_output_tokens=2048,
        safety_margin_tokens=1024,
    )
    report = calc.calculate(
        system_prompt_tokens=500,
        tool_schema_tokens=200,
        message_tokens=4000,
        packed_context_tokens=1000,
        tool_result_tokens=800,
    )
    assert report.context_window == 32_768
    assert report.system_prompt_tokens == 500
    assert report.tool_schema_tokens == 200
    assert report.message_tokens == 4000
    assert report.packed_context_tokens == 1000
    assert report.tool_result_tokens == 800
    assert report.reserved_output_tokens == 2048
    assert report.safety_margin_tokens == 1024
    expected_total = 500 + 200 + 4000 + 1000 + 800 + 2048 + 1024
    assert report.projected_total_tokens == expected_total
    assert report.available_input_tokens == 32_768 - expected_total
    assert report.state == BudgetState.OK  # 9572/32768 ≈ 29%
    assert len(report.warnings) == 0
