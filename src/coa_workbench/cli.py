from __future__ import annotations

import importlib.util
import json
import platform
import sys
import webbrowser
from pathlib import Path

import typer

from coa_workbench import __version__
from coa_workbench.config import load_raid_profiles
from coa_workbench.storage import DuckDBUnavailableError, apply_migrations

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command("doctor")
def doctor(project_root: Path = typer.Option(Path("."), exists=True, file_okay=False)) -> None:
    """Check the localhost application prerequisites."""
    root = project_root.resolve()
    checks = {
        "version": __version__,
        "python": platform.python_version(),
        "python_supported": sys.version_info >= (3, 12),
        "project_root": str(root),
        "raid_profiles_exists": (root / "config" / "raid_profiles.yaml").exists(),
        "endpoint_registry_exists": (root / "config" / "endpoint_registry.yaml").exists(),
        "web_runtime_importable": all(
            importlib.util.find_spec(name) is not None for name in ("fastapi", "uvicorn")
        ),
        "duckdb_importable": importlib.util.find_spec("duckdb") is not None,
        "runtime_mode": "localhost-web",
        "excel_required": False,
    }
    typer.echo(json.dumps(checks, ensure_ascii=False, indent=2))
    if not checks["python_supported"] or not checks["web_runtime_importable"]:
        raise typer.Exit(code=2)


@app.command("validate-config")
def validate_config(
    path: Path = typer.Option(Path("config/raid_profiles.yaml"), exists=True, dir_okay=False)
) -> None:
    config = load_raid_profiles(path)
    typer.echo(f"Validated {len(config.raid_profiles)} raid profile(s), schema v{config.schema_version}.")


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


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", help="Keep 127.0.0.1 for local-only access."),
    port: int = typer.Option(8000, min=1, max=65535),
    reload: bool = typer.Option(False, help="Auto-reload during development."),
    open_browser: bool = typer.Option(True, "--open-browser/--no-open-browser"),
) -> None:
    """Run the local browser application."""
    import uvicorn

    url = f"http://{host}:{port}"
    if open_browser:
        webbrowser.open(url)
    typer.echo(f"CoA Raid Intelligence: {url}")
    uvicorn.run("coa_workbench.web.app:app", host=host, port=port, reload=reload)
