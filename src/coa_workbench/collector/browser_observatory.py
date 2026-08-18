from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from coa_workbench.collector.discovery_scenarios import validate_scenario_code
from coa_workbench.collector.interaction_session import ActionMarker, build_public_interaction_review
from coa_workbench.collector.network_observation import NetworkObservation

BROWSER_OBSERVATORY_VERSION = "browser-observatory-v1"
BROWSER_RUNTIME_REQUIREMENT = "playwright>=1.61,<2"
_ACTION_BINDING = "__coa_observe_action"
_ALLOWED_RESOURCE_TYPES = {"fetch", "xhr"}

_ACTION_INIT_SCRIPT = r"""
(() => {
  if (window.__coaBrowserObservatoryInstalled) return;
  window.__coaBrowserObservatoryInstalled = true;

  function domPath(element) {
    const parts = [];
    let current = element;
    while (current && current.nodeType === 1 && parts.length < 8) {
      let part = current.tagName.toLowerCase();
      if (current.id) {
        part += `#${current.id}`;
        parts.unshift(part);
        break;
      }
      const parent = current.parentElement;
      if (parent) {
        const peers = Array.from(parent.children).filter(
          child => child.tagName === current.tagName
        );
        if (peers.length > 1) {
          part += `:nth-of-type(${peers.indexOf(current) + 1})`;
        }
      }
      parts.unshift(part);
      current = parent;
    }
    return parts.join('>');
  }

  function payloadFor(element, eventType) {
    const selectedText = element instanceof HTMLSelectElement && element.selectedOptions.length
      ? element.selectedOptions[0].textContent
      : null;
    const text = (
      element.getAttribute('aria-label') ||
      element.getAttribute('title') ||
      selectedText ||
      element.textContent ||
      ''
    ).trim().replace(/\s+/g, ' ').slice(0, 160);
    return {
      event_type: eventType,
      observed_at_ms: Date.now(),
      control_identity: {
        tag: element.tagName.toLowerCase(),
        role: element.getAttribute('role'),
        type: element.getAttribute('type'),
        id: element.id || null,
        name: element.getAttribute('name'),
        dom_path: domPath(element),
      },
      private_label: text || null,
    };
  }

  document.addEventListener('change', event => {
    const element = event.target instanceof Element
      ? event.target.closest('select,input,textarea')
      : null;
    if (!element) return;
    void window.__coa_observe_action(payloadFor(element, 'change'));
  }, true);

  document.addEventListener('click', event => {
    if (!(event.target instanceof Element)) return;
    if (event.target.closest('select,input,textarea')) return;
    const element = event.target.closest(
      "button,a,[role='button'],[role='tab'],[role='option']," +
      "[role='menuitem'],[role='radio'],[role='checkbox'],summary"
    );
    if (!element) return;
    void window.__coa_observe_action(payloadFor(element, 'click'));
  }, true);
})();
"""


class PlaywrightUnavailableError(RuntimeError):
    pass


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _iso_from_epoch_ms(value: object) -> str:
    try:
        milliseconds = float(value)
    except (TypeError, ValueError):
        return _utc_now()
    return datetime.fromtimestamp(milliseconds / 1000, timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def _private_fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _header_value(message: Any, name: str) -> str | None:
    try:
        value = message.header_value(name)
    except Exception:
        return None
    return str(value) if value else None


class BrowserActionRecorder:
    def __init__(self) -> None:
        self.actions: list[ActionMarker] = []
        self._control_codes: dict[str, str] = {}

    def record_baseline(self) -> ActionMarker:
        action = ActionMarker(
            action_id=f"a{len(self.actions) + 1:04d}",
            observed_at=_utc_now(),
            kind="baseline",
            private_label=None,
            control_code="baseline",
            transition_code="baseline",
        )
        self.actions.append(action)
        return action

    def record(
        self,
        payload: Mapping[str, Any],
        *,
        page_url: str | None = None,
    ) -> ActionMarker:
        event_type = str(payload.get("event_type") or "unknown").casefold()
        identity = payload.get("control_identity")
        if not isinstance(identity, Mapping):
            identity = {}
        fingerprint = _private_fingerprint(dict(identity))
        control_code = self._control_codes.get(fingerprint)
        if control_code is None:
            control_code = f"control_{len(self._control_codes) + 1:03d}"
            self._control_codes[fingerprint] = control_code

        private_payload = {
            "control_identity": dict(identity),
            "private_label": payload.get("private_label"),
            "page_url": page_url,
        }
        action = ActionMarker(
            action_id=f"a{len(self.actions) + 1:04d}",
            observed_at=_iso_from_epoch_ms(payload.get("observed_at_ms")),
            kind=event_type,
            private_label=_canonical_json(private_payload),
            control_code=control_code,
            transition_code="change" if event_type == "change" else "activate",
        )
        self.actions.append(action)
        return action

    def private_manifest(self) -> dict[str, object]:
        return {
            "manifest_version": BROWSER_OBSERVATORY_VERSION,
            "actions": [
                {
                    "action_id": action.action_id,
                    "observed_at": action.observed_at,
                    "kind": action.kind,
                    "control_code": action.control_code,
                    "transition_code": action.transition_code,
                    "private_label": action.private_label,
                }
                for action in self.actions
            ],
        }


class LiveNetworkRecorder:
    def __init__(self, *, allowed_host: str, api_prefix: str = "/api/") -> None:
        self.allowed_host = allowed_host
        self.api_prefix = api_prefix
        self.observations: list[NetworkObservation] = []
        self._started_at: dict[int, str] = {}

    def _accepted(self, request: Any) -> bool:
        url = str(request.url)
        parts = urlsplit(url)
        resource_type = str(request.resource_type or "").casefold()
        return (
            parts.scheme == "https"
            and parts.hostname == self.allowed_host
            and parts.path.startswith(self.api_prefix)
            and resource_type in _ALLOWED_RESOURCE_TYPES
        )

    def on_request(self, request: Any) -> None:
        if self._accepted(request):
            self._started_at[id(request)] = _utc_now()

    def _append(self, request: Any, *, failed: bool) -> None:
        if not self._accepted(request):
            return
        observed_at = self._started_at.pop(id(request), _utc_now())
        response = None
        if not failed:
            try:
                response = request.response()
            except Exception:
                response = None

        response_body = None
        if response is not None:
            try:
                response_body = response.body()
            except Exception:
                response_body = None

        try:
            request_body = request.post_data_buffer
        except Exception:
            request_body = None

        self.observations.append(
            NetworkObservation(
                ordinal=len(self.observations),
                observed_at=observed_at,
                method=str(request.method).upper(),
                url=str(request.url),
                status=None if response is None else int(response.status),
                request_content_type=_header_value(request, "content-type"),
                response_content_type=None
                if response is None
                else _header_value(response, "content-type"),
                request_body=request_body,
                response_body=response_body,
                resource_type=str(request.resource_type) if request.resource_type else None,
                source_kind="playwright",
            )
        )

    def on_requestfinished(self, request: Any) -> None:
        self._append(request, failed=False)

    def on_requestfailed(self, request: Any) -> None:
        self._append(request, failed=True)


@dataclass(frozen=True, slots=True)
class BrowserObservatoryConfig:
    start_url: str
    allowed_host: str
    user_data_dir: Path
    private_session_root: Path
    public_output_dir: Path
    api_prefix: str = "/api/"
    source_code: str = "coa_ascension_logs"
    scenario_code: str = "unassigned"
    trace_enabled: bool = True

    def validate(self) -> None:
        parts = urlsplit(self.start_url)
        if parts.scheme != "https" or parts.hostname != self.allowed_host:
            raise ValueError("start_url must be HTTPS and match allowed_host")
        if not self.api_prefix.startswith("/"):
            raise ValueError("api_prefix must start with /")
        validate_scenario_code(self.source_code)
        validate_scenario_code(self.scenario_code)


def _load_sync_playwright() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise PlaywrightUnavailableError(
            "Browser Observatory requires Playwright. Install the local runtime with "
            f"uv pip install '{BROWSER_RUNTIME_REQUIREMENT}' and then run "
            "uv run playwright install chromium."
        ) from exc
    return sync_playwright


def _pump_browser_events(page: Any, *, interval_ms: float = 250) -> None:
    try:
        while True:
            page.wait_for_timeout(interval_ms)
    except KeyboardInterrupt:
        return


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run_browser_profile_bootstrap(config: BrowserObservatoryConfig) -> dict[str, object]:
    config.validate()
    config.user_data_dir.mkdir(parents=True, exist_ok=True)
    sync_playwright = _load_sync_playwright()

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            config.user_data_dir,
            headless=False,
            no_viewport=True,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(config.start_url, wait_until="domcontentloaded")
        print("Dedicated Browser Observatory profile is open. Authenticate if needed.")
        print("Return to this terminal and press Ctrl+C when profile setup is complete.")
        _pump_browser_events(page)
        context.close()

    return {
        "browser_observatory_version": BROWSER_OBSERVATORY_VERSION,
        "profile_bootstrap_completed": True,
        "evidence_capture_performed": False,
        "private_profile_path_included": False,
    }


def run_browser_observatory(config: BrowserObservatoryConfig) -> dict[str, object]:
    config.validate()
    session_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    session_dir = config.private_session_root / session_id
    session_dir.mkdir(parents=True, exist_ok=False)
    config.user_data_dir.mkdir(parents=True, exist_ok=True)
    config.public_output_dir.mkdir(parents=True, exist_ok=True)

    har_path = session_dir / "network.har"
    trace_path = session_dir / "trace.zip"
    private_actions_path = session_dir / "actions-private.json"
    public_review_path = config.public_output_dir / f"coa-browser-observatory-{session_id}.json"

    action_recorder = BrowserActionRecorder()
    network_recorder = LiveNetworkRecorder(
        allowed_host=config.allowed_host,
        api_prefix=config.api_prefix,
    )
    sync_playwright = _load_sync_playwright()

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            config.user_data_dir,
            headless=False,
            no_viewport=True,
            artifacts_dir=session_dir,
            record_har_path=har_path,
            record_har_content="embed",
            record_har_mode="full",
            record_har_omit_content=False,
        )

        def on_action(source: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
            page = source.get("page")
            page_url = str(page.url) if page is not None else None
            action_recorder.record(payload, page_url=page_url)

        context.expose_binding(_ACTION_BINDING, on_action)
        context.add_init_script(_ACTION_INIT_SCRIPT)
        context.on("request", network_recorder.on_request)
        context.on("requestfinished", network_recorder.on_requestfinished)
        context.on("requestfailed", network_recorder.on_requestfailed)

        tracing_started = False
        if config.trace_enabled:
            context.tracing.start(screenshots=True, snapshots=True, sources=False)
            tracing_started = True

        page = context.pages[0] if context.pages else context.new_page()
        action_recorder.record_baseline()
        page.goto(config.start_url, wait_until="domcontentloaded")
        print("Browser Observatory is active. Use the browser normally.")
        print("Return to this terminal and press Ctrl+C when the discovery session is complete.")
        _pump_browser_events(page)

        review = build_public_interaction_review(
            tuple(action_recorder.actions),
            tuple(network_recorder.observations),
        )
        review["source"] = {
            "observation_source": "playwright",
            "browser_observatory_version": BROWSER_OBSERVATORY_VERSION,
            "network_request_count": len(network_recorder.observations),
            "action_count": len(action_recorder.actions),
            "source_code": config.source_code,
            "scenario_code": config.scenario_code,
            "har_recorded": True,
            "trace_recorded": tracing_started,
            "private_paths_included": False,
            "browser_navigation_performed": True,
            "direct_source_api_requests_performed_by_observatory": False,
        }
        _write_json(private_actions_path, action_recorder.private_manifest())
        _write_json(public_review_path, review)

        if tracing_started:
            context.tracing.stop(path=trace_path)
        context.close()

    return {
        "session_id": session_id,
        "public_review_path": str(public_review_path),
        "private_session_dir": str(session_dir),
        "action_count": len(action_recorder.actions),
        "network_request_count": len(network_recorder.observations),
    }


__all__ = [
    "BROWSER_OBSERVATORY_VERSION",
    "BROWSER_RUNTIME_REQUIREMENT",
    "BrowserActionRecorder",
    "BrowserObservatoryConfig",
    "LiveNetworkRecorder",
    "PlaywrightUnavailableError",
    "_pump_browser_events",
    "run_browser_observatory",
    "run_browser_profile_bootstrap",
]
