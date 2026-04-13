---
source_hash: 4e0fe72978b840bd
status: partially_digested
updated_at: 1776054844.6630266
---

# Entity: src/core/buddy/storage.py

## Classes


## Functions
- **def _ensure_dir()**: 无文档说明
- **def _read_data()**: Read and return raw JSON data, or None if missing/corrupt.
- **def _write_data()**: 无文档说明
- **def _migrate_if_needed()**: Migrate old flat format to new multi-companion format in-place.
- **def _default_seed()**: Build the default seed for the original companion (matches companion.py logic).
- **def load_stored_companion()**: Load the *active* stored companion from disk, or None if not hatched yet.
- **def load_active_seed()**: Load the seed of the active companion.
- **def save_stored_companion()**: Save the companion soul to disk (first companion / original hatch).
- **def save_new_companion()**: Append a new companion to the collection and make it active.
- **def load_all_stored_companions()**: Load all stored companions.
- **def load_active_index()**: Return the active companion index (0-based).
- **def save_active_index()**: Set the active companion index. Returns True on success.
- **def load_companion_muted()**: Check if companion reactions are muted.
- **def save_companion_muted()**: Toggle the muted flag in the companion file.
- **def load_active_mood()**: Load mood of the active companion. Returns neutral mood if missing.
- **def save_active_mood()**: Save mood for the active companion.