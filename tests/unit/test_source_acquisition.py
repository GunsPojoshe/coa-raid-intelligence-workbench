from __future__ import annotations

from coa_workbench.collector.source_acquisition import classify_acquisition


def test_classify_managed_edge_challenge_without_exposing_body() -> None:
    body = (
        b"<!DOCTYPE html><html><script src='/cdn-cgi/challenge-platform/x'></script>"
        b"<iframe src='https://challenges.cloudflare.com/test'></iframe></html>"
    )
    result = classify_acquisition(
        status=403,
        content_type="text/html",
        body=body,
        error="HTTP 403: Forbidden",
    )
    assert result.outcome == "blocked"
    assert result.blocker_class == "managed_edge_challenge"
    assert result.error_class == "http_403"
    assert result.body_kind == "html"


def test_classify_valid_json_success_as_schema_candidate() -> None:
    result = classify_acquisition(
        status=200,
        content_type="application/json",
        body=b'{"rows":[]}',
    )
    assert result.outcome == "schema_candidate"
    assert result.blocker_class is None
    assert result.error_class is None
    assert result.body_kind == "json"
