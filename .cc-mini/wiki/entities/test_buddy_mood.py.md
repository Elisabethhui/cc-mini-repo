# Entity: tests/test_buddy_mood.py

## Classes
- **class TestCompanionMood**: 无文档说明
  - Methods: test_default_neutral, test_to_dict_round_trip, test_from_dict_missing_keys, test_dominant_returns_furthest_from_neutral, test_dominant_all_neutral
- **class TestClassifyEvents**: 无文档说明
  - Methods: test_success_keywords, test_error_keywords, test_exploration_keywords, test_long_text, test_no_events_for_generic_text, test_case_insensitive, test_multiple_events
- **class TestApplyEvents**: 无文档说明
  - Methods: test_pet_boosts_happy, test_error_boosts_grumpy, test_clamp_upper, test_clamp_lower, test_multiple_events_stack, test_unknown_event_ignored, test_preserves_last_updated
- **class TestMoodDecay**: 无文档说明
  - Methods: test_no_decay_on_first_update, test_decay_toward_neutral, test_no_overshoot_above, test_no_overshoot_below, test_bored_drift_on_idle, test_no_decay_within_same_minute
- **class TestDescribeMood**: 无文档说明
  - Methods: test_contains_dimensions, test_contains_dominant
- **class TestMoodStorage**: 无文档说明
  - Methods: test_round_trip, test_missing_mood_returns_neutral, test_missing_file_returns_neutral, test_mood_preserves_companion_data

## Functions
