"""Test offline cho công cụ kiểm tra CP5; không phải bằng chứng cloud."""

import json

import httpx
import pytest

from scripts.check_deployment import check_service, validate_url


@pytest.mark.parametrize("url", [
    "http://service.example", "https://user:secret@service.example",
    "https://service.example/ask", "https://service.example?key=secret",
])
def test_rejects_unsafe_or_non_root_cloud_url(url):
    with pytest.raises(ValueError):
        validate_url(url)


def test_http_requires_explicit_local_mode():
    with pytest.raises(ValueError):
        validate_url("http://localhost:8000")
    assert validate_url("http://localhost:8000/", local=True) == "http://localhost:8000"
    with pytest.raises(ValueError):
        validate_url("http://service.example", local=True)


def test_authenticated_history_rate_limit_and_secret_redaction():
    counts = {}
    key = "dummy-key-only-for-tests"

    def handle(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/ready":
            return httpx.Response(200, json={"status": "ready", "redis": True})
        if request.headers.get("X-API-Key") != key:
            return httpx.Response(401)
        user = request.headers["X-User-Id"]
        count = counts.get(user, 0)
        counts[user] = count + 1
        if count >= 2:
            return httpx.Response(429)
        return httpx.Response(200, json={
            "answer": "Mock response", "user_id": user, "history_length": count * 2,
        })

    with httpx.Client(base_url="https://service.example", transport=httpx.MockTransport(handle)) as client:
        results = check_service(client, key, rate_limit=2)
    assert len(results) == 8
    assert all(result["passed"] for result in results)
    assert key not in json.dumps(results)
    assert len(counts) == 2  # Rate-limit probe uses a different user from history probe.


def test_public_checks_detect_bad_json_unready_and_unprotected_api():
    def handle(request):
        if request.url.path == "/health":
            return httpx.Response(200, text="not JSON")
        if request.url.path == "/ready":
            return httpx.Response(503)
        return httpx.Response(200)

    with httpx.Client(base_url="https://service.example", transport=httpx.MockTransport(handle)) as client:
        results = check_service(client, None)
    assert len(results) == 3
    assert not any(result["passed"] for result in results)


def test_connection_failure_does_not_disclose_exception_details():
    def handle(request):
        raise httpx.ConnectError("sensitive detail", request=request)

    with httpx.Client(base_url="https://service.example", transport=httpx.MockTransport(handle)) as client:
        results = check_service(client, None)
    assert all(not result["passed"] for result in results)
    assert all(result["error"] == "ConnectError" for result in results)
    assert "sensitive detail" not in json.dumps(results)
