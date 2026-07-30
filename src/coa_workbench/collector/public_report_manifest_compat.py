from __future__ import annotations

from typing import Any

from . import public_report_manifest as _implementation

TERMINAL_PRIVATE_SEARCH_KIND = "report_pagination_terminal_search_private_batch"


def capture_public_report_manifest(*args: Any, **kwargs: Any) -> dict[str, Any]:
    previous_kind = _implementation._TERMINAL_PRIVATE_KIND
    _implementation._TERMINAL_PRIVATE_KIND = TERMINAL_PRIVATE_SEARCH_KIND
    try:
        return _implementation.capture_public_report_manifest(*args, **kwargs)
    finally:
        _implementation._TERMINAL_PRIVATE_KIND = previous_kind


__all__ = ["TERMINAL_PRIVATE_SEARCH_KIND", "capture_public_report_manifest"]
