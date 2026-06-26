from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass(frozen=True)
class HealthCheck:
    endpoint: str
    ok: bool
    latency_ms: float
    detail: str = ""


@dataclass(frozen=True)
class ModelHealthResult:
    reachable: bool
    provider: str
    model: str
    base_url: str | None
    checks: tuple[HealthCheck, ...]
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def _build_url(base_url: str | None, path: str) -> str:
    """Build a full URL from a base_url and an API path."""
    if not base_url:
        return path
    base = base_url.rstrip("/")
    # If base_url already ends with /v1, don't double it
    if path.startswith("/v1/") and base.endswith("/v1"):
        return base + path[len("/v1"):]
    return base + path


def _safe_post_chat_completion(
    url: str,
    api_key: str | None,
    model: str,
    timeout: float,
) -> tuple[bool, str, float]:
    """Send a minimal chat-completion request. Returns (ok, detail, latency_ms)."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
        "stream": False,
    }
    start = __import__("time").time()
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)
        latency = (__import__("time").time() - start) * 1000
        if response.status_code == 200:
            return True, f"HTTP {response.status_code}", latency
        # Some local servers return 422 or 400 for unsupported params but are alive
        if response.status_code in (400, 422):
            return True, f"HTTP {response.status_code} (model may not support all params)", latency
        return False, f"HTTP {response.status_code}: {response.text[:200]}", latency
    except httpx.TimeoutException as exc:
        latency = (__import__("time").time() - start) * 1000
        return False, f"Timeout after {timeout}s", latency
    except httpx.ConnectError as exc:
        latency = (__import__("time").time() - start) * 1000
        return False, f"Connection error: {exc}", latency
    except Exception as exc:
        latency = (__import__("time").time() - start) * 1000
        return False, f"Error: {exc}", latency


def _safe_get_models(
    url: str,
    api_key: str | None,
    timeout: float,
) -> tuple[bool, str, float, list[str]]:
    """GET /v1/models. Returns (ok, detail, latency_ms, model_ids)."""
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    start = __import__("time").time()
    model_ids: list[str] = []
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, headers=headers)
        latency = (__import__("time").time() - start) * 1000
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                model_ids = [m.get("id", "") for m in data["data"] if isinstance(m, dict)]
            return True, f"HTTP {response.status_code} ({len(model_ids)} models)", latency, model_ids
        return False, f"HTTP {response.status_code}: {response.text[:200]}", latency, model_ids
    except httpx.TimeoutException as exc:
        latency = (__import__("time").time() - start) * 1000
        return False, f"Timeout after {timeout}s", latency, model_ids
    except Exception as exc:
        latency = (__import__("time").time() - start) * 1000
        return False, f"Error: {exc}", latency, model_ids


def _safe_get_health(
    url: str,
    timeout: float,
) -> tuple[bool, str, float]:
    """GET /health. Returns (ok, detail, latency_ms)."""
    start = __import__("time").time()
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url)
        latency = (__import__("time").time() - start) * 1000
        if response.status_code in (200, 204):
            return True, f"HTTP {response.status_code}", latency
        return False, f"HTTP {response.status_code}: {response.text[:200]}", latency
    except httpx.TimeoutException as exc:
        latency = (__import__("time").time() - start) * 1000
        return False, f"Timeout after {timeout}s", latency
    except Exception as exc:
        latency = (__import__("time").time() - start) * 1000
        return False, f"Error: {exc}", latency


def check_model_health(
    provider: str,
    base_url: str | None,
    api_key: str | None,
    model: str,
    timeout: float = 5.0,
) -> ModelHealthResult:
    """Run lightweight health checks against a local OpenAI-compatible endpoint.

    Never raises.  Failures are captured as warnings/errors in the result.
    """
    warnings: list[str] = []
    errors: list[str] = []
    checks: list[HealthCheck] = []
    reachable = False

    # 1. /health (optional — many local servers expose this)
    health_url = _build_url(base_url, "/health")
    ok, detail, latency = _safe_get_health(health_url, timeout)
    checks.append(HealthCheck(endpoint="/health", ok=ok, latency_ms=latency, detail=detail))
    if not ok:
        warnings.append(f"/health unavailable: {detail}")

    # 2. /v1/models
    models_url = _build_url(base_url, "/v1/models")
    ok, detail, latency, model_ids = _safe_get_models(models_url, api_key, timeout)
    checks.append(HealthCheck(endpoint="/v1/models", ok=ok, latency_ms=latency, detail=detail))
    if not ok:
        warnings.append(f"/v1/models unavailable: {detail}")
    else:
        reachable = True
        if model and model not in model_ids and model_ids:
            warnings.append(
                f"Model '{model}' not found in /v1/models list ({len(model_ids)} available)."
            )

    # 3. /v1/chat/completions minimal request
    chat_url = _build_url(base_url, "/v1/chat/completions")
    ok, detail, latency = _safe_post_chat_completion(chat_url, api_key, model, timeout)
    checks.append(
        HealthCheck(endpoint="/v1/chat/completions", ok=ok, latency_ms=latency, detail=detail)
    )
    if not ok:
        errors.append(f"Chat completions failed: {detail}")
    else:
        reachable = True

    return ModelHealthResult(
        reachable=reachable,
        provider=provider,
        model=model,
        base_url=base_url,
        checks=tuple(checks),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def format_model_health(result: ModelHealthResult) -> str:
    """Render a health result as a compact human-readable string."""
    lines = [
        f"Provider: {result.provider}",
        f"Model: {result.model}",
        f"Base URL: {result.base_url or '(default)'}",
        f"Reachable: {'yes' if result.reachable else 'no'}",
        "",
        "Checks:",
    ]
    for check in result.checks:
        icon = "[green]✓[/green]" if check.ok else "[red]✗[/red]"
        lines.append(f"  {icon} {check.endpoint} — {check.detail} ({check.latency_ms:.0f}ms)")
    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in result.warnings:
            lines.append(f"  [yellow]⚠[/yellow] {w}")
    if result.errors:
        lines.append("")
        lines.append("Errors:")
        for e in result.errors:
            lines.append(f"  [red]✗[/red] {e}")
    return "\n".join(lines)
