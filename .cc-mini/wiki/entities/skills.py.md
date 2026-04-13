---
source_hash: b107f024882f8149
status: partially_digested
updated_at: 1776054844.6630266
---

# Entity: src/core/skills.py

## Classes
- **class Skill**: A single skill definition.
  - Methods: get_prompt

## Functions
- **def _parse_frontmatter()**: Split ``text`` into (frontmatter_dict, body).
- **def _ensure_str()**: Coerce *val* to a string — rejoin lists produced by the frontmatter parser.
- **def _skill_from_frontmatter()**: Build a ``Skill`` from parsed frontmatter and body text.
- **def register_skill()**: Add a skill to the global registry.
- **def get_skill()**: Look up a skill by name.
- **def list_skills()**: Return all registered skills, optionally filtered.
- **def clear_skills()**: Remove skills from the registry.  If *source* given, only that source.
- **def load_skills_from_dir()**: Scan *skills_dir* for ``<name>/SKILL.md`` and register each skill.
- **def discover_skills()**: Discover and register skills from standard locations.
- **def build_skills_prompt_section()**: Build the skills listing for the system prompt.