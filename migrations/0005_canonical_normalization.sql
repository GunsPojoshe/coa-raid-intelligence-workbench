-- Schema-inspection, verified mappings, canonical normalization runs and rejects.

CREATE TABLE IF NOT EXISTS payload_schema_profile (
    profile_id VARCHAR PRIMARY KEY,
    raw_id VARCHAR,
    schema_fingerprint VARCHAR NOT NULL,
    inspector_version VARCHAR NOT NULL,
    profile_json VARCHAR NOT NULL,
    inspected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (raw_id, schema_fingerprint, inspector_version)
);

CREATE TABLE IF NOT EXISTS normalization_mapping (
    mapping_id VARCHAR PRIMARY KEY,
    source_code VARCHAR NOT NULL,
    endpoint_code VARCHAR,
    schema_fingerprint VARCHAR NOT NULL,
    mapping_version VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    mapping_json VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS normalization_run (
    run_id VARCHAR PRIMARY KEY,
    raw_id VARCHAR,
    mapping_id VARCHAR NOT NULL,
    normalizer_version VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    counts_json VARCHAR,
    error_json VARCHAR
);

CREATE TABLE IF NOT EXISTS normalization_reject (
    reject_id VARCHAR PRIMARY KEY,
    run_id VARCHAR NOT NULL,
    raw_id VARCHAR,
    entity_type VARCHAR,
    source_path VARCHAR,
    reason_code VARCHAR NOT NULL,
    reject_json VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE aura_state_interval ADD COLUMN max_stack_count INTEGER;
ALTER TABLE aura_state_interval ADD COLUMN refresh_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE aura_state_interval ADD COLUMN termination_reason VARCHAR;

CREATE INDEX IF NOT EXISTS idx_payload_schema_fingerprint
    ON payload_schema_profile (schema_fingerprint, inspected_at);
CREATE INDEX IF NOT EXISTS idx_normalization_mapping_fingerprint
    ON normalization_mapping (source_code, schema_fingerprint, status);
CREATE INDEX IF NOT EXISTS idx_normalization_reject_run
    ON normalization_reject (run_id, reason_code);
