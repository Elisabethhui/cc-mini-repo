---
source_hash: d0d25ebe97a4d36a
status: partially_digested
updated_at: 1776054844.6630266
---

# Entity: src/core/buddy/poke_game/persistence.py

## Classes


## Functions
- **def load_loot()**: Load persisted data from disk.
- **def save_loot()**: Save data to disk.
- **def save_session()**: Save tickets and badges at end of session. Everything else is discarded.
- **def restore_from_loot()**: Restore banked tickets, owned badges, and badge stat bonuses.
- **def _parse_effect()**: Parse badge effect string into [(stat, amount), ...].