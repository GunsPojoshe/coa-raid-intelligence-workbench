from __future__ import annotations

from typing import Any

from coa_workbench.collector import public_report_manifest as implementation
from coa_workbench.collector import public_report_manifest_compat as compatibility


def test_uses_real_terminal_private_kind_and_restores_previous_value(monkeypatch) -> None:
    observed_kinds: list[str] = []
    previous_kind = implementation._TERMINAL_PRIVATE_KIND

    def fake_capture(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        observed_kinds.append(implementation._TERMINAL_PRIVATE_KIND)
        return {"ok": True}

    monkeypatch.setattr(implementation, "capture_public_report_manifest", fake_capture)

    result = compatibility.capture_public_report_manifest()

    assert result == {"ok": True}
    assert observed_kinds == [compatibility.TERMINAL_PRIVATE_SEARCH_KIND]
    assert compatibility.TERMINAL_PRIVATE_SEARCH_KIND == (
        "report_pagination_terminal_search_private_batch"
    )
    assert implementation._TERMINAL_PRIVATE_KIND == previous_kind
