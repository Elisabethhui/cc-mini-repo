from core.token_budget import TokenBudgetManager, BudgetState, BudgetThresholds


def test_budget_manager_decides_states():
    mgr = TokenBudgetManager(
        context_window=100_000,
        max_output_tokens=2_000,
        safety_margin_tokens=1_000,
        thresholds=BudgetThresholds(
            warning_ratio=0.65,
            preserve_ratio=0.75,
            split_ratio=0.85,
            hard_stop_ratio=0.92,
        ),
    )
    # projected = message_tokens + 2000 + 1000 = message_tokens + 3000
    # warning at 65% => projected >= 65_000 => msg >= 62_000
    # preserve at 75% => projected >= 75_000 => msg >= 72_000
    # split at 85% => projected >= 85_000 => msg >= 82_000
    # hard_stop at 92% => projected >= 92_000 => msg >= 89_000
    assert mgr.decide(10_000).state == BudgetState.OK          # projected=13K
    assert mgr.decide(62_000).state == BudgetState.WARNING      # projected=65K
    assert mgr.decide(72_000).state == BudgetState.PRESERVE     # projected=75K
    assert mgr.decide(82_000).state == BudgetState.SPLIT        # projected=85K
    assert mgr.decide(89_000).state == BudgetState.HARD_STOP    # projected=92K


def test_estimate_from_messages_roughly_counts_content():
    mgr = TokenBudgetManager()
    messages = [
        {"role": "user", "content": "a" * 400},
        {"role": "assistant", "content": [{"type": "text", "text": "b" * 400}]},
    ]
    estimate = mgr.estimate_from_messages(messages)
    assert estimate >= 200


def test_projected_total_includes_output_and_safety():
    mgr = TokenBudgetManager(
        context_window=32_768,
        max_output_tokens=2_048,
        safety_margin_tokens=1_024,
    )
    decision = mgr.decide(10_000)
    assert decision.projected_total_tokens == 13_072  # 10_000 + 2_048 + 1_024


def test_hard_stop_prevents_llm_call():
    mgr = TokenBudgetManager(
        context_window=10_000,
        max_output_tokens=2_000,
        safety_margin_tokens=1_000,
    )
    decision = mgr.decide(10_000)  # projected = 13_000 > context_window
    assert decision.state == BudgetState.HARD_STOP
    assert decision.should_stop is True


def test_warning_only_dehydrates():
    mgr = TokenBudgetManager(
        context_window=100_000,
        max_output_tokens=2_000,
        safety_margin_tokens=1_000,
        thresholds=BudgetThresholds(warning_ratio=0.6),
    )
    decision = mgr.decide(60_000)  # projected = 63_000, ratio = 63%
    assert decision.state == BudgetState.WARNING
    assert decision.should_dehydrate is True
    assert decision.should_stop is False
    assert decision.should_checkpoint is False
