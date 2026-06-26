from unittest.mock import MagicMock, patch

import httpx

from core.model_health import (
    check_model_health,
    format_model_health,
    HealthCheck,
    ModelHealthResult,
)


def _make_response(status_code: int, json_data: dict | None = None, text: str = ""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    return resp


def test_health_all_ok():
    with patch("httpx.Client") as MockClient:
        client = MagicMock()
        MockClient.return_value.__enter__ = lambda self, *a, **k: self
        MockClient.return_value.__exit__ = lambda self, *a, **k: None
        MockClient.return_value.get = client.get
        MockClient.return_value.post = client.post

        client.get.side_effect = [
            _make_response(200),  # /health
            _make_response(200, {"data": [{"id": "mymodel"}]}),  # /v1/models
        ]
        client.post.return_value = _make_response(200)  # /v1/chat/completions

        result = check_model_health(
            provider="openai",
            base_url="http://localhost:1234",
            api_key="fake-key",
            model="mymodel",
            timeout=2.0,
        )

    assert result.reachable is True
    assert result.provider == "openai"
    assert result.model == "mymodel"
    assert len(result.checks) == 3
    assert all(c.ok for c in result.checks)
    assert result.errors == ()
    assert result.warnings == ()


def test_health_chat_completions_fails():
    with patch("httpx.Client") as MockClient:
        client = MagicMock()
        MockClient.return_value.__enter__ = lambda self, *a, **k: self
        MockClient.return_value.__exit__ = lambda self, *a, **k: None
        MockClient.return_value.get = client.get
        MockClient.return_value.post = client.post

        client.get.side_effect = [
            _make_response(200),  # /health
            _make_response(200, {"data": [{"id": "mymodel"}]}),  # /v1/models
        ]
        client.post.return_value = _make_response(500, text="server error")

        result = check_model_health(
            provider="openai",
            base_url="http://localhost:1234",
            api_key=None,
            model="mymodel",
            timeout=2.0,
        )

    assert result.reachable is True  # /v1/models succeeded
    assert result.checks[2].ok is False
    assert len(result.errors) == 1
    assert "Chat completions failed" in result.errors[0]


def test_health_connect_error():
    with patch("httpx.Client") as MockClient:
        client = MagicMock()
        MockClient.return_value.__enter__ = lambda self, *a, **k: self
        MockClient.return_value.__exit__ = lambda self, *a, **k: None
        MockClient.return_value.get = client.get
        MockClient.return_value.post = client.post

        exc = httpx.ConnectError("Connection refused")
        client.get.side_effect = [exc, exc]
        client.post.side_effect = exc

        result = check_model_health(
            provider="openai",
            base_url="http://localhost:1234",
            api_key=None,
            model="mymodel",
            timeout=2.0,
        )

    assert result.reachable is False
    assert len(result.warnings) == 2
    assert len(result.errors) == 1
    assert all(not c.ok for c in result.checks)


def test_health_model_not_in_list():
    with patch("httpx.Client") as MockClient:
        client = MagicMock()
        MockClient.return_value.__enter__ = lambda self, *a, **k: self
        MockClient.return_value.__exit__ = lambda self, *a, **k: None
        MockClient.return_value.get = client.get
        MockClient.return_value.post = client.post

        client.get.side_effect = [
            _make_response(200),  # /health
            _make_response(200, {"data": [{"id": "other-model"}]}),  # /v1/models
        ]
        client.post.return_value = _make_response(200)

        result = check_model_health(
            provider="openai",
            base_url="http://localhost:1234",
            api_key=None,
            model="mymodel",
            timeout=2.0,
        )

    assert result.reachable is True
    assert len(result.warnings) == 1
    assert "mymodel" in result.warnings[0]


def test_format_model_health():
    result = ModelHealthResult(
        reachable=True,
        provider="openai",
        model="mymodel",
        base_url="http://localhost:1234",
        checks=(
            HealthCheck(endpoint="/health", ok=True, latency_ms=12.0, detail="HTTP 200"),
            HealthCheck(endpoint="/v1/models", ok=False, latency_ms=0.0, detail="Timeout"),
            HealthCheck(endpoint="/v1/chat/completions", ok=True, latency_ms=45.0, detail="HTTP 200"),
        ),
        warnings=("Model not in list",),
        errors=(),
    )
    text = format_model_health(result)
    assert "Provider: openai" in text
    assert "Reachable: yes" in text
    assert "/health" in text
    assert "/v1/models" in text
    assert "/v1/chat/completions" in text
    assert "Warnings:" in text
    assert "Model not in list" in text


def test_health_minimal_request_400_treated_as_ok():
    """Some local servers return 400/422 for unsupported params but are alive."""
    with patch("httpx.Client") as MockClient:
        client = MagicMock()
        MockClient.return_value.__enter__ = lambda self, *a, **k: self
        MockClient.return_value.__exit__ = lambda self, *a, **k: None
        MockClient.return_value.get = client.get
        MockClient.return_value.post = client.post

        client.get.side_effect = [
            _make_response(200),
            _make_response(200, {"data": [{"id": "mymodel"}]}),
        ]
        client.post.return_value = _make_response(422, text="unprocessable")

        result = check_model_health(
            provider="openai",
            base_url="http://localhost:1234",
            api_key=None,
            model="mymodel",
            timeout=2.0,
        )

    assert result.checks[2].ok is True
    assert "422" in result.checks[2].detail
    assert result.reachable is True
