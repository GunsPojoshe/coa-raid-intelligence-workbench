from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "artifacts" / "project-integrity-report.json"

_REQUIRED_PATHS = (
    "AGENTS.md",
    "README.md",
    "docs/CURRENT_PARADIGM.md",
    "docs/DOCUMENTATION_INDEX.md",
    "docs/PROJECT_MASTER_CONTEXT.md",
    "docs/PROJECT_STATE.md",
    "docs/OFFICIAL_PUBLIC_API.md",
    "docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md",
    "docs/UPSTREAM_ASCENSION_LOGS_EVIDENCE.md",
    "docs/LOCAL_WORKSPACE_BOUNDARY.md",
    "docs/CI_OPERATIONS.md",
    "evidence/real-data/coa-public-api-catalog-real.json",
    "evidence/real-data/coa-public-api-statistics-provenance-capture-real.json",
    "evidence/real-data/coa-public-api-statistics-persistence-real.json",
    "evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json",
    "evidence/real-data/coa-public-api-population-coverage-real.json",
    "evidence/real-data/coa-current-roster-build-provenance-real.json",
    "src/coa_workbench/collector/public_api_capability.py",
    "src/coa_workbench/collector/public_api_source_health.py",
    "src/coa_workbench/collector/source_profile_reanalysis.py",
    "src/coa_workbench/analytics/public_api_population_coverage.py",
    "scripts/review_public_api_capabilities.py",
    "scripts/persist_public_api_statistics.py",
    "scripts/capture_public_api_population_coverage.py",
    "migrations/0013_public_api_statistics.sql",
)

_CANONICAL_DOCS = (
    "README.md",
    "AGENTS.md",
    "docs/CURRENT_PARADIGM.md",
    "docs/DOCUMENTATION_INDEX.md",
    "docs/PROJECT_MASTER_CONTEXT.md",
    "docs/PROJECT_STATE.md",
    "docs/OFFICIAL_PUBLIC_API.md",
)

_REQUIRED_MARKERS = {
    "README.md": (
        "Raid Leader Companion",
        "independent analytics",
        "official CoA Ascension Logs public API",
        "DuckDB",
        "Planner scoring remains fail-closed",
    ),
    "docs/CURRENT_PARADIGM.md": (
        "independent local BI/decision-support system",
        "official documented CoA Ascension Logs public API",
        "events:read",
        "Browser/HAR",
        "profile-scoped aggregate invalidation: proven",
    ),
    "docs/PROJECT_STATE.md": (
        "stats:read",
        "events:read",
        "real DuckDB persistence/idempotence: proven",
        "planner scoring: blocked",
    ),
    "docs/PROJECT_MASTER_CONTEXT.md": (
        "forward-only migrations 0001-0013",
        "public_api_population_prior_v1",
        "source_endpoint_profile dependency",
        "bounded public population coverage model/workflow",
    ),
    "docs/OFFICIAL_PUBLIC_API.md": (
        "Request-scope provenance",
        "events:read",
        "migrations/0013_public_api_statistics.sql",
        "capture_public_api_population_coverage.py",
    ),
}

_STALE_CANONICAL_MARKERS = (
    "e2/log-evidence-refactor",
    "e3/real-log-capture",
    "e4/interactive-har-discovery",
    "Draft PR #",
    "CONTINUATION_PROMPT.md",
    "NEXT_CHAT_HANDOFF.md",
    "Current next gate — selected-report",
)

_FORBIDDEN_TRACKED_PREFIXES = (
    "data/private/",
    "data/raw/",
    "data/parquet/",
    "data/warehouse/",
    "data/normalized/",
    "data/reconstructed/",
    "data/extracted/",
    "data/exchange/in/",
    "data/exchange/out/",
    "data/backups/",
    "data/logs/",
    "exports/",
    "artifacts/",
    "workbook/working/",
)

_ALLOWED_TRACKED_PRIVATE_NAMES = {".gitkeep"}
_MIGRATION_RE = re.compile(r"^(\d{4})_[A-Za-z0-9_]+\.sql$")


def _git_tracked_paths() -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return sorted(
        part.decode("utf-8", errors="surrogateescape")
        for part in completed.stdout.split(b"\0")
        if part
    )


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _check_required_paths() -> dict[str, Any]:
    missing = [path for path in _REQUIRED_PATHS if not (ROOT / path).is_file()]
    return {"name": "required_paths", "passed": not missing, "missing": missing}


def _check_documentation_index() -> dict[str, Any]:
    index = _read("docs/DOCUMENTATION_INDEX.md")
    missing = [
        path
        for path in _CANONICAL_DOCS
        if path not in index and path != "docs/DOCUMENTATION_INDEX.md"
    ]
    return {"name": "documentation_index", "passed": not missing, "missing": missing}


def _check_markers() -> dict[str, Any]:
    missing: dict[str, list[str]] = {}
    for path, markers in _REQUIRED_MARKERS.items():
        text = _read(path)
        absent = [marker for marker in markers if marker not in text]
        if absent:
            missing[path] = absent
    return {"name": "canonical_markers", "passed": not missing, "missing": missing}


def _check_no_stale_markers() -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    for path in _CANONICAL_DOCS:
        text = _read(path)
        for marker in _STALE_CANONICAL_MARKERS:
            if marker in text:
                hits.append({"path": path, "marker": marker})
    return {"name": "no_stale_canonical_markers", "passed": not hits, "hits": hits}


def _check_migrations() -> dict[str, Any]:
    rows: list[tuple[int, str]] = []
    invalid: list[str] = []
    for path in sorted((ROOT / "migrations").glob("*.sql")):
        match = _MIGRATION_RE.fullmatch(path.name)
        if match is None:
            invalid.append(path.name)
            continue
        rows.append((int(match.group(1)), path.name))
    numbers = [number for number, _ in rows]
    expected = list(range(1, max(numbers, default=0) + 1))
    passed = not invalid and numbers == expected and bool(numbers) and numbers[-1] == 13
    return {
        "name": "migration_sequence",
        "passed": passed,
        "numbers": numbers,
        "invalid_names": invalid,
        "expected": expected,
    }


def _check_tracked_private_paths(tracked: list[str]) -> dict[str, Any]:
    forbidden: list[str] = []
    for path in tracked:
        if not path.startswith(_FORBIDDEN_TRACKED_PREFIXES):
            continue
        if Path(path).name in _ALLOWED_TRACKED_PRIVATE_NAMES:
            continue
        forbidden.append(path)
    return {"name": "tracked_private_paths", "passed": not forbidden, "paths": forbidden}


def _check_temporary_paths(tracked: list[str]) -> dict[str, Any]:
    temp = [
        path
        for path in tracked
        if path.endswith((".tmp", ".tmp.md", ".bak", ".orig"))
        or "/tmp/" in f"/{path}/"
        or path.startswith("README.current.")
    ]
    return {"name": "temporary_tracked_paths", "passed": not temp, "paths": temp}


def build_report() -> dict[str, Any]:
    tracked = _git_tracked_paths()
    checks = [
        _check_required_paths(),
        _check_documentation_index(),
        _check_markers(),
        _check_no_stale_markers(),
        _check_migrations(),
        _check_tracked_private_paths(tracked),
        _check_temporary_paths(tracked),
    ]
    passed = sum(bool(check["passed"]) for check in checks)
    return {
        "schema_version": 2,
        "summary": {
            "status": "passed" if passed == len(checks) else "failed",
            "passed": passed,
            "total": len(checks),
        },
        "checks": checks,
    }


def main() -> int:
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["summary"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
