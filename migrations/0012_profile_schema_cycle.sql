-- Aggregate schema observations across one reviewed response profile within a Network/HAR cycle.
-- Individual raw captures and exact source_schema_snapshot rows remain immutable.

CREATE TABLE IF NOT EXISTS source_profile_schema_cycle (
    cycle_snapshot_id VARCHAR PRIMARY KEY,
    source_code VARCHAR NOT NULL,
    endpoint_code VARCHAR NOT NULL,
    contract_id VARCHAR NOT NULL,
    observation_profile_key VARCHAR NOT NULL,
    cycle_fingerprint VARCHAR NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    member_capture_count INTEGER NOT NULL,
    member_capture_ids_json VARCHAR NOT NULL,
    schema_fingerprint VARCHAR NOT NULL,
    root_type VARCHAR NOT NULL,
    path_types_json VARCHAR NOT NULL,
    dimension_values_json VARCHAR NOT NULL,
    scan_truncated BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_json VARCHAR,
    UNIQUE (endpoint_code, observation_profile_key, cycle_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_source_profile_schema_cycle_endpoint_profile_time
    ON source_profile_schema_cycle (endpoint_code, observation_profile_key, observed_at);
