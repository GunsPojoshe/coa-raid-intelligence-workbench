"""Run the complete, offline-capable repository verification suite."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "artifacts" / "verification-report.json"


def run_check(
    name: str, command: list[str], *, env: dict[str, str] | None = None
) -> dict[str, Any]:
    print(f"\n=== {name} ===", flush=True)
    print("$ " + " ".join(command), flush=True)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    status = "passed" if completed.returncode == 0 else "failed"
    print(f"--- {status} (exit {completed.returncode}) ---", flush=True)
    return {
        "name": name,
        "command": command,
        "status": status,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    python = sys.executable
    clean_env = os.environ.copy()
    clean_env.pop("COA_ENABLE_LEGACY_EFFECTS", None)
    checks: list[dict[str, Any]] = []

    commands = [
        ("Ruff lint", [python, "-m", "ruff", "check", "."], None),
        (
            "Ruff format",
            [python, "-m", "ruff", "format", "--check", "."],
            None,
        ),
        ("Full pytest", [python, "-m", "pytest"], clean_env),
        (
            "Doctor",
            [python, "-m", "coa_workbench", "doctor", "--project-root", "."],
            clean_env,
        ),
        ("CLI help", [python, "-m", "coa_workbench", "--help"], clean_env),
        (
            "Config smoke test",
            [
                python,
                "-m",
                "coa_workbench",
                "validate-config",
                "--path",
                "config/raid_profiles.yaml",
            ],
            clean_env,
        ),
        (
            "Legacy scoring disabled by default",
            [
                python,
                "-m",
                "pytest",
                "tests/unit/test_effect_analytics.py::test_preview_disables_legacy_scoring_by_default",
            ],
            clean_env,
        ),
        (
            "Unverified normalization mapping rejected",
            [
                python,
                "-m",
                "pytest",
                "tests/unit/test_canonical_normalizer.py::test_candidate_mapping_is_blocked",
            ],
            clean_env,
        ),
    ]
    for name, command, env in commands:
        checks.append(run_check(name, command, env=env))

    with tempfile.TemporaryDirectory(prefix="coa-verification-") as temp_dir:
        database = Path(temp_dir) / "coa.duckdb"
        migration_command = [
            python,
            "-m",
            "coa_workbench",
            "init-db",
            "--database",
            str(database),
            "--migrations",
            "migrations",
        ]
        checks.append(run_check("Clean database initialization", migration_command, env=clean_env))
        checks.append(
            run_check("Repeated database initialization", migration_command, env=clean_env)
        )

    passed = sum(check["status"] == "passed" for check in checks)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(ROOT),
        "summary": {
            "status": "passed" if passed == len(checks) else "failed",
            "passed": passed,
            "total": len(checks),
        },
        "checks": checks,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\n=== Summary: {passed}/{len(checks)} checks passed ===")
    print(f"JSON report: {REPORT_PATH}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
