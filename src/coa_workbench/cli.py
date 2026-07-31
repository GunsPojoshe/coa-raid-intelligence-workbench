from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlsplit

import typer

from coa_workbench import __version__
from coa_workbench.collector import (
    RawArchive,
    capture_to_dict,
    load_source_registry,
    probe_registry_route,
    probe_result_to_dict,
)
from coa_workbench.config import load_raid_profiles
from coa_workbench.normalizer import (
    NormalizationMapping,
    inspect_payload,
    normalize_payload,
    reconstruct_aura_intervals,
    structure_fingerprint,
)
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
        "ascension_source_registry_exists": (
            root / "config" / "ascension_logs_sources.yaml"
        ).exists(),
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


@app.command("probe-source")
def probe_source(
    endpoint_code: str = typer.Argument("public_home"),
    registry_path: Path = typer.Option(
        Path("config/ascension_logs_sources.yaml"),
        "--registry",
        exists=True,
        dir_okay=False,
    ),
    raw_root: Path = typer.Option(Path("data/raw"), file_okay=False),
    database: Path = typer.Option(Path("data/warehouse/coa.duckdb"), dir_okay=False),
    migrations: Path = typer.Option(Path("migrations"), exists=True, file_okay=False),
    timeout_seconds: float = typer.Option(20.0, min=1.0, max=120.0),
) -> None:
    """Probe one configured source route and archive its unmodified response."""
    registry = load_source_registry(registry_path)
    archive = RawArchive(raw_root, database_path=database, migrations_dir=migrations)
    result = probe_registry_route(
        registry,
        endpoint_code,
        archive,
        timeout_seconds=timeout_seconds,
    )
    typer.echo(json.dumps(probe_result_to_dict(result), ensure_ascii=False, indent=2, default=str))
    if result.error or result.status is None or result.status >= 400:
        raise typer.Exit(code=4)


@app.command("import-json")
def import_json(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    endpoint_code: str = typer.Option("manual_json", "--endpoint"),
    request_key: str | None = typer.Option(None, "--request-key"),
    raw_root: Path = typer.Option(Path("data/raw"), file_okay=False),
    database: Path = typer.Option(Path("data/warehouse/coa.duckdb"), dir_okay=False),
    migrations: Path = typer.Option(Path("migrations"), exists=True, file_okay=False),
) -> None:
    """Archive a locally exported JSON response without interpreting its mechanics."""
    json.loads(path.read_text(encoding="utf-8"))
    archive = RawArchive(raw_root, database_path=database, migrations_dir=migrations)
    capture = archive.capture_file(
        path,
        source_code="coa_ascension_logs",
        endpoint_code=endpoint_code,
        request_key=request_key,
        content_type="application/json",
        metadata={"import_mode": "manual_json"},
    )
    typer.echo(json.dumps(capture_to_dict(capture), ensure_ascii=False, indent=2))


@app.command("import-har")
def import_har(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    registry_path: Path = typer.Option(
        Path("config/ascension_logs_sources.yaml"),
        "--registry",
        exists=True,
        dir_okay=False,
    ),
    raw_root: Path = typer.Option(Path("data/raw"), file_okay=False),
    database: Path = typer.Option(Path("data/warehouse/coa.duckdb"), dir_okay=False),
    migrations: Path = typer.Option(Path("migrations"), exists=True, file_okay=False),
) -> None:
    """Archive response bodies from an exported browser HAR for the configured source host."""
    registry = load_source_registry(registry_path)
    allowed_host = urlsplit(registry.base_url).hostname
    if not allowed_host:
        raise typer.BadParameter("source registry base_url has no hostname")
    archive = RawArchive(raw_root, database_path=database, migrations_dir=migrations)
    captures = archive.import_har(
        path,
        source_code=registry.source_code,
        allowed_host=allowed_host,
    )
    typer.echo(
        json.dumps(
            {
                "har": str(path),
                "allowed_host": allowed_host,
                "captured": len(captures),
                "objects": [capture_to_dict(capture) for capture in captures],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("inspect-json")
def inspect_json(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    output: Path | None = typer.Option(None, "--output", dir_okay=False),
) -> None:
    """Inspect JSON structure and propose collection candidates without assigning semantics."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    inspection = inspect_payload(payload)
    result = inspection.to_dict()
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("normalize-json")
def normalize_json(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    mapping_path: Path = typer.Option(..., "--mapping", exists=True, dir_okay=False),
    output: Path | None = typer.Option(None, "--output", dir_okay=False),
) -> None:
    """Normalize one JSON payload through an explicitly verified mapping and rebuild aura state."""
    raw_bytes = path.read_bytes()
    payload = json.loads(raw_bytes)
    fingerprint = structure_fingerprint(payload)
    mapping = NormalizationMapping.from_path(mapping_path)
    batch = normalize_payload(payload, mapping, schema_fingerprint=fingerprint)
    encounter_ends = {
        str(record["encounter_id"]): int(record["duration_ms"])
        for record in batch.encounters
        if record.get("duration_ms") not in (None, "")
    }
    aura_state = reconstruct_aura_intervals(batch.aura_events, encounter_end_ms=encounter_ends)
    result = {
        "payload_hash": hashlib.sha256(raw_bytes).hexdigest(),
        "schema_fingerprint": fingerprint,
        "canonical": batch.to_dict(),
        "aura_state": {
            "interval_count": len(aura_state.intervals),
            "anomaly_count": len(aura_state.anomalies),
            "intervals": [item.to_dict() for item in aura_state.intervals],
            "anomalies": list(aura_state.anomalies),
        },
    }
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


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
