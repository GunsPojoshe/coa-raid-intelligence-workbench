from __future__ import annotations

import json
import signal
from pathlib import Path

from coa_workbench.collector.browser_observatory import (
    BrowserActionRecorder,
    BrowserObservatoryConfig,
    LiveNetworkRecorder,
)
from coa_workbench.collector.interaction_session import build_public_interaction_review


class _FakeResponse:
    def __init__(self, body: bytes, status: int = 200) -> None:
        self._body = body
        self.status = status

    def body(self) -> bytes:
        return self._body

    def header_value(self, name: str) -> str | None:
        return "application/json" if name.casefold() == "content-type" else None


class _FakeRequest:
    def __init__(
        self,
        url: str,
        *,
        resource_type: str = "xhr",
        body: bytes | None = None,
        response: _FakeResponse | None = None,
    ) -> None:
        self.url = url
        self.method = "POST" if body is not None else "GET"
        self.resource_type = resource_type
        self.post_data_buffer = body
        self._response = response

    def response(self) -> _FakeResponse | None:
        return self._response

    def header_value(self, name: str) -> str | None:
        if name.casefold() == "content-type" and self.post_data_buffer is not None:
            return "application/json"
        return None


def test_action_recorder_uses_session_control_codes_without_public_private_labels() -> None:
    recorder = BrowserActionRecorder()
    baseline = recorder.record_baseline()
    first = recorder.record(
        {
            "event_type": "change",
            "observed_at_ms": 1_787_094_001_000,
            "control_identity": {"tag": "select", "id": "difficulty"},
            "private_label": "Private Difficulty A",
        },
        page_url="https://coa.ascensionlogs.gg/reports/private-report",
    )
    second = recorder.record(
        {
            "event_type": "change",
            "observed_at_ms": 1_787_094_002_000,
            "control_identity": {"tag": "select", "id": "difficulty"},
            "private_label": "Private Difficulty B",
        },
        page_url="https://coa.ascensionlogs.gg/reports/private-report",
    )
    third = recorder.record(
        {
            "event_type": "click",
            "observed_at_ms": 1_787_094_003_000,
            "control_identity": {"tag": "button", "id": "boss"},
            "private_label": "Private Boss",
        }
    )

    assert baseline.control_code == "baseline"
    assert first.control_code == "control_001"
    assert second.control_code == "control_001"
    assert third.control_code == "control_002"
    assert first.transition_code == "change"
    assert third.transition_code == "activate"

    public = build_public_interaction_review(recorder.actions, ())
    rendered = json.dumps(public, sort_keys=True)
    assert "Private Difficulty A" not in rendered
    assert "Private Difficulty B" not in rendered
    assert "Private Boss" not in rendered
    assert "private-report" not in rendered
    assert "control_001" in rendered


def test_live_network_recorder_filters_scope_and_preserves_private_values_only_in_model() -> None:
    recorder = LiveNetworkRecorder(allowed_host="coa.ascensionlogs.gg")
    accepted = _FakeRequest(
        "https://coa.ascensionlogs.gg/api/reports/123?difficulty=private-value",
        body=b'{"encounterId":456}',
        response=_FakeResponse(b'{"player":"Private Player","amount":42}'),
    )
    wrong_host = _FakeRequest(
        "https://example.invalid/api/reports/123",
        response=_FakeResponse(b"{}"),
    )
    document = _FakeRequest(
        "https://coa.ascensionlogs.gg/api/reports/123",
        resource_type="document",
        response=_FakeResponse(b"{}"),
    )

    for request in (accepted, wrong_host, document):
        recorder.on_request(request)
        recorder.on_requestfinished(request)

    assert len(recorder.observations) == 1
    observation = recorder.observations[0]
    assert observation.request_body == b'{"encounterId":456}'
    assert observation.response_body == b'{"player":"Private Player","amount":42}'
    assert observation.source_kind == "playwright"

    rendered = json.dumps(observation.public_summary(), sort_keys=True)
    assert "private-value" not in rendered
    assert "Private Player" not in rendered
    assert '"encounterId": 456' not in rendered
    assert "/api/reports/123" not in rendered
    assert "difficulty" in rendered
    assert "encounterId" in rendered


def test_failed_network_request_is_retained_without_response() -> None:
    recorder = LiveNetworkRecorder(allowed_host="coa.ascensionlogs.gg")
    request = _FakeRequest("https://coa.ascensionlogs.gg/api/reports/123")

    recorder.on_request(request)
    recorder.on_requestfailed(request)

    assert len(recorder.observations) == 1
    assert recorder.observations[0].status is None
    assert recorder.observations[0].response_body is None


def test_browser_observatory_config_requires_https_exact_host(tmp_path: Path) -> None:
    base = dict(
        allowed_host="coa.ascensionlogs.gg",
        user_data_dir=tmp_path / "profile",
        private_session_root=tmp_path / "sessions",
        public_output_dir=tmp_path / "out",
    )
    BrowserObservatoryConfig(
        start_url="https://coa.ascensionlogs.gg/reports",
        **base,
    ).validate()

    for start_url in (
        "http://coa.ascensionlogs.gg/reports",
        "https://example.invalid/reports",
    ):
        config = BrowserObservatoryConfig(start_url=start_url, **base)
        try:
            config.validate()
        except ValueError as exc:
            assert str(exc) == "start_url must be HTTPS and match allowed_host"
        else:
            raise AssertionError("expected ValueError")


def test_browser_event_pump_converts_sigint_to_graceful_stop(monkeypatch) -> None:
    from coa_workbench.collector.browser_observatory import _pump_browser_events

    active_handler = signal.default_int_handler
    installed_handlers: list[object] = []

    def fake_signal(signum: int, handler: object) -> object:
        nonlocal active_handler
        assert signum == signal.SIGINT
        previous = active_handler
        active_handler = handler
        installed_handlers.append(handler)
        return previous

    monkeypatch.setattr(signal, "signal", fake_signal)

    class _FakePage:
        def __init__(self) -> None:
            self.calls: list[float] = []

        def wait_for_timeout(self, timeout: float) -> None:
            self.calls.append(timeout)
            if len(self.calls) == 3:
                assert callable(active_handler)
                active_handler(signal.SIGINT, None)

    page = _FakePage()
    _pump_browser_events(page, interval_ms=125)

    assert page.calls == [125, 125, 125]
    assert installed_handlers[0] is not signal.default_int_handler
    assert installed_handlers[-1] is signal.default_int_handler


def test_browser_event_pump_keeps_keyboard_interrupt_fallback() -> None:
    from coa_workbench.collector.browser_observatory import _pump_browser_events

    class _FakePage:
        def wait_for_timeout(self, _timeout: float) -> None:
            raise KeyboardInterrupt

    _pump_browser_events(_FakePage(), interval_ms=125)


def test_browser_observatory_config_rejects_non_public_scenario_code(tmp_path: Path) -> None:
    config = BrowserObservatoryConfig(
        start_url="https://coa.ascensionlogs.gg/reports",
        allowed_host="coa.ascensionlogs.gg",
        user_data_dir=tmp_path / "profile",
        private_session_root=tmp_path / "sessions",
        public_output_dir=tmp_path / "out",
        scenario_code="Private Scenario",
    )

    try:
        config.validate()
    except ValueError as exc:
        assert str(exc) == "scenario_code must be a lowercase public-safe code"
    else:
        raise AssertionError("expected ValueError")
