from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess


DEFAULT_TIMEOUT_SECONDS = 2.0
DEFAULT_MAX_ITEMS = 20
DEFAULT_MAX_LINES = 40
DEFAULT_MAX_CHARS = 2000


@dataclass(frozen=True)
class CodeIntelResult:
    provider: str
    query: str
    ok: bool
    items: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    truncated: bool = False


class CodeIntelProvider:
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

    def status(self) -> CodeIntelResult:
        if self.available():
            result = self._run_command(
                provider="codegraph",
                query="status",
                argv=["codegraph", "status"],
            )
            if result.ok:
                return result
            warnings = result.warnings + ("codegraph status failed; using rg fallback",)
        else:
            warnings = ("codegraph not available; using rg fallback",)
        fallback = self._run_command(
            provider="rg",
            query="status",
            argv=["rg", "--files", ".ai-dev", "AGENTS.md"],
        )
        return self._with_warnings(fallback, warnings)

    def query(self, keyword: str) -> CodeIntelResult:
        keyword = keyword.strip()
        if not keyword:
            return CodeIntelResult(
                provider="none",
                query=keyword,
                ok=False,
                items=(),
                warnings=("query is empty",),
                truncated=False,
            )
        if self.available():
            result = self._run_command(
                provider="codegraph",
                query=keyword,
                argv=["codegraph", "query", keyword],
            )
            if result.ok:
                return result
            warnings = result.warnings + ("codegraph query failed; using rg fallback",)
        else:
            warnings = ("codegraph not available; using rg fallback",)
        fallback = self._run_command(
            provider="rg",
            query=keyword,
            argv=["rg", "-n", "--no-heading", "--color", "never", keyword, "."],
        )
        return self._with_warnings(fallback, warnings)

    def _run_command(self, *, provider: str, query: str, argv: list[str]) -> CodeIntelResult:
        if shutil.which(argv[0]) is None:
            return CodeIntelResult(
                provider=provider,
                query=query,
                ok=False,
                items=(),
                warnings=(f"{argv[0]} not available",),
                truncated=False,
            )
        try:
            proc = subprocess.run(
                argv,
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return CodeIntelResult(
                provider=provider,
                query=query,
                ok=False,
                items=(),
                warnings=(f"{provider} timed out after {self.timeout_seconds:g}s",),
                truncated=False,
            )
        except OSError as exc:
            return CodeIntelResult(
                provider=provider,
                query=query,
                ok=False,
                items=(),
                warnings=(str(exc),),
                truncated=False,
            )
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip() or f"{provider} exited {proc.returncode}"
            return CodeIntelResult(
                provider=provider,
                query=query,
                ok=False,
                items=(),
                warnings=(detail,),
                truncated=False,
            )
        items, truncated = _compact_output(
            proc.stdout,
            max_items=self.max_items,
            max_lines=self.max_lines,
            max_chars=self.max_chars,
        )
        return CodeIntelResult(
            provider=provider,
            query=query,
            ok=True,
            items=items,
            warnings=(),
            truncated=truncated,
        )

    def _with_warnings(self, result: CodeIntelResult, warnings: tuple[str, ...]) -> CodeIntelResult:
        return CodeIntelResult(
            provider=result.provider,
            query=result.query,
            ok=result.ok,
            items=result.items,
            warnings=warnings + result.warnings,
            truncated=result.truncated,
        )


def _compact_output(
    text: str,
    *,
    max_items: int,
    max_lines: int,
    max_chars: int,
) -> tuple[tuple[str, ...], bool]:
    source_lines = [line.strip() for line in text.splitlines() if line.strip()]
    total_lines = source_lines[:max_lines]
    truncated = len(source_lines) > len(total_lines)
    items: list[str] = []
    used_chars = 0
    for line in total_lines:
        if len(items) >= max_items:
            truncated = True
            break
        next_chars = used_chars + len(line)
        if items:
            next_chars += 1
        if next_chars > max_chars:
            truncated = True
            break
        items.append(line)
        used_chars = next_chars
    return tuple(items), truncated
