-- Immutable raw capture observations.
-- raw_object stores one content-addressed payload; this table stores every fetch/import occurrence.

CREATE TABLE IF NOT EXISTS raw_fetch_observation (
    observation_id VARCHAR PRIMARY KEY,
    raw_id VARCHAR NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    http_status INTEGER,
    request_url_sanitized VARCHAR,
    metadata_json VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_fetch_observation_raw
    ON raw_fetch_observation (raw_id, fetched_at);
