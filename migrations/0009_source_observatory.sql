-- Source Observatory v1 persistence schema.

ALTER TABLE source_endpoint ADD COLUMN source_code VARCHAR;
ALTER TABLE source_endpoint ADD COLUMN logical_name VARCHAR;
ALTER TABLE source_endpoint ADD COLUMN first_seen_at TIMESTAMP;
ALTER TABLE source_endpoint ADD COLUMN last_seen_at TIMESTAMP;

CREATE TABLE IF NOT EXISTS source_contract_version (
    contract_id VARCHAR PRIMARY KEY,
    source_code VARCHAR NOT NULL,
    endpoint_code VARCHAR NOT NULL,
    method VARCHAR NOT NULL,
    route_template VARCHAR NOT NULL,
    contract_fingerprint VARCHAR NOT NULL,
    parameter_keys_json VARCHAR NOT NULL,
    request_body_shape_json VARCHAR,
    auth_state VARCHAR NOT NULL,
    discovery_source VARCHAR NOT NULL,
    review_state VARCHAR NOT NULL,
    first_seen_at TIMESTAMP NOT NULL,
    last_seen_at TIMESTAMP NOT NULL,
    metadata_json VARCHAR,
    UNIQUE (endpoint_code, contract_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_source_contract_endpoint_seen
    ON source_contract_version (endpoint_code, last_seen_at);

CREATE TABLE IF NOT EXISTS source_capture (
    capture_id VARCHAR PRIMARY KEY,
    contract_id VARCHAR NOT NULL,
    endpoint_code VARCHAR NOT NULL,
    raw_id VARCHAR NOT NULL,
    raw_observation_id VARCHAR NOT NULL,
    captured_at TIMESTAMP NOT NULL,
    request_fingerprint VARCHAR NOT NULL,
    schema_fingerprint VARCHAR,
    http_status INTEGER,
    content_type VARCHAR,
    metadata_json VARCHAR,
    UNIQUE (contract_id, raw_observation_id)
);

CREATE INDEX IF NOT EXISTS idx_source_capture_endpoint_time
    ON source_capture (endpoint_code, captured_at);

CREATE TABLE IF NOT EXISTS source_schema_snapshot (
    snapshot_id VARCHAR PRIMARY KEY,
    capture_id VARCHAR NOT NULL UNIQUE,
    contract_id VARCHAR NOT NULL,
    endpoint_code VARCHAR NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    schema_fingerprint VARCHAR NOT NULL,
    root_type VARCHAR NOT NULL,
    path_types_json VARCHAR NOT NULL,
    dimension_values_json VARCHAR NOT NULL,
    scan_truncated BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_json VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_source_schema_endpoint_time
    ON source_schema_snapshot (endpoint_code, observed_at);

CREATE TABLE IF NOT EXISTS source_change_event (
    event_id VARCHAR PRIMARY KEY,
    source_code VARCHAR NOT NULL,
    endpoint_code VARCHAR NOT NULL,
    contract_id VARCHAR NOT NULL,
    capture_id VARCHAR NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    change_type VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    subject_path VARCHAR,
    previous_value_json VARCHAR,
    current_value_json VARCHAR,
    confidence DOUBLE NOT NULL DEFAULT 1.0,
    status VARCHAR NOT NULL DEFAULT 'open',
    metadata_json VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_source_change_endpoint_time
    ON source_change_event (endpoint_code, observed_at);

CREATE TABLE IF NOT EXISTS artifact_dependency (
    dependency_id VARCHAR PRIMARY KEY,
    artifact_type VARCHAR NOT NULL,
    artifact_key VARCHAR NOT NULL,
    analysis_type VARCHAR NOT NULL,
    analysis_version VARCHAR NOT NULL,
    dependency_type VARCHAR NOT NULL,
    dependency_key VARCHAR NOT NULL,
    dependency_version VARCHAR,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json VARCHAR,
    UNIQUE (
        artifact_type, artifact_key, analysis_type, analysis_version,
        dependency_type, dependency_key, dependency_version
    )
);

CREATE INDEX IF NOT EXISTS idx_artifact_dependency_source
    ON artifact_dependency (dependency_type, dependency_key, active);

CREATE TABLE IF NOT EXISTS analysis_run (
    analysis_run_id VARCHAR PRIMARY KEY,
    analysis_type VARCHAR NOT NULL,
    analysis_version VARCHAR NOT NULL,
    artifact_type VARCHAR,
    artifact_key VARCHAR,
    target_scope_json VARCHAR NOT NULL,
    input_fingerprint VARCHAR,
    output_fingerprint VARCHAR,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    status VARCHAR NOT NULL,
    metadata_json VARCHAR
);

CREATE TABLE IF NOT EXISTS reanalysis_request (
    request_id VARCHAR PRIMARY KEY,
    reason_event_id VARCHAR NOT NULL,
    dependency_id VARCHAR NOT NULL,
    artifact_type VARCHAR NOT NULL,
    artifact_key VARCHAR NOT NULL,
    analysis_type VARCHAR NOT NULL,
    requested_analysis_version VARCHAR NOT NULL,
    target_scope_json VARCHAR NOT NULL,
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR NOT NULL DEFAULT 'pending',
    dedupe_key VARCHAR NOT NULL UNIQUE,
    metadata_json VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_reanalysis_status_requested
    ON reanalysis_request (status, requested_at);
