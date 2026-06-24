from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .codeintel import CodeIntelProvider


DEFAULT_MAX_RECOMMENDATIONS = 6
DEFAULT_MAX_WARNINGS = 4


@dataclass(frozen=True)
class TestRecommendation:
    test_target: str
    command: str
    source: str
    reason: str


@dataclass(frozen=True)
class TestSelectionResult:
    changed_files: tuple[str, ...]
    recommendations: tuple[TestRecommendation, ...]
    confidence: str
    warnings: tuple[str, ...]
    truncated: bool = False


def select_tests_for_changes(
    root: Path,
    changed_files: list[str] | tuple[str, ...],
    *,
    codeintel: CodeIntelProvider | None = None,
    max_recommendations: int = DEFAULT_MAX_RECOMMENDATIONS,
) -> TestSelectionResult:
    root = root.resolve()
    normalized = _normalize_changed_files(changed_files)
    warnings: list[str] = []
    recommendations: list[TestRecommendation] = []
    truncated = False

    provider = codeintel or CodeIntelProvider(root)
    if provider.available() and provider.initialized():
        recommendations.extend(_collect_codeintel_recommendations(provider, normalized))
        if recommendations:
            return _finalize_result(
                normalized,
                recommendations,
                confidence="high",
                warnings=warnings,
                max_recommendations=max_recommendations,
            )
        warnings.append("codeintel returned no affected tests; using fallback rules")
    else:
        warnings.append("codeintel unavailable; using fallback rules")

    mapping = _load_testing_mappings(root)
    recommendations.extend(_collect_manual_recommendations(normalized, mapping))
    recommendations.extend(_collect_nearby_recommendations(normalized))

    if not recommendations:
        recommendations.append(
            TestRecommendation(
                test_target="tests/",
                command='pytest tests/ -v -k "not integration"',
                source="fallback",
                reason="broad fallback because no targeted tests were identified",
            )
        )
        confidence = "low"
    else:
        confidence = "medium"

    result = _finalize_result(
        normalized,
        recommendations,
        confidence=confidence,
        warnings=warnings,
        max_recommendations=max_recommendations,
    )
    truncated = result.truncated
    return TestSelectionResult(
        changed_files=result.changed_files,
        recommendations=result.recommendations,
        confidence=result.confidence,
        warnings=result.warnings,
        truncated=truncated,
    )


def format_test_selection_result(result: TestSelectionResult) -> str:
    lines = [
        "Test Selector",
        f"Confidence: {result.confidence}",
        f"Changed files: {len(result.changed_files)}",
        "",
        "Recommendations:",
    ]
    for recommendation in result.recommendations:
        lines.append(
            f"- {recommendation.command} [{recommendation.source}: {recommendation.reason}]"
        )
    if result.warnings:
        lines.extend(("", "Warnings:"))
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.truncated:
        lines.append("")
        lines.append("Truncated: true")
    return "\n".join(lines).rstrip()


def _collect_codeintel_recommendations(
    provider: CodeIntelProvider,
    changed_files: tuple[str, ...],
) -> list[TestRecommendation]:
    seen: set[str] = set()
    recommendations: list[TestRecommendation] = []
    for changed_file in changed_files:
        result = provider.query(changed_file)
        for item in result.items:
            for target in _extract_test_targets(item):
                if target in seen:
                    continue
                seen.add(target)
                recommendations.append(
                    TestRecommendation(
                        test_target=target,
                        command=_build_pytest_command(target),
                        source="codeintel",
                        reason=f"affected test discovered for {changed_file}",
                    )
                )
    return recommendations


def _collect_manual_recommendations(
    changed_files: tuple[str, ...],
    mapping: tuple[tuple[str, tuple[str, ...]], ...],
) -> list[TestRecommendation]:
    seen: set[str] = set()
    recommendations: list[TestRecommendation] = []
    for changed_file in changed_files:
        for source_path, test_targets in mapping:
            if not _mapping_matches(changed_file, source_path):
                continue
            for target in test_targets:
                if target in seen:
                    continue
                seen.add(target)
                recommendations.append(
                    TestRecommendation(
                        test_target=target,
                        command=_build_pytest_command(target),
                        source="manual",
                        reason=f"mapped from {source_path}",
                    )
                )
    return recommendations


def _collect_nearby_recommendations(changed_files: tuple[str, ...]) -> list[TestRecommendation]:
    seen: set[str] = set()
    recommendations: list[TestRecommendation] = []
    for changed_file in changed_files:
        path = Path(changed_file)
        if path.parts[:2] != ("src", "core") or path.suffix != ".py":
            continue
        stem = path.stem
        candidates = (
            f"tests/test_{stem}.py",
            f"tests/core/test_{stem}.py",
        )
        for target in candidates:
            if target in seen:
                continue
            seen.add(target)
            recommendations.append(
                TestRecommendation(
                    test_target=target,
                    command=_build_pytest_command(target),
                    source="nearby",
                    reason=f"filename heuristic for {changed_file}",
                )
            )
    return recommendations


def _load_testing_mappings(root: Path) -> tuple[tuple[str, tuple[str, ...]], ...]:
    path = root / ".ai-dev" / "TESTING.md"
    if not path.exists():
        return ()
    mappings: list[tuple[str, tuple[str, ...]]] = []
    pattern = re.compile(r"^- `([^`]+)` -> (.+)$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        source_path = match.group(1)
        test_targets = tuple(re.findall(r"`([^`]+)`", match.group(2)))
        if test_targets:
            mappings.append((source_path, test_targets))
    return tuple(mappings)


def _finalize_result(
    changed_files: tuple[str, ...],
    recommendations: list[TestRecommendation],
    *,
    confidence: str,
    warnings: list[str],
    max_recommendations: int,
) -> TestSelectionResult:
    deduped = _dedupe_recommendations(recommendations)
    truncated = len(deduped) > max_recommendations
    trimmed = tuple(deduped[:max_recommendations])
    trimmed_warnings = tuple(warnings[:DEFAULT_MAX_WARNINGS])
    if len(warnings) > DEFAULT_MAX_WARNINGS:
        truncated = True
    return TestSelectionResult(
        changed_files=changed_files,
        recommendations=trimmed,
        confidence=confidence,
        warnings=trimmed_warnings,
        truncated=truncated,
    )


def _normalize_changed_files(changed_files: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in changed_files:
        candidate = raw.strip()
        if not candidate:
            continue
        if " -> " in candidate:
            candidate = candidate.split(" -> ", 1)[1].strip()
        parts = candidate.split()
        if len(parts) > 1 and not parts[0].startswith(("src/", "tests/", ".ai-dev/")):
            candidate = parts[-1]
        if candidate.startswith("a/") or candidate.startswith("b/"):
            candidate = candidate[2:]
        if candidate not in seen:
            seen.add(candidate)
            normalized.append(candidate)
    return tuple(normalized)


def _extract_test_targets(text: str) -> tuple[str, ...]:
    raw_matches = re.findall(r"(tests/[A-Za-z0-9_./:-]+)", text)
    matches: list[str] = []
    for match in raw_matches:
        py_index = match.find(".py")
        if py_index == -1:
            continue
        target = match[: py_index + 3]
        suffix = match[py_index + 3 :]
        if suffix.startswith("::"):
            target += suffix
        matches.append(target)
    return tuple(matches)


def _mapping_matches(changed_file: str, source_path: str) -> bool:
    if source_path.endswith("/"):
        return changed_file.startswith(source_path)
    return changed_file == source_path


def _build_pytest_command(target: str) -> str:
    return f"pytest {target} -v"


def _dedupe_recommendations(recommendations: list[TestRecommendation]) -> list[TestRecommendation]:
    seen: set[str] = set()
    deduped: list[TestRecommendation] = []
    for recommendation in recommendations:
        if recommendation.command in seen:
            continue
        seen.add(recommendation.command)
        deduped.append(recommendation)
    return deduped
