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
    "docs/CONTINUATION_PROMPT.md",
    "docs/NEXT_CHAT_HANDOFF.md",
    "docs/OFFICIAL_PUBLIC_API.md",
    "docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md",
    "docs/UPSTREAM_ASCENSION_LOGS_EVIDENCE.md",
    "docs/LOCAL_WORKSPACE_BOUNDARY.md",
    "docs/LOCAL_WORKSPACE_AUDIT.md",
    "docs/CI_OPERATIONS.md",
    "docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md",
    "evidence/real-data/coa-public-api-catalog-real.json",
    "evidence/real-data/coa-public-api-statistics-capture-real.json",
    "evidence/real-data/coa-public-api-statistics-shape-real.json",
    "evidence/real-data/coa-public-api-statistics-provenance-capture-real.json",
    "evidence/real-data/coa-public-api-statistics-persistence-real.json",
    "evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json",
    "src/coa_workbench/collector/public_api_source_health.py",
    "src/coa_workbench/collector/source_profile_reanalysis.py",
    "src/coa_workbench/analytics/public_api_population_coverage.py",
    "scripts/inventory_local_workspace.py",
    "scripts/persist_public_api_statistics.py",
    "scripts/capture_public_api_population_coverage.py",
    "migrations/0013_public_api_statistics.sql",
)

_CANONICAL_DOCS = (
    "README.md",
    "AGENTS.md",
    "docs/CURRENT_PARADIGM.md",
    "docs/PROJECT_MASTER_CONTEXT.md",
    "docs/PROJECT_STATE.md",
    "docs/CONTINUATION_PROMPT.md",
    "docs/NEXT_CHAT_HANDOFF.md",
    "docs/OFFICIAL_PUBLIC_API.md",
    "docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md",
    "docs/BROWSER_OBSERVATORY.md",
)

_STALE_MARKERS = (
    "migrations: 0001–0008",
    "migrations `0001`–`0008`",
    "0001-0011",
    "0001–0011",
    "currently 0001-0012",
    "forward-only migrations 0001-0012",
    "The current tracked migration series reaches `0012_profile_schema_cycle.sql`",
    "Current helper-definition stage",
    "first real Browser Observatory session",
    "First real E4 scenario",
    "source-structure reviewer: implemented, real run pending",
    "report.difficulty Browser Observatory session",
    "Real archived-capture replay is not yet proven",
    "Real-source persistence remains pending",
    "real capture replay/idempotence: pending",
    "real statistics persistence/idempotence: pending",
    "one bounded provenance-aware /statistics recapture",
    "aggregate Source Observatory/Health integration: implemented/tested; real local replay pending",
    "Source Observatory/Health integration: current gate",
    "Current next gate is Source Observatory/Health replay",
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


def _check_documentation_authority() -> dict[str, Any]:
    index = _read("docs/DOCUMENTATION_INDEX.md")
    missing_mentions = [path for path in _CANONICAL_DOCS if path not in index]
    return {
        "name": "documentation_authority",
        "passed": not missing_mentions,
        "missing_index_mentions": missing_mentions,
    }


def _check_current_paradigm_markers() -> dict[str, Any]:
    required_markers = {
        "docs/CURRENT_PARADIGM.md": (
            "official documented CoA Ascension Logs public API",
            "Browser/HAR",
            "population aggregate persistence/idempotence: proven",
            "aggregate Source Observatory/Health: proven",
            "profile-scoped aggregate invalidation: proven",
            "bounded multi-profile population coverage",
        ),
        "docs/PROJECT_STATE.md": (
            "real statistics normalization: proven",
            "real DuckDB persistence/idempotence: proven",
            "aggregate Source Observatory/Health integration: proven real",
            "profile-scoped aggregate invalidation: proven real",
            "bounded multi-profile population coverage v1",
            "historical difficulty equivalence",
        ),
        "docs/PROJECT_MASTER_CONTEXT.md": (
            "forward-only migrations 0001-0013",
            "public_api_population_prior_v1",
            "source_endpoint_profile dependency",
            "bounded public population coverage model/workflow",
        ),
        "docs/DOCUMENTATION_INDEX.md": (
            "0013_public_api_statistics.sql",
            "coa-public-api-statistics-persistence-real.json",
            "coa-public-api-statistics-profile-reanalysis-real.json",
            "Source Observatory/Health",
            "capture_public_api_population_coverage.py",
        ),
        "README.md": (
            "active official-API / upstream-evidence workstream",
            "scripts/inventory_local_workspace.py",
            "forward-only migrations 0001-0013",
            "scripts/persist_public_api_statistics.py",
            "scripts/capture_public_api_population_coverage.py",
            "second-pass replay:            idempotent",
            "legacy broad endpoint dependency: inactive",
        ),
        "docs/OFFICIAL_PUBLIC_API.md": (
            "Request-scope provenance rule",
            "0013_public_api_statistics.sql",
            "src/coa_workbench/collector/public_api_source_health.py",
            "coa-public-api-statistics-profile-reanalysis-real.json",
            "capture_public_api_population_coverage.py",
        ),
        "docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md": (
            "official documented public API",
            "schema_profile_keys",
            "source_endpoint_profile",
            "Real aggregate profile migration proof",
            "Bounded population coverage v1",
        ),
    }
    missing: dict[str, list[str]] = {}
    for path, markers in required_markers.items():
        text = _read(path)
        absent = [marker for marker in markers if marker not in text]
        if absent:
            missing[path] = absent
    return {"name": "current_paradigm_markers", "passed": not missing, "missing": missing}


def _check_no_stale_canonical_markers() -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    for path in _CANONICAL_DOCS:
        text = _read(path)
        for marker in _STALE_MARKERS:
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
    passed = not invalid and numbers == expected and bool(numbers) and numbers[-1] >= 13
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
        _check_documentation_authority(),
        _check_current_paradigm_markers(),
        _check_no_stale_canonical_markers(),
        _check_migrations(),
        _check_tracked_private_paths(tracked),
        _check_temporary_paths(tracked),
    ]
    passed = sum(bool(check["passed"]) for check in checks)
    return {
        "schema_version": 1,
        "summary": {
            "status": "passed" if passed == len(checks) else "failed",
            "passed": passed,
            "total": len(checks),
            "tracked_file_count": len(tracked),
        },
        "checks": checks,
    }


def main() -> int:
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["summary"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
