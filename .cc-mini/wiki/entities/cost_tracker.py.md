---
source_hash: 8b1a1789eab251fd
status: partially_digested
updated_at: 1776054844.6630266
---

# Entity: src/core/cost_tracker.py

## Classes
- **class _PricingTier**: 无文档说明
  - Methods: 
- **class ModelUsage**: 无文档说明
  - Methods: 
- **class CostTracker**: Accumulates token usage and cost across API calls.
  - Methods: __init__, total_cost_usd, last_input_tokens, calculate_cost, add_usage, add_lines_changed, format_cost

## Functions
- **def _tier_for_model()**: 无文档说明
- **def _is_known_model()**: 无文档说明
- **def _fmt_tokens()**: Format token count with k/m suffixes like the official CLI.
- **def _fmt_duration()**: Format seconds as 'Xh Ym Zs', 'Ym Zs', or 'Xs'.