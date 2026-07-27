-- Evidence-first schema for CoA Logs ingestion and mechanic inference.
-- Legacy effect/provider rows remain available for audit but are not canonical.

ALTER TABLE effect_family ADD COLUMN trust_status VARCHAR DEFAULT 'legacy_unverified';
ALTER TABLE effect_family ADD COLUMN source_kind VARCHAR DEFAULT 'legacy_excel';
ALTER TABLE provider_capability ADD COLUMN trust_status VARCHAR DEFAULT 'legacy_unverified';
ALTER TABLE provider_capability ADD COLUMN source_kind VARCHAR DEFAULT 'legacy_excel';

CREATE TABLE IF NOT EXISTS game_version (
    game_version_id VARCHAR PRIMARY KEY,
    version_code VARCHAR NOT NULL UNIQUE,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    detected_from_logs BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_json VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS observation_batch (
    batch_id VARCHAR PRIMARY KEY,
    source_code VARCHAR NOT NULL,
    raw_id VARCHAR,
    report_id VARCHAR,
    encounter_id VARCHAR,
    game_version_id VARCHAR,
    observed_at TIMESTAMP,
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    parser_version VARCHAR NOT NULL,
    payload_hash VARCHAR NOT NULL,
    quality_status VARCHAR NOT NULL DEFAULT 'unreviewed',
    metadata_json VARCHAR,
    UNIQUE (source_code, payload_hash, parser_version)
);

CREATE TABLE IF NOT EXISTS aura_observation (
    observation_id VARCHAR PRIMARY KEY,
    batch_id VARCHAR NOT NULL,
    encounter_id VARCHAR NOT NULL,
    event_ordinal BIGINT NOT NULL,
    timestamp_ms BIGINT NOT NULL,
    event_type VARCHAR NOT NULL,
    spell_id VARCHAR NOT NULL,
    source_actor_id VARCHAR,
    target_actor_id VARCHAR,
    stacks INTEGER,
    source_class_code VARCHAR,
    source_spec_code VARCHAR,
    target_type VARCHAR,
    observation_json VARCHAR,
    UNIQUE (encounter_id, event_ordinal, batch_id)
);

CREATE TABLE IF NOT EXISTS aura_state_interval (
    interval_id VARCHAR PRIMARY KEY,
    encounter_id VARCHAR NOT NULL,
    spell_id VARCHAR NOT NULL,
    source_actor_id VARCHAR,
    target_actor_id VARCHAR NOT NULL,
    started_at_ms BIGINT NOT NULL,
    ended_at_ms BIGINT,
    stack_count INTEGER,
    application_ordinal BIGINT,
    removal_ordinal BIGINT,
    reconstruction_version VARCHAR NOT NULL,
    state_status VARCHAR NOT NULL DEFAULT 'reconstructed',
    metadata_json VARCHAR
);

CREATE TABLE IF NOT EXISTS mechanic_hypothesis (
    hypothesis_id VARCHAR PRIMARY KEY,
    hypothesis_type VARCHAR NOT NULL,
    subject_type VARCHAR NOT NULL,
    subject_key VARCHAR NOT NULL,
    predicate VARCHAR NOT NULL,
    object_type VARCHAR,
    object_key VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'candidate',
    confidence DOUBLE NOT NULL DEFAULT 0,
    first_observed_at TIMESTAMP,
    last_observed_at TIMESTAMP,
    supporting_encounters INTEGER NOT NULL DEFAULT 0,
    contradicting_encounters INTEGER NOT NULL DEFAULT 0,
    inference_version VARCHAR NOT NULL,
    hypothesis_json VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (hypothesis_type, subject_key, predicate, object_key, inference_version)
);

CREATE TABLE IF NOT EXISTS hypothesis_evidence_link (
    hypothesis_id VARCHAR NOT NULL,
    observation_id VARCHAR NOT NULL,
    evidence_direction VARCHAR NOT NULL,
    evidence_weight DOUBLE NOT NULL,
    reason_code VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (hypothesis_id, observation_id, reason_code)
);

CREATE TABLE IF NOT EXISTS evidence_weight_policy (
    policy_id VARCHAR PRIMARY KEY,
    version VARCHAR NOT NULL UNIQUE,
    recency_half_life_days DOUBLE NOT NULL,
    guild_weight DOUBLE NOT NULL,
    global_weight DOUBLE NOT NULL,
    min_independent_reports INTEGER NOT NULL,
    min_independent_encounters INTEGER NOT NULL,
    confirmation_threshold DOUBLE NOT NULL,
    rejection_threshold DOUBLE NOT NULL,
    policy_json VARCHAR NOT NULL,
    active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mechanic_inference_run (
    run_id VARCHAR PRIMARY KEY,
    dataset_snapshot_id VARCHAR,
    policy_version VARCHAR NOT NULL,
    inference_version VARCHAR NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    status VARCHAR NOT NULL,
    input_counts_json VARCHAR,
    output_counts_json VARCHAR,
    error_json VARCHAR
);

CREATE TABLE IF NOT EXISTS source_route_probe (
    probe_id VARCHAR PRIMARY KEY,
    endpoint_code VARCHAR NOT NULL,
    probed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    http_status INTEGER,
    auth_state VARCHAR NOT NULL,
    schema_fingerprint VARCHAR,
    response_hash VARCHAR,
    result_status VARCHAR NOT NULL,
    notes VARCHAR,
    metadata_json VARCHAR
);
