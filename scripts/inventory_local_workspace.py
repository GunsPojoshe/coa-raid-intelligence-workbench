from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_TOOLING_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "__pycache__",
    "playwright-report",
    "test-results",
}

_PRIVATE_PREFIXES = (
    "data/private/",
    "data/raw/",
    "data/warehouse/",
    "data/parquet/",
    "data/normalized/",
    "data/reconstructed/",
    "data/extracted/",
    "data/exchange/in/",
    "data/backups/",
    "data/logs/",
    "exports/",
    "artifacts/",
    "workbook/working/",
)

_GENERATED_PREFIXES = ("data/exchange/out/",)


def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _git_path_set(repo_root: Path, *args: str) -> set[str]:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
    )
    return {
        part.decode("utf-8", errors="surrogateescape")
        for part in completed.stdout.split(b"\0")
        if part
    }


def _classify(relative_path: str, *, tracked: bool) -> str:
    normalized = relative_path.replace("\\", "/")
    if tracked:
        return "tracked"
    if normalized.startswith(_PRIVATE_PREFIXES):
        return "private_or_authoritative_local"
    if normalized.startswith(_GENERATED_PREFIXES):
        return "generated_exchange_output"
    return "untracked_other"


def _iter_workspace_files(
    repo_root: Path,
    *,
    tracked: set[str],
    modified_tracked: set[str],
    git_untracked: set[str],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    rows: list[dict[str, Any]] = []
    skipped_dirs: Counter[str] = Counter()

    for current_root, dir_names, file_names in os.walk(repo_root):
        kept_dirs: list[str] = []
        for name in dir_names:
            if name in _TOOLING_DIRS:
                skipped_dirs[name] += 1
            else:
                kept_dirs.append(name)
        dir_names[:] = kept_dirs

        root_path = Path(current_root)
        for file_name in file_names:
            path = root_path / file_name
            relative = path.relative_to(repo_root)
            relative_text = relative.as_posix()
            is_tracked = relative_text in tracked
            stat = path.stat()
            rows.append(
                {
                    "path": relative_text,
                    "size_bytes": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                    "suffix": path.suffix.casefold(),
                    "is_tracked": is_tracked,
                    "is_modified_tracked": relative_text in modified_tracked,
                    "is_git_visible_untracked": relative_text in git_untracked,
                    "workspace_class": _classify(relative_text, tracked=is_tracked),
                }
            )

    rows.sort(key=lambda row: str(row["path"]))
    return rows, skipped_dirs


def _private_manifest(repo_root: Path) -> dict[str, Any]:
    tracked = _git_path_set(repo_root, "ls-files", "-z")
    modified_tracked = _git_path_set(repo_root, "diff", "--name-only", "-z")
    modified_tracked.update(_git_path_set(repo_root, "diff", "--cached", "--name-only", "-z"))
    git_untracked = _git_path_set(repo_root, "ls-files", "--others", "--exclude-standard", "-z")
    missing_tracked = sorted(
        relative_path for relative_path in tracked if not (repo_root / relative_path).exists()
    )

    rows, skipped_dirs = _iter_workspace_files(
        repo_root,
        tracked=tracked,
        modified_tracked=modified_tracked,
        git_untracked=git_untracked,
    )
    classes = Counter(str(row["workspace_class"]) for row in rows)
    suffixes = Counter(str(row["suffix"]) or "<none>" for row in rows)
    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git": {
            "branch": _git(repo_root, "branch", "--show-current"),
            "head": _git(repo_root, "rev-parse", "HEAD"),
            "modified_tracked_paths": sorted(modified_tracked),
            "git_visible_untracked_paths": sorted(git_untracked),
            "missing_tracked_paths": missing_tracked,
        },
        "inventory": {
            "file_count": len(rows),
            "tracked_existing_file_count": sum(bool(row["is_tracked"]) for row in rows),
            "nontracked_existing_file_count": sum(not bool(row["is_tracked"]) for row in rows),
            "modified_tracked_file_count": len(modified_tracked),
            "git_visible_untracked_file_count": len(git_untracked),
            "missing_tracked_file_count": len(missing_tracked),
            "workspace_class_counts": dict(sorted(classes.items())),
            "suffix_counts": dict(sorted(suffixes.items())),
            "skipped_tooling_directory_counts": dict(sorted(skipped_dirs.items())),
            "files": rows,
        },
        "safety": {
            "file_contents_read": False,
            "secret_values_read": False,
            "content_hashes_computed": False,
            "diff_contents_read": False,
            "destructive_git_commands_used": False,
            "private_manifest": True,
        },
    }


def _public_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    inventory = manifest["inventory"]
    return {
        "schema_version": 2,
        "inventory": {
            "file_count": inventory["file_count"],
            "tracked_existing_file_count": inventory["tracked_existing_file_count"],
            "nontracked_existing_file_count": inventory["nontracked_existing_file_count"],
            "modified_tracked_file_count": inventory["modified_tracked_file_count"],
            "git_visible_untracked_file_count": inventory["git_visible_untracked_file_count"],
            "missing_tracked_file_count": inventory["missing_tracked_file_count"],
            "workspace_class_counts": inventory["workspace_class_counts"],
            "suffix_counts": inventory["suffix_counts"],
            "skipped_tooling_directory_counts": inventory["skipped_tooling_directory_counts"],
        },
        "safety": {
            "contains_file_paths": False,
            "contains_secret_values": False,
            "contains_file_contents": False,
            "contains_content_hashes": False,
            "contains_diff_contents": False,
            "destructive_git_commands_used": False,
        },
        "public_release_safe": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inventory local project files without reading file contents or modifying state."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path("data/private/local-workspace-inventory.json"),
    )
    parser.add_argument(
        "--public-output",
        type=Path,
        default=Path("data/exchange/out/local-workspace-inventory-summary.json"),
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    manifest = _private_manifest(repo_root)
    summary = _public_summary(manifest)

    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    args.private_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.public_output.parent.mkdir(parents=True, exist_ok=True)
    args.public_output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
