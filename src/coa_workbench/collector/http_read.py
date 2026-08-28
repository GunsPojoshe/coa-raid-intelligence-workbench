from __future__ import annotations

import ssl
from http.client import IncompleteRead, RemoteDisconnected
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request

OpenUrl = Callable[..., Any]
_READ_CHUNK_BYTES = 64 * 1024


def _read_body(response: Any, max_bytes: int | None) -> bytes:
    """Prefer HTTPResponse.read1 so chunked bodies do not wait for a huge read size."""
    read1 = getattr(response, "read1", None)
    if not callable(read1):
        return response.read(max_bytes + 1) if max_bytes is not None else response.read()

    chunks: list[bytes] = []
    total = 0
    while True:
        try:
            chunk = read1(_READ_CHUNK_BYTES)
        except IncompleteRead as exc:
            partial = exc.partial if isinstance(exc.partial, bytes) else b""
            raise IncompleteRead(b"".join(chunks) + partial, exc.expected) from exc
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)
        total += len(chunk)
        if max_bytes is not None and total > max_bytes:
            return b"".join(chunks)


def read_response_resilient(
    request: Request,
    *,
    timeout_seconds: float,
    opener: OpenUrl,
    max_bytes: int | None = None,
    retry_count: int = 1,
) -> tuple[int | None, str | None, bytes | None, str | None]:
    """Read one response without allowing a slow or incomplete body to abort a batch."""
    request.add_header("Accept-Encoding", "identity")
    request.add_header("Connection", "close")

    last_status: int | None = None
    last_content_type: str | None = None
    last_body: bytes | None = None
    last_error: str | None = None

    for attempt in range(retry_count + 1):
        try:
            with opener(
                request,
                timeout=timeout_seconds,
                context=ssl.create_default_context(),
            ) as response:
                last_status = int(response.status)
                last_content_type = response.headers.get_content_type()
                try:
                    body = _read_body(response, max_bytes)
                except TimeoutError:
                    last_error = (
                        f"read timeout after {timeout_seconds:g} seconds "
                        f"(attempt {attempt + 1}/{retry_count + 1})"
                    )
                    continue
                except IncompleteRead as exc:
                    last_body = exc.partial if isinstance(exc.partial, bytes) else None
                    last_error = (
                        f"incomplete HTTP response after {len(last_body or b'')} bytes "
                        f"(attempt {attempt + 1}/{retry_count + 1})"
                    )
                    continue
                if max_bytes is not None and len(body) > max_bytes:
                    return (
                        last_status,
                        last_content_type,
                        None,
                        f"response exceeded {max_bytes} bytes",
                    )
                return last_status, last_content_type, body, None
        except HTTPError as exc:
            last_status = exc.code
            last_content_type = exc.headers.get_content_type() if exc.headers else None
            try:
                body = _read_body(exc, max_bytes)
            except TimeoutError:
                body = None
                last_error = f"HTTP {exc.code} response read timed out: {exc.reason}"
            except IncompleteRead as incomplete:
                body = incomplete.partial if isinstance(incomplete.partial, bytes) else None
                last_error = f"HTTP {exc.code} response body was incomplete: {exc.reason}"
            else:
                if max_bytes is not None and len(body) > max_bytes:
                    body = None
                last_error = f"HTTP {exc.code}: {exc.reason}"
            return last_status, last_content_type, body, last_error
        except TimeoutError:
            last_error = (
                f"connection timeout after {timeout_seconds:g} seconds "
                f"(attempt {attempt + 1}/{retry_count + 1})"
            )
        except RemoteDisconnected:
            last_error = (
                "remote disconnected before response completed "
                f"(attempt {attempt + 1}/{retry_count + 1})"
            )
        except URLError as exc:
            last_error = (
                f"network error on attempt {attempt + 1}/{retry_count + 1}: {exc.reason}"
            )
        except OSError as exc:
            last_error = f"network I/O error on attempt {attempt + 1}/{retry_count + 1}: {exc}"

    return last_status, last_content_type, last_body, last_error or "response read failed"
