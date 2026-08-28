from __future__ import annotations

from pathlib import Path
from urllib.error import URLError
from urllib.request import Request

import pytest

from coa_workbench.collector.browser_context_api import (
    BrowserContextApiConfig,
    BrowserPageUrlOpener,
)


class _FakePage:
    def __init__(self, result: object) -> None:
        self.result = result
        self.urls: list[str] = []

    def evaluate(self, _script: str, url: str) -> object:
        self.urls.append(url)
        return self.result


def test_browser_page_url_opener_executes_exact_same_origin_get() -> None:
    page = _FakePage(
        {
            "ok": True,
            "status": 200,
            "contentType": "application/json; charset=utf-8",
            "body": '{"ok":true}',
        }
    )
    opener = BrowserPageUrlOpener(page, allowed_host="coa.ascensionlogs.gg")
    request = Request(
        "https://coa.ascensionlogs.gg/api/reports/123?includeTrash=false",
        method="GET",
    )

    with opener(request) as response:
        assert response.status == 200
        assert response.headers.get_content_type() == "application/json"
        assert response.read1(5) == b'{"ok"'
        assert response.read1(100) == b":true}"
        assert response.read1(100) == b""

    assert page.urls == [request.full_url]


def test_browser_page_url_opener_rejects_cross_origin_and_non_get() -> None:
    opener = BrowserPageUrlOpener(_FakePage({}), allowed_host="coa.ascensionlogs.gg")

    with pytest.raises(URLError):
        opener(Request("https://example.invalid/api/reports/123", method="GET"))
    with pytest.raises(URLError):
        opener(Request("https://coa.ascensionlogs.gg/api/reports/123", method="POST"))


def test_browser_page_url_opener_surfaces_fetch_failure() -> None:
    opener = BrowserPageUrlOpener(
        _FakePage({"ok": False, "error": "TypeError: Failed to fetch"}),
        allowed_host="coa.ascensionlogs.gg",
    )

    with pytest.raises(URLError, match="Failed to fetch"):
        opener(Request("https://coa.ascensionlogs.gg/api/reports/123", method="GET"))


def test_browser_context_api_config_requires_exact_https_host(tmp_path: Path) -> None:
    BrowserContextApiConfig(
        start_url="https://coa.ascensionlogs.gg/",
        allowed_host="coa.ascensionlogs.gg",
        user_data_dir=tmp_path / "profile",
    ).validate()

    for start_url in (
        "http://coa.ascensionlogs.gg/",
        "https://example.invalid/",
    ):
        with pytest.raises(ValueError, match="start_url must be HTTPS"):
            BrowserContextApiConfig(
                start_url=start_url,
                allowed_host="coa.ascensionlogs.gg",
                user_data_dir=tmp_path / "profile",
            ).validate()
