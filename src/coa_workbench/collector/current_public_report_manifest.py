from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .public_report_manifest_compat import capture_public_report_manifest
from .raw_archive import RawArchive
from .report_pagination_terminal_search import capture_report_pagination_terminal_search
from .source_registry import SourceRegistry

StatusCallback = Callable[[str], None]
ProgressCallback = Callable[[str, int, int], None]

_TEMPORAL_DRIFT_MARKERS = (
    "hasMore relation failed",
    "report count mismatch",
    "sentinel payload changed during capture",
    "sweep does not match sentinel payload",
    "aggregate report count mismatch",
    "cross-page duplicate report ids",
)


def _is_temporal_manifest_drift(error: ValueError) -> bool:
    message = str(error)
    return any(marker in message for marker in _TEMPORAL_DRIFT_MARKERS)


def _remove_manifest_state(
    checkpoint_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
) -> None:
    for path in (checkpoint_path, private_output_path, receipt_output_path):
        path.unlink(missing_ok=True)


def capture_current_public_report_manifest(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    boundary_receipt_path: Path,
    boundary_private_path: Path,
    terminal_receipt_path: Path,
    terminal_private_path: Path,
    mapping_path: Path,
    checkpoint_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    terminal_max_requests: int = 16,
    manifest_max_attempts: int = 3,
    timeout_seconds: float = 20.0,
    retry_count: int = 1,
    request_delay_seconds: float = 0.15,
    opener: Any | None = None,
    progress_callback: ProgressCallback | None = None,
    status_callback: StatusCallback | None = None,
) -> dict[str, Any]:
    """Resume a stable manifest or refresh its terminal contract after temporal drift."""
    if manifest_max_attempts < 1 or manifest_max_attempts > 5:
        raise ValueError("manifest_max_attempts must be between 1 and 5")

    def status(message: str) -> None:
        if status_callback is not None:
            status_callback(message)

    use_existing_checkpoint = checkpoint_path.exists()
    last_drift_error: ValueError | None = None

    for attempt in range(1, manifest_max_attempts + 1):
        if use_existing_checkpoint:
            status(f"manifest attempt {attempt}: resuming existing checkpoint")
        else:
            status(f"manifest attempt {attempt}: refreshing terminal contract")
            capture_report_pagination_terminal_search(
                registry,
                archive,
                boundary_receipt_path=boundary_receipt_path,
                boundary_private_path=boundary_private_path,
                private_output_path=terminal_private_path,
                receipt_output_path=terminal_receipt_path,
                expected_guild_label=expected_guild_label,
                max_requests=terminal_max_requests,
                timeout_seconds=timeout_seconds,
                retry_count=retry_count,
                opener=opener,
            )

        try:
            return capture_public_report_manifest(
                registry,
                archive,
                terminal_receipt_path=terminal_receipt_path,
                terminal_private_path=terminal_private_path,
                mapping_path=mapping_path,
                checkpoint_path=checkpoint_path,
                private_output_path=private_output_path,
                receipt_output_path=receipt_output_path,
                expected_guild_label=expected_guild_label,
                timeout_seconds=timeout_seconds,
                retry_count=retry_count,
                request_delay_seconds=request_delay_seconds,
                resume=True,
                opener=opener,
                progress_callback=progress_callback,
            )
        except ValueError as error:
            if not _is_temporal_manifest_drift(error):
                raise
            last_drift_error = error
            if attempt >= manifest_max_attempts:
                raise
            status(
                "public-report pagination changed during capture; "
                "discarding only stale manifest state and retrying"
            )
            _remove_manifest_state(checkpoint_path, private_output_path, receipt_output_path)
            use_existing_checkpoint = False

    if last_drift_error is not None:
        raise last_drift_error
    raise RuntimeError("public report manifest orchestration ended without a result")


__all__ = ["capture_current_public_report_manifest"]
