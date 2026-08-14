from pathlib import Path

from coa_workbench.collector.source_health import build_source_health
from coa_workbench.storage.migrations import apply_migrations


def test_source_health_empty_database(tmp_path: Path) -> None:
    database = tmp_path / "health.duckdb"
    apply_migrations(database, Path("migrations"))

    result = build_source_health(database)

    assert result["health_version"] == "source-health-v1"
    assert result["summary"]["endpoint_count"] == 0
    assert result["summary"]["captured_endpoint_count"] == 0
    assert result["summary"]["open_change_event_count"] == 0
    assert result["summary"]["pending_reanalysis_request_count"] == 0
    assert result["endpoints"] == []
    assert result["recent_changes"] == []
    assert result["privacy"]["dimension_values_included"] is False
