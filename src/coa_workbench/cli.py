from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path

import typer

from coa_workbench import __version__
from coa_workbench.baseline import freeze_workbook_baseline
from coa_workbench.config import load_raid_profiles
from coa_workbench.storage import DuckDBUnavailableError, apply_migrations

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command("doctor")
def doctor(project_root: Path = typer.Option(Path("."), exists=True, file_okay=False)) -> None:
    """Check the local development/runtime prerequisites."""
    root = project_root.resolve()
    checks = {
        "version": __version__,
        "python": platform.python_version(),
        "python_supported": sys.version_info >= (3, 12),
        "project_root": str(root),
        "raid_profiles_exists": (root / "config" / "raid_profiles.yaml").exists(),
        "endpoint_registry_exists": (root / "config" / "endpoint_registry.yaml").exists(),
        "baseline_manifest_exists": (root / "baseline" / "source_manifest.json").exists(),
        "duckdb_importable": importlib.util.find_spec("duckdb") is not None,
    }
    typer.echo(json.dumps(checks, ensure_ascii=False, indent=2))
    if not checks["python_supported"]:
        raise typer.Exit(code=2)


@app.command("validate-config")
def validate_config(
    path: Path = typer.Option(Path("config/raid_profiles.yaml"), exists=True, dir_okay=False)
) -> None:
    config = load_raid_profiles(path)
    typer.echo(f"Validated {len(config.raid_profiles)} raid profile(s), schema v{config.schema_version}.")


@app.command("freeze-baseline")
def freeze_baseline(
    workbook: Path = typer.Argument(..., exists=True, dir_okay=False),
    output_dir: Path = typer.Option(Path("baseline"), file_okay=False),
    project_document: list[Path] = typer.Option([], "--project-document", exists=True, dir_okay=False),
) -> None:
    """Read the workbook without saving it and freeze inventory, tables and golden state."""
    results = freeze_workbook_baseline(workbook, output_dir, additional_sources=project_document)
    typer.echo(json.dumps({key: str(value) for key, value in results.items()}, ensure_ascii=False, indent=2))


@app.command("init-db")
def init_db(
    database: Path = typer.Option(Path("data/warehouse/coa.duckdb"), dir_okay=False),
    migrations: Path = typer.Option(Path("migrations"), exists=True, file_okay=False),
) -> None:
    """Create/update the local DuckDB warehouse."""
    try:
        applied = apply_migrations(database, migrations)
    except DuckDBUnavailableError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=3) from exc
    typer.echo(json.dumps({"database": str(database), "applied": applied}, ensure_ascii=False, indent=2))
