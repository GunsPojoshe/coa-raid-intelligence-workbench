from __future__ import annotations

import json
from pathlib import Path

from coa_workbench.collector.public_api_archive import load_latest_public_api_capture
from coa_workbench.collector.public_api_stats_capture import (
    capture_public_api_stats,
    public_api_stats_capture_to_dict,
)
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_registry import load_source_registry


class _Headers:
    def get_content_type(self) -> str:
        return "application/json"


class _Response:
    def __init__(self, payload: object) -> None:
        self.status = 200
        self.headers = _Headers()
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self._body if size is None or size < 0 else self._body[:size]


def test_statistics_capture_keeps_query_values_only_in_private_archive_metadata(
    tmp_path: Path,
) -> None:
    registry = load_source_registry(Path("config/coa_public_api_sources.yaml"))
    raw_root = tmp_path / "raw"
    payload = {
        "success": True,
        "phase": 12,
        "difficulty": "all",
        "metric": "avg_dps",
        "bracket": "all",
        "damage_mode": "standard",
        "statistics": {},
    }

    result = capture_public_api_stats(
        registry,
        RawArchive(raw_root),
        endpoint_code="public_api_statistics",
        api_key="local-secret-key",
        query={
            "phase": 12,
            "difficulty": "all",
            "metric": "avg_dps",
            "bracket": "all",
            "damageMode": "standard",
            "role": "dps",
        },
        opener=lambda _request, **_kwargs: _Response(payload),
    )
    archived = load_latest_public_api_capture(
        raw_root,
        source_code=registry.source_code,
        endpoint_code="public_api_statistics",
    )

    assert archived.query_keys == (
        "phase",
        "difficulty",
        "metric",
        "bracket",
        "damageMode",
        "role",
    )
    assert archived.query_value_mapping() == {
        "phase": "12",
        "difficulty": "all",
        "metric": "avg_dps",
        "bracket": "all",
        "damageMode": "standard",
        "role": "dps",
    }

    public_receipt = json.dumps(public_api_stats_capture_to_dict(result))
    assert "local-secret-key" not in public_receipt
    assert '"12"' not in public_receipt
    assert '"dps"' not in public_receipt
    assert '"standard"' not in public_receipt
