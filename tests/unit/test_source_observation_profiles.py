from coa_workbench.collector.source_observatory import (
    ReviewedGetContract,
    observation_profile_key,
)


def _contract() -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="coa_ascension_logs",
        endpoint_code="report_encounter_throughput_timeline_api",
        base_url="https://coa.ascensionlogs.gg",
        route_template=(
            "/api/reports/{reportId}/encounters/{encounterId}/throughput-timeline"
        ),
        parameter_keys=("bucket_size_ms", "metric", "perspective"),
        schema_profile_keys=("metric", "perspective"),
        auth_state="browser_context_observed",
        discovery_source="test",
        review_state="verified",
    )


def test_profile_key_ignores_path_values_and_non_profile_query_values() -> None:
    contract = _contract()
    first = observation_profile_key(
        contract,
        "https://coa.ascensionlogs.gg/api/reports/1/encounters/2/throughput-timeline"
        "?bucket_size_ms=1000&metric=damage",
    )
    second = observation_profile_key(
        contract,
        "https://coa.ascensionlogs.gg/api/reports/9/encounters/8/throughput-timeline"
        "?metric=damage&bucket_size_ms=5000",
    )
    assert first == second


def test_profile_key_distinguishes_response_shaping_values_and_missing_keys() -> None:
    contract = _contract()
    damage = observation_profile_key(
        contract,
        "https://coa.ascensionlogs.gg/api/reports/1/encounters/2/throughput-timeline"
        "?metric=damage&bucket_size_ms=1000",
    )
    healing = observation_profile_key(
        contract,
        "https://coa.ascensionlogs.gg/api/reports/1/encounters/2/throughput-timeline"
        "?metric=healing&bucket_size_ms=1000",
    )
    damage_taken = observation_profile_key(
        contract,
        "https://coa.ascensionlogs.gg/api/reports/1/encounters/2/throughput-timeline"
        "?metric=damage&perspective=taken&bucket_size_ms=1000",
    )
    assert damage != healing
    assert damage != damage_taken
    assert healing != damage_taken


def test_unprofiled_contract_returns_no_profile_key() -> None:
    contract = ReviewedGetContract(
        source_code="coa_ascension_logs",
        endpoint_code="reports_queue_status_api",
        base_url="https://coa.ascensionlogs.gg",
        route_template="/api/reports/queue-status",
        auth_state="browser_context_observed",
        discovery_source="test",
        review_state="verified",
    )
    assert observation_profile_key(
        contract,
        "https://coa.ascensionlogs.gg/api/reports/queue-status",
    ) is None
