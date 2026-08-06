from __future__ import annotations

from urllib.request import HTTPCookieProcessor

import pytest

from coa_workbench.collector.http_profile import (
    COA_FETCH_CONTEXT_V1,
    FETCH_CONTEXT_PROFILE_VERSION,
    SameOriginHttpSession,
)

BASE_URL = "https://coa.ascensionlogs.gg"


def test_fetch_context_profile_is_versioned_and_exact():
    assert COA_FETCH_CONTEXT_V1.version == FETCH_CONTEXT_PROFILE_VERSION
    assert COA_FETCH_CONTEXT_V1.as_headers() == {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"
        ),
        "Referer": "https://coa.ascensionlogs.gg/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }


def test_default_session_uses_one_in_memory_cookie_jar():
    session = SameOriginHttpSession(BASE_URL)

    cookie_handlers = [
        handler
        for handler in session._opener.handlers
        if isinstance(handler, HTTPCookieProcessor)
    ]
    assert len(cookie_handlers) == 1
    assert cookie_handlers[0].cookiejar is session._cookie_jar
    assert session.cookie_count == 0


def test_session_rejects_cross_origin_requests():
    session = SameOriginHttpSession(BASE_URL, opener=lambda *_args, **_kwargs: None)

    with pytest.raises(ValueError, match="cross-origin"):
        session.build_request("https://example.invalid/api/armory")


def test_safe_request_metadata_contains_names_but_not_values():
    session = SameOriginHttpSession(BASE_URL, opener=lambda *_args, **_kwargs: None)
    request = session.build_request(f"{BASE_URL}/api/armory/by-name/Name?realm=Realm")
    request.add_header("Cookie", "private-session=value")

    metadata = session.safe_request_metadata(request)

    assert metadata["http_profile_version"] == FETCH_CONTEXT_PROFILE_VERSION
    assert metadata["http_profile_header_names"] == list(COA_FETCH_CONTEXT_V1.header_names)
    assert "Cookie" in metadata["request_header_names"]
    assert "private-session=value" not in repr(metadata)
    assert "Chrome/138.0.0.0" not in repr(metadata)
