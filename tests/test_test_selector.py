from __future__ import annotations

from pathlib import Path

from core.codeintel import CodeIntelResult
from core.test_selector import format_test_selection_result, select_tests_for_changes


class FakeCodeIntel:
    def __init__(
        self,
        *,
        available: bool,
        initialized: bool,
        results: dict[str, CodeIntelResult] | None = None,
    ) -> None:
        self._available = available
        self._initialized = initialized
        self._results = results or {}
        self.queries: list[str] = []

    def available(self) -> bool:
        return self._available

    def initialized(self) -> bool:
        return self._initialized

    def query(self, keyword: str) -> CodeIntelResult:
        self.queries.append(keyword)
        return self._results.get(
            keyword,
            CodeIntelResult(provider="codegraph", query=keyword, ok=True, items=(), warnings=(), truncated=False),
        )


def _write_testing_registry(root: Path) -> None:
    testing = root / ".ai-dev" / "TESTING.md"
    testing.parent.mkdir(parents=True, exist_ok=True)
    testing.write_text(
        "# Testing Registry\n\n"
        "- `src/core/commands.py` -> `tests/test_commands.py`\n"
        "- `src/core/wiki/` -> `tests/test_wiki_phase1.py`, `tests/test_wiki_phase3.py`\n",
        encoding="utf-8",
    )


def test_select_tests_prefers_codeintel_results(tmp_path):
    _write_testing_registry(tmp_path)
    codeintel = FakeCodeIntel(
        available=True,
        initialized=True,
        results={
            "src/core/commands.py": CodeIntelResult(
                provider="codegraph",
                query="src/core/commands.py",
                ok=True,
                items=("tests/test_commands.py:10:test_help", "tests/test_main.py:2:test_cli"),
                warnings=(),
                truncated=False,
            )
        },
    )

    result = select_tests_for_changes(
        tmp_path,
        ["src/core/commands.py"],
        codeintel=codeintel,
    )

    assert result.confidence == "high"
    assert result.warnings == ()
    assert [item.command for item in result.recommendations] == [
        "pytest tests/test_commands.py -v",
        "pytest tests/test_main.py -v",
    ]
    assert codeintel.queries == ["src/core/commands.py"]


def test_select_tests_falls_back_to_manual_mapping_when_codeintel_unavailable(tmp_path):
    _write_testing_registry(tmp_path)
    codeintel = FakeCodeIntel(available=False, initialized=False)

    result = select_tests_for_changes(
        tmp_path,
        ["src/core/commands.py"],
        codeintel=codeintel,
    )

    assert result.confidence == "medium"
    assert result.recommendations[0].command == "pytest tests/test_commands.py -v"
    assert "codeintel unavailable; using fallback rules" in result.warnings
    assert codeintel.queries == []


def test_select_tests_falls_back_to_nearby_heuristic(tmp_path):
    _write_testing_registry(tmp_path)
    codeintel = FakeCodeIntel(available=False, initialized=False)

    result = select_tests_for_changes(
        tmp_path,
        ["src/core/codeintel.py"],
        codeintel=codeintel,
    )

    commands = [item.command for item in result.recommendations]
    assert "pytest tests/test_codeintel.py -v" in commands
    assert "pytest tests/core/test_codeintel.py -v" in commands


def test_select_tests_uses_broad_fallback_when_no_targeted_tests_found(tmp_path):
    _write_testing_registry(tmp_path)
    codeintel = FakeCodeIntel(available=False, initialized=False)

    result = select_tests_for_changes(
        tmp_path,
        ["README.md"],
        codeintel=codeintel,
    )

    assert result.confidence == "low"
    assert result.recommendations == (
        result.recommendations[0],
    )
    assert result.recommendations[0].command == 'pytest tests/ -v -k "not integration"'


def test_select_tests_normalizes_diff_style_file_inputs(tmp_path):
    _write_testing_registry(tmp_path)
    codeintel = FakeCodeIntel(available=False, initialized=False)

    result = select_tests_for_changes(
        tmp_path,
        ["M src/core/commands.py", "A  b/src/core/commands.py", "src/core/commands.py -> src/core/commands.py"],
        codeintel=codeintel,
    )

    assert result.changed_files == ("src/core/commands.py",)
    assert result.recommendations[0].command == "pytest tests/test_commands.py -v"


def test_select_tests_truncates_recommendations(tmp_path):
    _write_testing_registry(tmp_path)
    codeintel = FakeCodeIntel(
        available=True,
        initialized=True,
        results={
            "src/core/wiki/router.py": CodeIntelResult(
                provider="codegraph",
                query="src/core/wiki/router.py",
                ok=True,
                items=(
                    "tests/test_a.py:1:test_a",
                    "tests/test_b.py:1:test_b",
                    "tests/test_c.py:1:test_c",
                ),
                warnings=(),
                truncated=False,
            )
        },
    )

    result = select_tests_for_changes(
        tmp_path,
        ["src/core/wiki/router.py"],
        codeintel=codeintel,
        max_recommendations=2,
    )

    assert result.truncated is True
    assert len(result.recommendations) == 2


def test_format_test_selection_result_is_compact(tmp_path):
    _write_testing_registry(tmp_path)
    codeintel = FakeCodeIntel(available=False, initialized=False)

    result = select_tests_for_changes(
        tmp_path,
        ["src/core/commands.py"],
        codeintel=codeintel,
    )
    text = format_test_selection_result(result)

    assert "Test Selector" in text
    assert "Confidence: medium" in text
    assert "Recommendations:" in text
    assert "pytest tests/test_commands.py -v" in text
    assert "Warnings:" in text
