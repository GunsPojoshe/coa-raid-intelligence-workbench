-- Source Observatory acquisition observations.
-- Keeps transport/access outcomes separate from schema-bearing source_capture rows.

CREATE TABLE IF NOT EXISTS source_acquisition_observation (
    acquisition_id VARCHAR PRIMARY KEY,
    contract_id VARCHAR NOT NULL,
    source_code VARCHAR NOT NULL,
    endpoint_code VARCHAR NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    capture_mode VARCHAR NOT NULL,
    request_fingerprint VARCHAR NOT NULL,
    raw_id VARCHAR,
    raw_observation_id VARCHAR,
    source_capture_id VARCHAR,
    http_status INTEGER,
    content_type VARCHAR,
    body_kind VARCHAR NOT NULL,
    outcome VARCHAR NOT NULL,
    blocker_class VARCHAR,
    error_class VARCHAR,
    metadata_json VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_source_acquisition_endpoint_time
    ON source_acquisition_observation (endpoint_code, observed_at);

CREATE INDEX IF NOT EXISTS idx_source_acquisition_outcome_time
    ON source_acquisition_observation (outcome, observed_at);
