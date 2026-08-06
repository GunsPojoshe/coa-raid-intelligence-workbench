from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

MAX_TEXT_BLOB_BYTES = 5 * 1024 * 1024

FORBIDDEN_SUFFIXES = {
    ".duckdb",
    ".har",
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
}
FORBIDDEN_BASENAMES = {
    ".env",
    "cookies.json",
    "id_ed25519",
    "id_rsa",
}
LOCAL_ONLY_PREFIXES = (
    "artifacts/",
    "data/backups/",
    "data/exchange/in/",
    "data/exchange/out/",
    "data/extracted/",
    "data/logs/",
    "data/normalized/",
    "data/parquet/",
    "data/raw/",
    "data/reconstructed/",
    "data/warehouse/",
    "exports/",
    "workbook/working/",
)
ALLOWED_LOCAL_ONLY_FILES = {f"{prefix}.gitkeep" for prefix in LOCAL_ONLY_PREFIXES}

# Construct token prefixes in pieces so this scanner does not match its own source.
SECRET_PATTERNS = {
    "private_key_material": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "github_classic_token": re.compile(b"g" + rb"h[pousr]_[A-Za-z0-9]{36,255}"),
    "github_fine_grained_token": re.compile(b"github" + rb"_pat_[A-Za-z0-9_]{50,255}"),
    "openai_api_key": re.compile(b"s" + rb"k-(?:proj-)?[A-Za-z0-9_-]{32,255}"),
    "aws_access_key_id": re.compile(
        rb"(?:A3T[A-Z0-9]|AKIA|ASIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASCA)[A-Z0-9]{16}"
    ),
    "slack_token": re.compile(b"xo" + rb"x[baprs]-[A-Za-z0-9-]{20,255}"),
}


@dataclass(frozen=True, slots=True)
class Finding:
    kind: str
    rule_id: str
    object_id: str
    path: str
    line_number: int | None = None


def _git(*args: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr}")
    return completed.stdout


def _is_forbidden_path(path_text: str) -> str | None:
    normalized = path_text.replace("\\", "/").lstrip("./")
    path = PurePosixPath(normalized)
    basename = path.name.casefold()
    suffix = path.suffix.casefold()

    if normalized in ALLOWED_LOCAL_ONLY_FILES:
        return None
    if basename == ".env.example":
        return None
    if basename in FORBIDDEN_BASENAMES or basename.startswith(".env."):
        return "forbidden_environment_or_credential_file"
    if basename.endswith(".private.json"):
        return "private_json_artifact"
    if suffix in FORBIDDEN_SUFFIXES or basename.endswith(".duckdb.wal"):
        return "forbidden_sensitive_file_type"
    if any(normalized.startswith(prefix) for prefix in LOCAL_ONLY_PREFIXES):
        return "local_only_path_committed"
    return None


def _line_number(body: bytes, offset: int) -> int:
    return body.count(b"\n", 0, offset) + 1


def _iter_reachable_objects() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for raw_line in (
        _git("rev-list", "--objects", "--all")
        .decode("utf-8", errors="surrogateescape")
        .splitlines()
    ):
        object_id, separator, path = raw_line.partition(" ")
        rows.append((object_id, path if separator else ""))
    return rows


def audit_repository() -> dict[str, object]:
    findings: list[Finding] = []
    objects = _iter_reachable_objects()
    paths_by_object: dict[str, set[str]] = {}
    for object_id, path in objects:
        if path:
            paths_by_object.setdefault(object_id, set()).add(path)
            rule_id = _is_forbidden_path(path)
            if rule_id:
                findings.append(Finding("path", rule_id, object_id, path))

    text_blob_count = 0
    skipped_large_blob_count = 0
    scanned_blob_count = 0
    for object_id, paths in sorted(paths_by_object.items()):
        object_type = _git("cat-file", "-t", object_id).strip()
        if object_type != b"blob":
            continue
        scanned_blob_count += 1
        size = int(_git("cat-file", "-s", object_id).strip())
        if size > MAX_TEXT_BLOB_BYTES:
            skipped_large_blob_count += 1
            continue
        body = _git("cat-file", "blob", object_id)
        if b"\0" in body[:8192]:
            continue
        text_blob_count += 1
        display_path = sorted(paths)[0]
        for rule_id, pattern in SECRET_PATTERNS.items():
            match = pattern.search(body)
            if match:
                findings.append(
                    Finding(
                        "content",
                        rule_id,
                        object_id,
                        display_path,
                        _line_number(body, match.start()),
                    )
                )

    deduplicated = sorted(
        {finding for finding in findings},
        key=lambda item: (
            item.kind,
            item.rule_id,
            item.path,
            item.object_id,
            item.line_number or 0,
        ),
    )
    return {
        "schema_version": 1,
        "status": "passed" if not deduplicated else "failed",
        "scope": "all_reachable_git_refs",
        "scanned_object_path_count": len(objects),
        "scanned_blob_count": scanned_blob_count,
        "scanned_text_blob_count": text_blob_count,
        "skipped_large_blob_count": skipped_large_blob_count,
        "finding_count": len(deduplicated),
        "findings": [asdict(finding) for finding in deduplicated],
        "privacy_boundary": {
            "matched_values_emitted": False,
            "object_ids_emitted": True,
            "paths_emitted": True,
            "line_numbers_emitted": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit all reachable Git objects before public release."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/public-readiness-report.json"),
    )
    args = parser.parse_args()

    report = audit_repository()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "scanned_blob_count": report["scanned_blob_count"],
                "finding_count": report["finding_count"],
                "report": args.output.as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
