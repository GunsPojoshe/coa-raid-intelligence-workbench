from pathlib import Path

import pytest

from coa_workbench.collector.public_api_credentials import load_public_api_key


def test_private_file_is_preferred_over_environment(tmp_path: Path) -> None:
    key_file = tmp_path / "key.txt"
    key_file.write_text("file-secret\n", encoding="utf-8")

    value = load_public_api_key(
        key_file=key_file,
        env_name="TEST_KEY",
        environ={"TEST_KEY": "environment-secret"},
    )

    assert value == "file-secret"


def test_environment_is_used_when_private_file_is_missing(tmp_path: Path) -> None:
    value = load_public_api_key(
        key_file=tmp_path / "missing.txt",
        env_name="TEST_KEY",
        environ={"TEST_KEY": " environment-secret "},
    )

    assert value == "environment-secret"


def test_utf16_private_file_is_supported(tmp_path: Path) -> None:
    key_file = tmp_path / "key.txt"
    key_file.write_text("file-secret\r\n", encoding="utf-16")

    assert load_public_api_key(key_file=key_file, environ={}) == "file-secret"


def test_missing_private_file_and_environment_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Missing CoA Logs API key"):
        load_public_api_key(
            key_file=tmp_path / "missing.txt",
            env_name="TEST_KEY",
            environ={},
        )
