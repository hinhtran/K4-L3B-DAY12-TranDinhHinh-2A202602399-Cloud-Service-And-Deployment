"""Kiểm tra CP5 qua HTTP thật; chỉ ghi kết quả, không ghi API key.

python scripts/check_deployment.py https://your-service.onrender.com
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
import uuid

import httpx
from dotenv import load_dotenv


def validate_url(value: str, local: bool = False) -> str:
    parsed = urlsplit(value)
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL cần hostname và không được chứa credential.")
    if parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise ValueError("Dùng URL gốc của service, không thêm path/query/fragment.")
    if parsed.scheme != "https":
        if not (local and parsed.scheme == "http" and parsed.hostname in
                ("localhost", "127.0.0.1", "::1")):
            raise ValueError("Cloud phải dùng HTTPS; --local chỉ cho phép HTTP trên loopback.")
    return value.rstrip("/")


def check_service(client: httpx.Client, api_key: str | None, rate_limit: int | None = None) -> list[dict]:
    results = []

    def request(name, method, path, expected, *, predicate=None, **kwargs):
        try:
            response = client.request(method, path, **kwargs)
            passed = response.status_code == expected
            if passed and predicate is not None:
                try:
                    passed = bool(predicate(response.json()))
                except (ValueError, KeyError, TypeError, AttributeError):
                    passed = False
            # Không ghi headers/body, tránh đưa secret hay nội dung hội thoại vào báo cáo.
            results.append({"check": name, "expected": expected,
                            "actual": response.status_code, "passed": passed})
        except httpx.HTTPError as error:
            results.append({"check": name, "expected": expected,
                            "error": type(error).__name__, "passed": False})

    request("health", "GET", "/health", 200,
            predicate=lambda body: body.get("status") == "ok")
    request("ready", "GET", "/ready", 200,
            predicate=lambda body: body.get("status") == "ready" and body.get("redis") is True)
    payload = {"question": "Kiểm tra triển khai CP5"}
    request("missing_key", "POST", "/ask", 401, json=payload)
    if api_key is not None:
        user_id = "cp5-" + uuid.uuid4().hex
        headers = {"X-API-Key": api_key, "X-User-Id": user_id}
        request("authenticated_ask", "POST", "/ask", 200, headers=headers, json=payload,
                predicate=lambda body: bool(body.get("answer")) and
                body.get("user_id") == user_id and body.get("history_length") == 0)
        request("history_persisted", "POST", "/ask", 200, headers=headers, json=payload,
                predicate=lambda body: bool(body.get("answer")) and body.get("history_length") == 2)
        if rate_limit is not None:
            headers = {**headers, "X-User-Id": "cp5-rate-" + uuid.uuid4().hex}
            for index in range(rate_limit):
                request(f"rate_allowed_{index + 1}", "POST", "/ask", 200,
                        headers=headers, json=payload)
                if not results[-1]["passed"]:
                    break
            else:
                request("rate_blocked", "POST", "/ask", 429, headers=headers, json=payload)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="URL gốc của service đã deploy")
    parser.add_argument("--local", action="store_true", help="Cho phép HTTP localhost; không phải bằng chứng cloud")
    parser.add_argument("--public-only", action="store_true", help="Chỉ kiểm tra health, ready và thiếu key")
    parser.add_argument("--rate-limit", type=int, help="Kiểm tra hạn mức/phút đã cấu hình (2–60)")
    parser.add_argument("--output", type=Path, help="Lưu báo cáo JSON không chứa secret")
    args = parser.parse_args()
    try:
        url = validate_url(args.url, args.local)
    except ValueError as error:
        parser.error(str(error))
    if args.rate_limit is not None and not 2 <= args.rate_limit <= 60:
        parser.error("--rate-limit phải từ 2 đến 60.")
    if args.public_only and args.rate_limit is not None:
        parser.error("--rate-limit cần API key; không dùng cùng --public-only.")

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    key = None
    if not args.public_only:
        key = os.getenv("DEPLOY_API_KEY") or getpass.getpass("API key của service (ẩn khi nhập): ")
        if not key.strip():
            parser.error("API key không được để trống.")
    with httpx.Client(base_url=url, timeout=60, follow_redirects=False) as client:
        results = check_service(client, key, args.rate_limit)
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "url": url,
              "mode": "local" if args.local else "cloud",
              "authenticated_checks": key is not None,
              "passed": all(item["passed"] for item in results), "checks": results}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
