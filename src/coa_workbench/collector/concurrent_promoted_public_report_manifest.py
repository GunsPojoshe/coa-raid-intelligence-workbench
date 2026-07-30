from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Any

from . import public_report_manifest as _implementation
from .http_profile import SameOriginHttpSession

_DEFAULT_WORKERS = 4
_MAX_WORKERS = 8
_CHECKPOINT_FLUSH_INTERVAL = 8


class _LockedArchive:
    """Serialize archive mutations while allowing network reads to overlap."""

    def __init__(self, archive: Any, lock: Lock) -> None:
        self._archive = archive
        self._lock = lock

    def capture_bytes(self, *args: Any, **kwargs: Any):
        with self._lock:
            return self._archive.capture_bytes(*args, **kwargs)


def _required_path(kwargs: dict[str, Any], field_name: str) -> Path:
    value = kwargs.get(field_name)
    if not isinstance(value, Path):
        raise ValueError(f"concurrent promoted manifest requires {field_name}")
    return value


def _flush_checkpoint(
    checkpoint_path: Path,
    checkpoint: dict[str, Any],
    pages: dict[str, Any],
) -> None:
    checkpoint["updated_at"] = _implementation._generated_at()
    checkpoint["summary"] = {
        "completed_page_count": len(pages),
        "contains_source_scalar_values": True,
        "finalized": False,
        "capture_mode": "bounded_concurrent_prefill",
    }
    _implementation._write_json(checkpoint_path, checkpoint)


def capture_promoted_manifest_concurrently(
    registry: Any,
    archive: Any,
    *,
    manifest_workers: int = _DEFAULT_WORKERS,
    **kwargs: Any,
) -> dict[str, Any]:
    """Prefill promoted-limit manifest pages concurrently, then use canonical finalization."""
    if manifest_workers < 2 or manifest_workers > _MAX_WORKERS:
        raise ValueError(f"manifest_workers must be between 2 and {_MAX_WORKERS}")

    terminal_receipt_path = _required_path(kwargs, "terminal_receipt_path")
    terminal_private_path = _required_path(kwargs, "terminal_private_path")
    mapping_path = _required_path(kwargs, "mapping_path")
    checkpoint_path = _required_path(kwargs, "checkpoint_path")

    expected_guild_label = str(kwargs.get("expected_guild_label", "Argentum"))
    timeout_seconds = float(kwargs.get("timeout_seconds", 20.0))
    retry_count = int(kwargs.get("retry_count", 1))
    resume = bool(kwargs.get("resume", True))
    opener = kwargs.get("opener")
    progress_callback = kwargs.get("progress_callback")

    terminal_receipt, terminal_receipt_body = _implementation._load_object(
        terminal_receipt_path, "pagination terminal receipt"
    )
    terminal_private, terminal_private_body = _implementation._load_object(
        terminal_private_path, "private pagination terminal search"
    )
    mapping, mapping_body = _implementation._load_object(mapping_path, "public report mapping")
    terminal_page, terminal_count, limit = _implementation._validate_terminal_receipt(
        terminal_receipt, expected_guild_label
    )
    _implementation._validate_terminal_private(
        terminal_private,
        terminal_private_body,
        terminal_receipt,
        expected_guild_label,
        terminal_page,
    )
    _implementation._validate_mapping(mapping)
    sentinels = _implementation._sentinel_pages(terminal_page)

    if checkpoint_path.exists():
        if not resume:
            raise ValueError("public report manifest checkpoint exists but resume is disabled")
        checkpoint, _ = _implementation._load_object(
            checkpoint_path, "public report manifest checkpoint"
        )
        _implementation._validate_checkpoint(
            checkpoint,
            terminal_receipt_body=terminal_receipt_body,
            terminal_private_body=terminal_private_body,
            mapping_body=mapping_body,
            expected_guild_label=expected_guild_label,
            terminal_page=terminal_page,
            terminal_count=terminal_count,
            limit=limit,
            sentinel_pages=sentinels,
        )
    else:
        checkpoint = _implementation._new_checkpoint(
            terminal_receipt_path=terminal_receipt_path,
            terminal_receipt_body=terminal_receipt_body,
            terminal_private_path=terminal_private_path,
            terminal_private_body=terminal_private_body,
            mapping_path=mapping_path,
            mapping_body=mapping_body,
            expected_guild_label=expected_guild_label,
            terminal_page=terminal_page,
            terminal_count=terminal_count,
            limit=limit,
            sentinel_pages=sentinels,
        )
        _implementation._write_json(checkpoint_path, checkpoint)

    start_sentinels = _implementation._required_object(
        checkpoint.get("start_sentinels"), "start_sentinels"
    )
    pages = _implementation._required_object(checkpoint.get("pages"), "pages")

    sentinel_session = SameOriginHttpSession(registry.base_url, opener=opener)
    for index, page in enumerate(sentinels, start=1):
        key = str(page)
        if key not in start_sentinels:
            start_sentinels[key] = _implementation._capture_page(
                registry,
                archive,
                sentinel_session,
                page=page,
                terminal_page=terminal_page,
                terminal_count=terminal_count,
                limit=limit,
                phase="start_sentinel",
                timeout_seconds=timeout_seconds,
                retry_count=retry_count,
            )
            _implementation._write_json(checkpoint_path, checkpoint)
        _implementation._notify(progress_callback, "start_sentinel", index, len(sentinels))

    missing_pages = [page for page in range(1, terminal_page + 1) if str(page) not in pages]
    if missing_pages:
        archive_lock = Lock()
        locked_archive = _LockedArchive(archive, archive_lock)

        def capture_page(page: int) -> dict[str, Any]:
            session = SameOriginHttpSession(registry.base_url, opener=opener)
            return _implementation._capture_page(
                registry,
                locked_archive,
                session,
                page=page,
                terminal_page=terminal_page,
                terminal_count=terminal_count,
                limit=limit,
                phase="manifest_page",
                timeout_seconds=timeout_seconds,
                retry_count=retry_count,
            )

        futures: dict[Future[dict[str, Any]], int] = {}
        completed_since_flush = 0
        executor = ThreadPoolExecutor(max_workers=manifest_workers)
        try:
            futures = {executor.submit(capture_page, page): page for page in missing_pages}
            for future in as_completed(futures):
                page = futures[future]
                pages[str(page)] = future.result()
                completed_since_flush += 1
                if completed_since_flush >= _CHECKPOINT_FLUSH_INTERVAL:
                    _flush_checkpoint(checkpoint_path, checkpoint, pages)
                    completed_since_flush = 0
                _implementation._notify(
                    progress_callback, "manifest_page", len(pages), terminal_page
                )
        except BaseException:
            for future in futures:
                future.cancel()
            _flush_checkpoint(checkpoint_path, checkpoint, pages)
            executor.shutdown(wait=True, cancel_futures=True)
            raise
        else:
            executor.shutdown(wait=True)
            _flush_checkpoint(checkpoint_path, checkpoint, pages)

    canonical_kwargs = dict(kwargs)
    canonical_kwargs["resume"] = True
    canonical_kwargs["request_delay_seconds"] = 0.0
    return _implementation.capture_public_report_manifest(registry, archive, **canonical_kwargs)


__all__ = ["capture_promoted_manifest_concurrently"]
