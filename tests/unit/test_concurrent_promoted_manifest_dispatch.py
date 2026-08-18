from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector import public_report_manifest_compat as manifest_compat
from coa_workbench.collector.concurrent_promoted_public_report_manifest import (
    capture_promoted_manifest_concurrently,
)


def test_promoted_terminal_dispatches_to_concurrent_capture(
    tmp_path: Path, monkeypatch
) -> None:
    terminal_receipt = tmp_path / "terminal.json"
    terminal_receipt.write_text(
        json.dumps({"search_version": "report-pagination-terminal-search-v2"}),
        encoding="utf-8",
    )
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_concurrent(*args, **kwargs):
        calls.append((args, kwargs))
        return {"summary": {"capture_mode": "bounded_concurrent_prefill"}}

    monkeypatch.setattr(
        manifest_compat, "capture_promoted_manifest_concurrently", fake_concurrent
    )

    registry = object()
    archive = object()
    result = manifest_compat.capture_public_report_manifest(
        registry,
        archive,
        terminal_receipt_path=terminal_receipt,
    )

    assert result["summary"]["capture_mode"] == "bounded_concurrent_prefill"
    assert calls == [
        ((registry, archive), {"terminal_receipt_path": terminal_receipt})
    ]


def test_legacy_terminal_does_not_use_concurrent_capture(
    tmp_path: Path, monkeypatch
) -> None:
    terminal_receipt = tmp_path / "terminal.json"
    terminal_receipt.write_text(
        json.dumps({"search_version": "report-pagination-terminal-search-v1"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        manifest_compat,
        "capture_promoted_manifest_concurrently",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("legacy terminal must not use concurrent promoted capture")
        ),
    )
    monkeypatch.setattr(
        manifest_compat._implementation,
        "capture_public_report_manifest",
        lambda *_args, **_kwargs: {"summary": {"capture_mode": "legacy"}},
    )

    result = manifest_compat.capture_public_report_manifest(
        object(), object(), terminal_receipt_path=terminal_receipt
    )

    assert result["summary"]["capture_mode"] == "legacy"


@pytest.mark.parametrize("workers", [0, 1, 9])
def test_concurrent_capture_rejects_unsafe_worker_counts(workers: int) -> None:
    with pytest.raises(ValueError, match="manifest_workers must be between 2 and 8"):
        capture_promoted_manifest_concurrently(
            object(), object(), manifest_workers=workers
        )
