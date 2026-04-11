# Entity: src/core/buddy/observer.py

## Classes
- **class CompanionChat**: Maintains conversation history for direct companion interactions.
  - Methods: __init__, add_user, add_assistant, get_messages, _trim

## Functions
- **def _is_addressed()**: Check if the user is directly addressing the companion by name.
- **def fire_companion_observer()**: Fire a background thread that generates a companion reaction.
- **def _extract_text()**: 无文档说明