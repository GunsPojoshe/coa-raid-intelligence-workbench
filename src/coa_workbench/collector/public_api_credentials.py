from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

DEFAULT_PUBLIC_API_KEY_ENV = "COA_LOGS_API_KEY"
DEFAULT_PUBLIC_API_KEY_FILE = Path("data/private/coa-logs-api-key.txt")


def _prepare_secret(value: str) -> str:
    prepared = value.strip()
    if not prepared:
        raise ValueError("API key is empty")
    if "\r" in prepared or "\n" in prepared:
        raise ValueError("API key cannot contain embedded line breaks")
    return prepared


def _read_secret_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    payload = path.read_bytes()
    if not payload:
        return None
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            text = payload.decode(encoding)
        except UnicodeDecodeError:
            continue
        if text.strip():
            return _prepare_secret(text)
    raise ValueError(f"API key file cannot be decoded safely: {path}")


def load_public_api_key(
    *,
    key_file: Path | None = DEFAULT_PUBLIC_API_KEY_FILE,
    env_name: str = DEFAULT_PUBLIC_API_KEY_ENV,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Load a local API key without accepting it through CLI/query arguments.

    The ignored private file is preferred so rotating the file takes effect immediately even if an
    older environment variable remains in the shell. The environment variable is a fallback for
    ephemeral shells and automated local runs.
    """

    if key_file is not None:
        file_value = _read_secret_file(key_file)
        if file_value is not None:
            return file_value

    active_environ = os.environ if environ is None else environ
    env_value = active_environ.get(env_name, "")
    if env_value.strip():
        return _prepare_secret(env_value)

    location = str(key_file) if key_file is not None else "<disabled>"
    raise ValueError(
        "Missing CoA Logs API key. Store it in the ignored local file "
        f"{location!r} or set environment variable {env_name!r}."
    )


__all__ = [
    "DEFAULT_PUBLIC_API_KEY_ENV",
    "DEFAULT_PUBLIC_API_KEY_FILE",
    "load_public_api_key",
]
