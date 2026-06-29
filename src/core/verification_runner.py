from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .dev_contract import VerificationSpec


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_STDOUT_CHARS = 4000
_MAX_STDERR_CHARS = 4000


# ---------------------------------------------------------------------------
# VerificationRunResult
# ---------------------------------------------------------------------------

@dataclass
class VerificationRunResult:
    """Outcome of running a VerificationSpec."""

    kind: str = ""
    command: list[str] = field(default_factory=list)
    expected_exit_code: int = 0
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    passed: bool = False
    skipped: bool = False
    timed_out: bool = False
    artifact_paths: list[str] = field(default_factory=list)
    summary: str = ""
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "command": list(self.command),
            "expected_exit_code": self.expected_exit_code,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": self.duration_seconds,
            "passed": self.passed,
            "skipped": self.skipped,
            "timed_out": self.timed_out,
            "artifact_paths": list(self.artifact_paths),
            "summary": self.summary,
            "risks": list(self.risks),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationRunResult:
        return cls(
            kind=str(data.get("kind", "")),
            command=list(data.get("command", [])),
            expected_exit_code=int(data.get("expected_exit_code", 0)),
            exit_code=data.get("exit_code"),
            stdout=str(data.get("stdout", "")),
            stderr=str(data.get("stderr", "")),
            duration_seconds=float(data.get("duration_seconds", 0.0)),
            passed=bool(data.get("passed", False)),
            skipped=bool(data.get("skipped", False)),
            timed_out=bool(data.get("timed_out", False)),
            artifact_paths=list(data.get("artifact_paths", [])),
            summary=str(data.get("summary", "")),
            risks=list(data.get("risks", [])),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_safe_path(workspace: Path, rel_path: str) -> bool:
    """Reject absolute paths and path traversal attempts."""
    if not rel_path:
        return False
    if rel_path.startswith("/"):
        return False
    parts = rel_path.replace("\\", "/").split("/")
    if ".." in parts:
        return False
    return True


def _resolve_within_workspace(workspace: Path, rel_path: str) -> Path | None:
    """Resolve a relative path under workspace, returning None if unsafe."""
    if not _is_safe_path(workspace, rel_path):
        return None
    target = (workspace / rel_path).resolve()
    try:
        target.relative_to(workspace.resolve())
    except ValueError:
        return None
    return target


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20] + "\n...[truncated]"


# ---------------------------------------------------------------------------
# VerificationRunner
# ---------------------------------------------------------------------------

class VerificationRunner:
    """Execute VerificationSpec in a bounded, safe manner."""

    def run(
        self,
        verification_spec: VerificationSpec,
        workspace: Path,
    ) -> VerificationRunResult:
        """Run the verification and return a result.

        Never uses shell=True.  Paths are restricted to *workspace*.
        """
        kind = verification_spec.kind
        if kind == "command":
            return self._run_command(verification_spec, workspace)
        if kind == "artifact":
            return self._run_artifact(verification_spec, workspace)
        if kind == "manual":
            return self._run_manual(verification_spec)
        if kind == "contract":
            return self._run_contract(verification_spec)
        return VerificationRunResult(
            kind=kind,
            passed=False,
            skipped=True,
            summary=f"Unknown verification kind: {kind}",
            risks=[f"Unknown verification kind: {kind}"],
        )

    def _run_command(
        self,
        spec: VerificationSpec,
        workspace: Path,
    ) -> VerificationRunResult:
        command = list(spec.command)
        if not command:
            return VerificationRunResult(
                kind="command",
                passed=False,
                skipped=True,
                summary="Empty command list",
                risks=["command verification has empty command list"],
            )

        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
                timeout=spec.timeout_seconds,
            )
            duration = time.monotonic() - t0
            exit_code = proc.returncode
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - t0
            exit_code = getattr(exc, "returncode", None)
            stdout_text = _truncate(exc.stdout or "", _MAX_STDOUT_CHARS)
            stderr_text = _truncate(exc.stderr or "", _MAX_STDERR_CHARS)
            return VerificationRunResult(
                kind="command",
                command=command,
                expected_exit_code=spec.expected_exit_code,
                exit_code=exit_code,
                stdout=stdout_text,
                stderr=stderr_text,
                duration_seconds=duration,
                passed=False,
                timed_out=True,
                summary=f"Command timed out after {spec.timeout_seconds}s",
                risks=[f"Timeout: {' '.join(command)}"],
            )
        except OSError as exc:
            duration = time.monotonic() - t0
            return VerificationRunResult(
                kind="command",
                command=command,
                expected_exit_code=spec.expected_exit_code,
                exit_code=None,
                stdout="",
                stderr=str(exc),
                duration_seconds=duration,
                passed=False,
                summary=f"Command failed to start: {exc}",
                risks=[f"OSError: {exc}"],
            )

        stdout_text = _truncate(proc.stdout, _MAX_STDOUT_CHARS)
        stderr_text = _truncate(proc.stderr, _MAX_STDERR_CHARS)
        passed = exit_code == spec.expected_exit_code

        summary = (
            f"Command {' '.join(command)} exited {exit_code} "
            f"(expected {spec.expected_exit_code})"
        )
        risks: list[str] = []
        if not passed and not timed_out:
            risks.append(f"Exit code mismatch: got {exit_code}, expected {spec.expected_exit_code}")

        return VerificationRunResult(
            kind="command",
            command=command,
            expected_exit_code=spec.expected_exit_code,
            exit_code=exit_code,
            stdout=stdout_text,
            stderr=stderr_text,
            duration_seconds=duration,
            passed=passed,
            timed_out=timed_out,
            summary=summary,
            risks=risks,
        )

    def _run_artifact(
        self,
        spec: VerificationSpec,
        workspace: Path,
    ) -> VerificationRunResult:
        expected = list(spec.expected_artifacts)
        if not expected:
            return VerificationRunResult(
                kind="artifact",
                passed=False,
                skipped=True,
                summary="No expected artifacts specified",
                risks=["artifact verification has empty expected_artifacts"],
            )

        found: list[str] = []
        missing: list[str] = []
        for rel_path in expected:
            target = _resolve_within_workspace(workspace, rel_path)
            if target is None:
                missing.append(rel_path)
                continue
            if target.exists():
                found.append(rel_path)
            else:
                missing.append(rel_path)

        passed = not missing
        summary = (
            f"Artifacts: {len(found)}/{len(expected)} present"
            if missing
            else f"All {len(expected)} artifacts present"
        )
        risks = [f"Missing artifacts: {missing}"] if missing else []

        return VerificationRunResult(
            kind="artifact",
            passed=passed,
            artifact_paths=found,
            summary=summary,
            risks=risks,
        )

    def _run_manual(self, spec: VerificationSpec) -> VerificationRunResult:
        return VerificationRunResult(
            kind="manual",
            passed=False,
            skipped=True,
            summary=f"Manual verification required: {spec.notes}",
            risks=["Manual verification not performed automatically"],
        )

    def _run_contract(self, spec: VerificationSpec) -> VerificationRunResult:
        errors = spec.validate()
        passed = not errors
        return VerificationRunResult(
            kind="contract",
            passed=passed,
            summary="Contract validation " + ("passed" if passed else "failed"),
            risks=errors,
        )
