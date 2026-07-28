from __future__ import annotations

from http.client import IncompleteRead
from urllib.request import Request

from coa_workbench.collector.http_read import read_response_resilient


class _Headers:
    def get_content_type(self) -> str:
        return "application/json"


class _Response:
    def __init__(self, chunks: list[bytes], *, incomplete: bool = False) -> None:
        self.status = 200
        self.headers = _Headers()
        self._chunks = iter(chunks)
        self._incomplete = incomplete

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read1(self, _size: int) -> bytes:
        try:
            return next(self._chunks)
        except StopIteration:
            if self._incomplete:
                raise IncompleteRead(b"", 0)
            return b""


class _SequenceOpener:
    def __init__(self, responses: list[_Response]) -> None:
        self._responses = iter(responses)
        self.calls = 0

    def __call__(self, _request, **_kwargs):
        self.calls += 1
        return next(self._responses)


def test_incomplete_chunked_response_is_retried():
    opener = _SequenceOpener(
        [
            _Response([b'{"success":'], incomplete=True),
            _Response([b'{"success":true}']),
        ]
    )

    status, content_type, body, error = read_response_resilient(
        Request("https://example.test/api"),
        timeout_seconds=3,
        opener=opener,
    )

    assert status == 200
    assert content_type == "application/json"
    assert body == b'{"success":true}'
    assert error is None
    assert opener.calls == 2


def test_final_incomplete_response_returns_observed_bytes_and_error():
    opener = _SequenceOpener(
        [
            _Response([b'{"success":true}'], incomplete=True),
            _Response([b'{"success":true}'], incomplete=True),
        ]
    )

    status, content_type, body, error = read_response_resilient(
        Request("https://example.test/api"),
        timeout_seconds=3,
        opener=opener,
    )

    assert status == 200
    assert content_type == "application/json"
    assert body == b'{"success":true}'
    assert error == "incomplete HTTP response after 16 bytes (attempt 2/2)"
    assert opener.calls == 2
