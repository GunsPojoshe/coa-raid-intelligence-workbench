from __future__ import annotations

from . import public_report_manifest as _implementation

TERMINAL_PRIVATE_SEARCH_KIND = "report_pagination_terminal_search_private_batch"

_implementation._TERMINAL_PRIVATE_KIND = TERMINAL_PRIVATE_SEARCH_KIND

capture_public_report_manifest = _implementation.capture_public_report_manifest

__all__ = ["TERMINAL_PRIVATE_SEARCH_KIND", "capture_public_report_manifest"]
