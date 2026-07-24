from pathlib import Path


def test_initial_migration_contains_required_contract_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    sql = (root / "migrations" / "0001_initial.sql").read_text(encoding="utf-8").lower()
    required = {
        "source_endpoint",
        "raw_object",
        "report",
        "encounter",
        "participant",
        "aura_event",
        "effect_family",
        "aura_definition",
        "provider_capability",
        "raid_profile",
        "dataset_snapshot",
        "raid_plan",
        "raid_slot",
        "job",
        "review_issue",
    }
    for table in required:
        assert f"create table if not exists {table}" in sql
