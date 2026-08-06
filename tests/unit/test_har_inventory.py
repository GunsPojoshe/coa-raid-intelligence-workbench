from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from coa_workbench.cli import app
from coa_workbench.collector.har_inventory import inspect_archived_payload, inventory_har
from coa_workbench.collector.raw_archive import RawArchive


def _entry(
    body: str | None,
    *,
    url: str = "https://coa.ascensionlogs.gg/api/unknown?token=secret&session=private&page=2",
    mime: str = "application/json",
    encoding: str | None = None,
) -> dict:
    content = {"mimeType": mime}
    if body is not None:
        content["text"] = body
    if encoding:
        content["encoding"] = encoding
    return {
        "startedDateTime": "2026-07-27T12:00:00Z",
        "request": {
            "method": "POST",
            "url": url,
            "headers": [{"name": "Authorization", "value": "Bearer request-secret"}],
            "cookies": [{"name": "auth", "value": "cookie-secret"}],
            "postData": {"text": "post-secret"},
        },
        "response": {
            "status": 200,
            "headers": [{"name": "x-private", "value": "response-secret"}],
            "cookies": [{"name": "response-cookie", "value": "response-cookie-secret"}],
            "content": content,
        },
    }


def _write_har(path: Path, entries: list) -> bytes:
    raw = json.dumps({"log": {"entries": entries}}).encode()
    path.write_bytes(raw)
    return raw


def test_inventory_covers_safe_content_types_errors_duplicates_and_determinism(tmp_path: Path) -> None:
    object_body = json.dumps({"items": [{"opaque": 1}], "z": True})
    array_body = json.dumps([{"value": 1}])
    encoded = base64.b64encode(object_body.encode()).decode()
    entries = [
        _entry(object_body),
        _entry(array_body),
        _entry("<html>hello</html>", mime="text/html"),
        _entry(None),
        _entry("{broken", mime="application/json"),
        _entry(encoded, encoding="base64"),
        _entry("ignored", url="https://other.example/path?token=foreign"),
        {"request": "broken", "response": {}},
    ]
    har_path = tmp_path / "Users" / "private-user" / "capture.har"
    har_path.parent.mkdir(parents=True)
    original = _write_har(har_path, entries)
    archive = RawArchive(tmp_path / "raw")

    first = inventory_har(
        har_path,
        archive=archive,
        source_code="coa_ascension_logs",
        allowed_host="coa.ascensionlogs.gg",
    )
    second = inventory_har(
        har_path,
        archive=archive,
        source_code="coa_ascension_logs",
        allowed_host="coa.ascensionlogs.gg",
    )

    assert har_path.read_bytes() == original
    assert [entry["candidate_label"] for entry in first["entries"][:6]] == [
        "json_object",
        "json_array",
        "html",
        "empty_body",
        "invalid_json",
        "json_object",
    ]
    assert first["entries"][5]["duplicate_payload"] is True
    assert first["entries"][6]["skip_reason"] == "hostname_not_allowed"
    assert first["entries"][7]["skip_reason"].startswith("malformed_entry:")
    assert first["entries"][0]["query_keys"] == ["page", "session", "token"]
    assert first["entries"][0]["top_level_keys"] == ["items", "z"]
    assert first["entries"][0]["candidate_collections"][0]["path"] == "/items"
    first_without_time = {key: value for key, value in first.items() if key != "generated_at"}
    second_without_time = {key: value for key, value in second.items() if key != "generated_at"}
    assert first_without_time == second_without_time
    rendered = json.dumps(first)
    for secret in (
        "secret",
        "private-user",
        "Authorization",
        "request-secret",
        "cookie-secret",
        "post-secret",
        "response-secret",
        "response-cookie-secret",
    ):
        assert secret not in rendered


def test_inventory_redacts_non_http_data_urls(tmp_path: Path) -> None:
    data_url = "data:image/png;base64,PRIVATE_BASE64_IMAGE_CONTENT"
    har_path = tmp_path / "capture.har"
    _write_har(har_path, [_entry("ignored", url=data_url, mime="image/png")])

    result = inventory_har(
        har_path,
        archive=RawArchive(tmp_path / "raw"),
        source_code="coa_ascension_logs",
        allowed_host="coa.ascensionlogs.gg",
    )

    entry = result["entries"][0]
    assert entry["route_path"] == "[non-http-url]"
    assert entry["query_keys"] == []
    assert entry["skip_reason"] == "unsupported_url_scheme"
    assert "PRIVATE_BASE64_IMAGE_CONTENT" not in json.dumps(result)


def test_inspect_archived_reads_gzip_json_by_hash_and_returns_relative_path(tmp_path: Path) -> None:
    root = tmp_path / "raw"
    capture = RawArchive(root).capture_bytes(
        b'{"rows":[{"opaque":1}]}',
        source_code="coa_ascension_logs",
        endpoint_code="har_discovered",
        request_key="GET:/unknown",
        content_type="application/json",
    )

    result = inspect_archived_payload(capture.payload_hash, raw_root=root)

    assert result["payload_hash"] == capture.payload_hash
    assert result["top_level_kind"] == "object"
    assert result["top_level_keys"] == ["rows"]
    assert result["payload_path"].startswith("source=coa_ascension_logs/")
    assert not Path(result["payload_path"]).is_absolute()
    assert gzip.open(capture.payload_path, "rb").read() == b'{"rows":[{"opaque":1}]}'


def test_inventory_cli_writes_safe_output_and_inspect_archived_cli(tmp_path: Path) -> None:
    har = tmp_path / "capture.har"
    _write_har(har, [_entry('{"items":[]}')])
    output = tmp_path / "inventory.json"
    raw = tmp_path / "raw"
    database = tmp_path / "coa.duckdb"
    runner = CliRunner()

    inventory_result = runner.invoke(
        app,
        [
            "inventory-har",
            str(har),
            "--output",
            str(output),
            "--raw-root",
            str(raw),
            "--database",
            str(database),
            "--migrations",
            "migrations",
            "--registry",
            "config/ascension_logs_sources.yaml",
        ],
    )

    assert inventory_result.exit_code == 0, inventory_result.output
    inventory = json.loads(output.read_text())
    payload_hash = inventory["entries"][0]["payload_hash"]
    assert payload_hash == hashlib.sha256(b'{"items":[]}').hexdigest()
    inspect_result = runner.invoke(
        app, ["inspect-archived", payload_hash, "--raw-root", str(raw)]
    )
    assert inspect_result.exit_code == 0, inspect_result.output
    assert json.loads(inspect_result.output)["payload_hash"] == payload_hash
