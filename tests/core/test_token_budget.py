
from core.token_budget import TokenBudgetManager, BudgetState, BudgetThresholds


def test_budget_manager_decides_states():
    mgr = TokenBudgetManager(BudgetThresholds(
        soft_limit=10,
        compact_limit=20,
        checkpoint_limit=30,
        hard_stop_limit=40,
        max_context=50,
    ))
    assert mgr.decide(5).state == BudgetState.NORMAL
    assert mgr.decide(15).state == BudgetState.WARNING
    assert mgr.decide(25).state == BudgetState.COMPACT
    assert mgr.decide(35).state == BudgetState.CHECKPOINT
    assert mgr.decide(45).state == BudgetState.HARD_STOP


def test_estimate_from_messages_roughly_counts_content():
    mgr = TokenBudgetManager()
    messages = [
        {"role": "user", "content": "a" * 400},
        {"role": "assistant", "content": [{"type": "text", "text": "b" * 400}]},
    ]
    estimate = mgr.estimate_from_messages(messages)
    assert estimate >= 200
