from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_cli() -> ModuleType:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "capture_public_report_manifest.py"
    spec = importlib.util.spec_from_file_location("capture_public_report_manifest_cli", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_refresh_terminal_removes_stale_checkpoint_before_manifest(
    tmp_path: Path, monkeypatch
) -> None:
    cli = _load_cli()
    checkpoint = tmp_path / "manifest.checkpoint.json"
    output = tmp_path / "manifest.json"
    private_output = tmp_path / "manifest.private.json"
    terminal_receipt = tmp_path / "terminal.json"
    terminal_private = tmp_path / "terminal.private.json"
    boundary_receipt = tmp_path / "boundary.json"
    boundary_private = tmp_path / "boundary.private.json"
    checkpoint.write_text("stale checkpoint", encoding="utf-8")
    output.write_text("stale receipt", encoding="utf-8")
    private_output.write_text("stale private manifest", encoding="utf-8")

    registry = object()
    archive = object()
    calls: list[str] = []

    monkeypatch.setattr(cli, "load_source_registry", lambda _path: registry)
    monkeypatch.setattr(cli, "RawArchive", lambda *_args, **_kwargs: archive)

    def fake_current_manifest(*args, **kwargs):
        assert args == (registry, archive)
        assert kwargs["boundary_receipt_path"] == boundary_receipt
        assert kwargs["boundary_private_path"] == boundary_private
        assert kwargs["terminal_receipt_path"] == terminal_receipt
        assert kwargs["terminal_private_path"] == terminal_private
        assert kwargs["checkpoint_path"] == checkpoint
        assert kwargs["private_output_path"] == private_output
        assert kwargs["receipt_output_path"] == output
        assert not checkpoint.exists()
        assert not output.exists()
        assert not private_output.exists()
        calls.append("current_manifest")
        return {
            "summary": {
                "completed_page_count": 1217,
                "report_occurrence_count": 6081,
                "unique_report_id_count": 6081,
            },
            "guild_field_summary": {"target_label_exact_match_report_count": 0},
        }

    monkeypatch.setattr(cli, "capture_current_public_report_manifest", fake_current_manifest)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "capture_public_report_manifest.py",
            "--refresh-terminal",
            "--terminal-receipt",
            str(terminal_receipt),
            "--terminal-private",
            str(terminal_private),
            "--boundary-receipt",
            str(boundary_receipt),
            "--boundary-private",
            str(boundary_private),
            "--checkpoint",
            str(checkpoint),
            "--private-output",
            str(private_output),
            "--output",
            str(output),
            "--mapping",
            str(tmp_path / "mapping.json"),
            "--registry",
            str(tmp_path / "registry.yaml"),
            "--raw-root",
            str(tmp_path / "raw"),
            "--database",
            str(tmp_path / "coa.duckdb"),
            "--migrations",
            str(tmp_path / "migrations"),
            "--request-delay-seconds",
            "0",
        ],
    )

    assert cli.main() == 0
    assert calls == ["current_manifest"]
