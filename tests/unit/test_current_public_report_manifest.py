from __future__ import annotations

from pathlib import Path

import pytest

from coa_workbench.collector import current_public_report_manifest as current


def _paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "boundary_receipt_path": tmp_path / "boundary.json",
        "boundary_private_path": tmp_path / "boundary.private.json",
        "terminal_receipt_path": tmp_path / "terminal.json",
        "terminal_private_path": tmp_path / "terminal.private.json",
        "mapping_path": tmp_path / "mapping.json",
        "checkpoint_path": tmp_path / "manifest.checkpoint.json",
        "private_output_path": tmp_path / "manifest.private.json",
        "receipt_output_path": tmp_path / "manifest.json",
    }


def test_refreshes_terminal_after_temporal_drift(tmp_path: Path, monkeypatch) -> None:
    paths = _paths(tmp_path)
    paths["checkpoint_path"].write_text("stale", encoding="utf-8")
    terminal_calls: list[bool] = []
    manifest_calls = 0

    def fake_terminal(*_args, **_kwargs):
        terminal_calls.append(paths["checkpoint_path"].exists())
        paths["terminal_receipt_path"].write_text("{}", encoding="utf-8")
        paths["terminal_private_path"].write_text("{}", encoding="utf-8")
        return {}

    def fake_manifest(*_args, **_kwargs):
        nonlocal manifest_calls
        manifest_calls += 1
        if manifest_calls == 1:
            raise ValueError("public report manifest page 1216 hasMore relation failed")
        return {"summary": {"completed_page_count": 1}}

    monkeypatch.setattr(current, "capture_report_pagination_terminal_search", fake_terminal)
    monkeypatch.setattr(current, "capture_public_report_manifest", fake_manifest)

    receipt = current.capture_current_public_report_manifest(object(), object(), **paths)

    assert receipt["summary"]["completed_page_count"] == 1
    assert manifest_calls == 2
    assert terminal_calls == [False]


def test_refreshes_terminal_after_terminal_page_count_drift(
    tmp_path: Path, monkeypatch
) -> None:
    paths = _paths(tmp_path)
    paths["checkpoint_path"].write_text("stale", encoding="utf-8")
    paths["private_output_path"].write_text("stale", encoding="utf-8")
    paths["receipt_output_path"].write_text("stale", encoding="utf-8")
    terminal_calls = 0
    manifest_calls = 0

    def fake_terminal(*_args, **_kwargs):
        nonlocal terminal_calls
        terminal_calls += 1
        assert not paths["checkpoint_path"].exists()
        assert not paths["private_output_path"].exists()
        assert not paths["receipt_output_path"].exists()
        return {}

    def fake_manifest(*_args, **_kwargs):
        nonlocal manifest_calls
        manifest_calls += 1
        if manifest_calls == 1:
            raise ValueError("public report manifest page 1217 expected 2 reports, got 3")
        return {"summary": {"completed_page_count": 1218}}

    monkeypatch.setattr(current, "capture_report_pagination_terminal_search", fake_terminal)
    monkeypatch.setattr(current, "capture_public_report_manifest", fake_manifest)

    receipt = current.capture_current_public_report_manifest(object(), object(), **paths)

    assert receipt["summary"]["completed_page_count"] == 1218
    assert manifest_calls == 2
    assert terminal_calls == 1


def test_preserves_checkpoint_for_transport_failure(tmp_path: Path, monkeypatch) -> None:
    paths = _paths(tmp_path)
    paths["checkpoint_path"].write_text("resume", encoding="utf-8")

    def unexpected_terminal(*_args, **_kwargs):
        raise AssertionError("terminal search must not run for a resumable transport failure")

    def failed_manifest(*_args, **_kwargs):
        raise ValueError("public report manifest page 300 capture was incomplete")

    monkeypatch.setattr(current, "capture_report_pagination_terminal_search", unexpected_terminal)
    monkeypatch.setattr(current, "capture_public_report_manifest", failed_manifest)

    with pytest.raises(ValueError, match="capture was incomplete"):
        current.capture_current_public_report_manifest(object(), object(), **paths)

    assert paths["checkpoint_path"].read_text(encoding="utf-8") == "resume"


def test_refreshes_terminal_before_new_manifest(tmp_path: Path, monkeypatch) -> None:
    paths = _paths(tmp_path)
    calls: list[str] = []

    def fake_terminal(*_args, **_kwargs):
        calls.append("terminal")
        return {}

    def fake_manifest(*_args, **_kwargs):
        calls.append("manifest")
        return {"summary": {"completed_page_count": 1}}

    monkeypatch.setattr(current, "capture_report_pagination_terminal_search", fake_terminal)
    monkeypatch.setattr(current, "capture_public_report_manifest", fake_manifest)

    current.capture_current_public_report_manifest(object(), object(), **paths)

    assert calls == ["terminal", "manifest"]


def test_stops_after_fixed_temporal_drift_attempts(tmp_path: Path, monkeypatch) -> None:
    paths = _paths(tmp_path)
    terminal_calls = 0
    manifest_calls = 0

    def fake_terminal(*_args, **_kwargs):
        nonlocal terminal_calls
        terminal_calls += 1
        return {}

    def drifting_manifest(*_args, **_kwargs):
        nonlocal manifest_calls
        manifest_calls += 1
        raise ValueError("public report manifest sentinel payload changed during capture")

    monkeypatch.setattr(current, "capture_report_pagination_terminal_search", fake_terminal)
    monkeypatch.setattr(current, "capture_public_report_manifest", drifting_manifest)

    with pytest.raises(ValueError, match="sentinel payload changed"):
        current.capture_current_public_report_manifest(
            object(), object(), manifest_max_attempts=2, **paths
        )

    assert terminal_calls == 2
    assert manifest_calls == 2
