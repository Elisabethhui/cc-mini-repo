from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .codeintel import (
    DEFAULT_MAX_CHARS,
    DEFAULT_MAX_ITEMS,
    DEFAULT_MAX_LINES,
    DEFAULT_TIMEOUT_SECONDS,
    _compact_output,
)


@dataclass(frozen=True)
class RetrievalResult:
    """Compact result from a CodeGraph-first retrieval query."""

    provider: str
    query_type: str
    query: str
    ok: bool
    items: tuple[str, ...]
    confidence: float
    warnings: tuple[str, ...] = ()
    truncated: bool = False


def _calc_confidence(provider: str, items: tuple[str, ...], truncated: bool) -> float:
    if not items:
        return 0.0
    base = 0.95 if provider == "codegraph" else 0.65
    if truncated:
        base -= 0.10
    return round(base, 2)


def _run_command(
    root: Path,
    *,
    provider: str,
    query_type: str,
    query: str,
    argv: list[str],
    timeout_seconds: float,
    max_items: int,
    max_lines: int,
    max_chars: int,
) -> RetrievalResult:
    if shutil.which(argv[0]) is None:
        return RetrievalResult(
            provider=provider,
            query_type=query_type,
            query=query,
            ok=False,
            items=(),
            confidence=0.0,
            warnings=(f"{argv[0]} not available",),
            truncated=False,
        )
    try:
        proc = subprocess.run(
            argv,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return RetrievalResult(
            provider=provider,
            query_type=query_type,
            query=query,
            ok=False,
            items=(),
            confidence=0.0,
            warnings=(f"{provider} timed out after {timeout_seconds:g}s",),
            truncated=False,
        )
    except OSError as exc:
        return RetrievalResult(
            provider=provider,
            query_type=query_type,
            query=query,
            ok=False,
            items=(),
            confidence=0.0,
            warnings=(str(exc),),
            truncated=False,
        )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"{provider} exited {proc.returncode}"
        return RetrievalResult(
            provider=provider,
            query_type=query_type,
            query=query,
            ok=False,
            items=(),
            confidence=0.0,
            warnings=(detail,),
            truncated=False,
        )
    items, truncated = _compact_output(
        proc.stdout,
        max_items=max_items,
        max_lines=max_lines,
        max_chars=max_chars,
    )
    confidence = _calc_confidence(provider, items, truncated)
    return RetrievalResult(
        provider=provider,
        query_type=query_type,
        query=query,
        ok=True,
        items=items,
        confidence=confidence,
        warnings=(),
        truncated=truncated,
    )


class CodeGraphRetrievalAdapter:
    """CodeGraph-first retrieval with graceful fallback to rg/heuristics.

    All methods return compact ``RetrievalResult`` objects that include
    ``confidence``, ``warnings``, and ``truncated`` flags.
    """

    def __init__(
        self,
        root: Path,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_items: int = DEFAULT_MAX_ITEMS,
        max_lines: int = DEFAULT_MAX_LINES,
        max_chars: int = DEFAULT_MAX_CHARS,
    ) -> None:
        self.root = root.resolve()
        self.timeout_seconds = timeout_seconds
        self.max_items = max_items
        self.max_lines = max_lines
        self.max_chars = max_chars

    def available(self) -> bool:
        return shutil.which("codegraph") is not None

    def initialized(self) -> bool:
        return (self.root / ".codegraph").exists()

    def _try_codegraph_then_rg(
        self,
        query_type: str,
        query: str,
        codegraph_argv: list[str],
        rg_argv: list[str],
    ) -> RetrievalResult:
        if self.available():
            result = _run_command(
                self.root,
                provider="codegraph",
                query_type=query_type,
                query=query,
                argv=codegraph_argv,
                timeout_seconds=self.timeout_seconds,
                max_items=self.max_items,
                max_lines=self.max_lines,
                max_chars=self.max_chars,
            )
            if result.ok:
                return result
            warnings = result.warnings + ("codegraph query failed; using rg fallback",)
        else:
            warnings = ("codegraph not available; using rg fallback",)

        fallback = _run_command(
            self.root,
            provider="rg",
            query_type=query_type,
            query=query,
            argv=rg_argv,
            timeout_seconds=self.timeout_seconds,
            max_items=self.max_items,
            max_lines=self.max_lines,
            max_chars=self.max_chars,
        )
        merged_warnings = warnings + fallback.warnings
        return RetrievalResult(
            provider=fallback.provider,
            query_type=fallback.query_type,
            query=fallback.query,
            ok=fallback.ok,
            items=fallback.items,
            confidence=fallback.confidence,
            warnings=merged_warnings,
            truncated=fallback.truncated,
        )

    # ------------------------------------------------------------------
    # Public query API
    # ------------------------------------------------------------------

    def query_symbols(self, symbol: str) -> RetrievalResult:
        symbol = symbol.strip()
        if not symbol:
            return RetrievalResult(
                provider="none",
                query_type="symbols",
                query=symbol,
                ok=False,
                items=(),
                confidence=0.0,
                warnings=("symbol query is empty",),
                truncated=False,
            )
        return self._try_codegraph_then_rg(
            query_type="symbols",
            query=symbol,
            codegraph_argv=["codegraph", "node", symbol],
            rg_argv=["rg", "-n", "--no-heading", "--color", "never", rf"\b{symbol}\b", "."],
        )

    def query_files(self, pattern: str) -> RetrievalResult:
        pattern = pattern.strip()
        if not pattern:
            return RetrievalResult(
                provider="none",
                query_type="files",
                query=pattern,
                ok=False,
                items=(),
                confidence=0.0,
                warnings=("file pattern is empty",),
                truncated=False,
            )
        return self._try_codegraph_then_rg(
            query_type="files",
            query=pattern,
            codegraph_argv=["codegraph", "files", pattern],
            rg_argv=["rg", "-g", f"*{pattern}*", "--files"],
        )

    def query_tests(self, symbol_or_file: str) -> RetrievalResult:
        symbol_or_file = symbol_or_file.strip()
        if not symbol_or_file:
            return RetrievalResult(
                provider="none",
                query_type="tests",
                query=symbol_or_file,
                ok=False,
                items=(),
                confidence=0.0,
                warnings=("test query is empty",),
                truncated=False,
            )
        return self._try_codegraph_then_rg(
            query_type="tests",
            query=symbol_or_file,
            codegraph_argv=["codegraph", "test", symbol_or_file],
            rg_argv=["rg", "-n", "--no-heading", "--color", "never", r"\btest_", "."],
        )

    def query_callers(self, symbol: str) -> RetrievalResult:
        symbol = symbol.strip()
        if not symbol:
            return RetrievalResult(
                provider="none",
                query_type="callers",
                query=symbol,
                ok=False,
                items=(),
                confidence=0.0,
                warnings=("caller query is empty",),
                truncated=False,
            )
        return self._try_codegraph_then_rg(
            query_type="callers",
            query=symbol,
            codegraph_argv=["codegraph", "callers", symbol],
            rg_argv=["rg", "-n", "--no-heading", "--color", "never", rf"\b{symbol}\b", "."],
        )

    def query_impact(self, symbol_or_file: str) -> RetrievalResult:
        symbol_or_file = symbol_or_file.strip()
        if not symbol_or_file:
            return RetrievalResult(
                provider="none",
                query_type="impact",
                query=symbol_or_file,
                ok=False,
                items=(),
                confidence=0.0,
                warnings=("impact query is empty",),
                truncated=False,
            )
        return self._try_codegraph_then_rg(
            query_type="impact",
            query=symbol_or_file,
            codegraph_argv=["codegraph", "impact", symbol_or_file],
            rg_argv=["rg", "-n", "--no-heading", "--color", "never", symbol_or_file, "."],
        )

    def fallback_rg(self, keyword: str) -> RetrievalResult:
        keyword = keyword.strip()
        if not keyword:
            return RetrievalResult(
                provider="none",
                query_type="fallback_rg",
                query=keyword,
                ok=False,
                items=(),
                confidence=0.0,
                warnings=("fallback query is empty",),
                truncated=False,
            )
        return _run_command(
            self.root,
            provider="rg",
            query_type="fallback_rg",
            query=keyword,
            argv=["rg", "-n", "--no-heading", "--color", "never", keyword, "."],
            timeout_seconds=self.timeout_seconds,
            max_items=self.max_items,
            max_lines=self.max_lines,
            max_chars=self.max_chars,
        )
