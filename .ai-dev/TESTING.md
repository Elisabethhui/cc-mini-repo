# Testing Registry

## Principle

Run the smallest useful verification first.

## Main Commands

```bash
pytest tests/ -v
pytest tests/ -v -k "not integration"
pytest tests/test_engine.py -v
pytest tests/test_engine.py::test_name -v
pytest tests/core/ -v
```

## Smoke

```bash
PYTHONPATH=src python -m core.main --help
PYTHONPATH=src python -c "import core; print('ok')"
```

## Mapping

- `src/core/engine.py` -> `tests/test_engine.py`
- `src/core/config.py` -> `tests/test_config.py`
- `src/core/context.py` -> `tests/test_context.py`
- `src/core/commands.py` -> `tests/test_commands.py`
- `src/core/permissions.py` -> `tests/test_permissions.py`
- `src/core/skills.py` -> `tests/test_skills.py`
- `src/core/token_budget.py` -> `tests/core/test_token_budget.py`
- `src/core/wiki/` -> `tests/test_wiki_phase1.py`, `tests/test_wiki_phase3.py`, `tests/test_wiki_phase6.py`
