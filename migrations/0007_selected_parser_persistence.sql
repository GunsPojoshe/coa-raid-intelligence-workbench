-- Persistence envelope for the verified report/encounter/actor/participant parser slice.
-- These rows are observations only. They do not establish gameplay mechanics or planner coverage.

CREATE TABLE IF NOT EXISTS parser_slice_persistence_run (
    persistence_run_id VARCHAR PRIMARY KEY,
    reconstruction_sha256 VARCHAR NOT NULL,
    reconstruction_version VARCHAR NOT NULL,
    source_code VARCHAR NOT NULL,
    source_normalization_name VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    input_counts_json VARCHAR NOT NULL,
    persisted_counts_json VARCHAR NOT NULL,
    source_batch_hashes_json VARCHAR NOT NULL,
    metadata_json VARCHAR,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    UNIQUE (reconstruction_sha256, reconstruction_version)
);

CREATE TABLE IF NOT EXISTS canonical_entity_observation (
    observation_id VARCHAR PRIMARY KEY,
    persistence_run_id VARCHAR NOT NULL,
    entity_type VARCHAR NOT NULL,
    entity_key VARCHAR NOT NULL,
    entity_hash VARCHAR NOT NULL,
    source_batch_ids_json VARCHAR NOT NULL,
    provenance_type VARCHAR NOT NULL,
    trust_status VARCHAR NOT NULL DEFAULT 'observed',
    entity_json VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (persistence_run_id, entity_type, entity_key)
);

CREATE INDEX IF NOT EXISTS idx_parser_slice_persistence_reconstruction
    ON parser_slice_persistence_run (reconstruction_sha256, reconstruction_version);

CREATE INDEX IF NOT EXISTS idx_canonical_entity_observation_entity
    ON canonical_entity_observation (entity_type, entity_key, trust_status);

CREATE INDEX IF NOT EXISTS idx_canonical_entity_observation_run
    ON canonical_entity_observation (persistence_run_id, entity_type);
