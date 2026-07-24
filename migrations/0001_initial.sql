-- CoA Raid Intelligence Workbench v0.5
-- Initial local warehouse/domain schema. IDs are supplied by import/domain layers.

CREATE TABLE IF NOT EXISTS source_endpoint (
    endpoint_id VARCHAR PRIMARY KEY,
    endpoint_code VARCHAR NOT NULL UNIQUE,
    route_template VARCHAR NOT NULL,
    method VARCHAR NOT NULL DEFAULT 'GET',
    params_json VARCHAR,
    auth_mode VARCHAR NOT NULL,
    schema_fingerprint VARCHAR,
    pagination_json VARCHAR,
    rate_policy_json VARCHAR,
    sample_payload_path VARCHAR,
    last_verified_at TIMESTAMP,
    status VARCHAR NOT NULL,
    fallback VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_object (
    raw_id VARCHAR PRIMARY KEY,
    endpoint_id VARCHAR,
    request_key VARCHAR NOT NULL,
    payload_hash VARCHAR NOT NULL,
    storage_path VARCHAR NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    http_status INTEGER,
    normalizer_status VARCHAR NOT NULL DEFAULT 'pending',
    metadata_json VARCHAR,
    UNIQUE (request_key, payload_hash)
);

CREATE TABLE IF NOT EXISTS report (
    report_id VARCHAR PRIMARY KEY,
    source_report_id VARCHAR NOT NULL UNIQUE,
    raid_date DATE,
    created_at TIMESTAMP,
    status VARCHAR,
    payload_hash VARCHAR,
    raw_id VARCHAR
);

CREATE TABLE IF NOT EXISTS encounter (
    encounter_id VARCHAR PRIMARY KEY,
    source_encounter_id VARCHAR NOT NULL,
    report_id VARCHAR NOT NULL,
    boss_id VARCHAR,
    boss_name VARCHAR,
    started_at TIMESTAMP,
    duration_ms BIGINT,
    success BOOLEAN,
    raid_size INTEGER,
    raid_format VARCHAR,
    format_bucket VARCHAR,
    canonical_physical_fight_id VARCHAR,
    data_quality_status VARCHAR NOT NULL DEFAULT 'unknown',
    UNIQUE (report_id, source_encounter_id)
);

CREATE TABLE IF NOT EXISTS actor (
    actor_id VARCHAR PRIMARY KEY,
    source_actor_id VARCHAR,
    nickname VARCHAR,
    actor_type VARCHAR,
    owner_actor_id VARCHAR,
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS player (
    player_id VARCHAR PRIMARY KEY,
    display_name VARCHAR NOT NULL,
    aliases_json VARCHAR,
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    identity_status VARCHAR NOT NULL DEFAULT 'unreviewed'
);

CREATE TABLE IF NOT EXISTS game_character (
    character_id VARCHAR PRIMARY KEY,
    player_id VARCHAR,
    nickname VARCHAR NOT NULL,
    class_code VARCHAR,
    aliases_json VARCHAR,
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS participant (
    encounter_id VARCHAR NOT NULL,
    actor_id VARCHAR NOT NULL,
    player_id VARCHAR,
    character_id VARCHAR,
    nickname VARCHAR,
    class_code VARCHAR,
    spec_code VARCHAR,
    role_code VARCHAR,
    participation_status VARCHAR NOT NULL DEFAULT 'observed',
    PRIMARY KEY (encounter_id, actor_id)
);

CREATE TABLE IF NOT EXISTS aura_event (
    encounter_id VARCHAR NOT NULL,
    timestamp_ms BIGINT NOT NULL,
    event_type VARCHAR NOT NULL,
    source_actor_id VARCHAR,
    target_actor_id VARCHAR,
    spell_id VARCHAR NOT NULL,
    stacks INTEGER,
    raw_id VARCHAR,
    event_ordinal BIGINT NOT NULL,
    PRIMARY KEY (encounter_id, event_ordinal)
);

CREATE TABLE IF NOT EXISTS build_snapshot (
    build_snapshot_id VARCHAR PRIMARY KEY,
    player_id VARCHAR,
    character_id VARCHAR,
    class_code VARCHAR NOT NULL,
    spec_code VARCHAR NOT NULL,
    role_code VARCHAR NOT NULL,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    confidence DOUBLE,
    source VARCHAR,
    UNIQUE (character_id, class_code, spec_code, valid_from)
);

CREATE TABLE IF NOT EXISTS effect_family (
    effect_id VARCHAR PRIMARY KEY,
    category VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    priority VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    source_key VARCHAR,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS aura_definition (
    aura_id VARCHAR PRIMARY KEY,
    spell_id VARCHAR NOT NULL,
    name VARCHAR,
    effect_id VARCHAR,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    source VARCHAR,
    UNIQUE (spell_id, valid_from)
);

CREATE TABLE IF NOT EXISTS mechanic_evidence (
    evidence_id VARCHAR PRIMARY KEY,
    evidence_type VARCHAR NOT NULL,
    entity_type VARCHAR NOT NULL,
    entity_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    confidence DOUBLE,
    source_reference VARCHAR,
    observed_at TIMESTAMP,
    payload_json VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mechanic_relationship (
    relationship_id VARCHAR PRIMARY KEY,
    left_entity_id VARCHAR NOT NULL,
    right_entity_id VARCHAR NOT NULL,
    relationship_type VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    confidence DOUBLE,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    version VARCHAR NOT NULL,
    UNIQUE (left_entity_id, right_entity_id, relationship_type, version)
);

CREATE TABLE IF NOT EXISTS provider_capability (
    capability_id VARCHAR PRIMARY KEY,
    class_code VARCHAR NOT NULL,
    spec_code VARCHAR NOT NULL,
    build_code VARCHAR,
    effect_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    confidence DOUBLE,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    activation_json VARCHAR,
    scope_json VARCHAR,
    version VARCHAR NOT NULL,
    UNIQUE (class_code, spec_code, build_code, effect_id, version)
);

CREATE TABLE IF NOT EXISTS raid_profile (
    profile_id VARCHAR PRIMARY KEY,
    code VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    raid_format VARCHAR NOT NULL,
    target_size_rules_json VARCHAR NOT NULL,
    role_limits_json VARCHAR NOT NULL,
    class_limit INTEGER,
    spec_limit INTEGER,
    critical_effects_json VARCHAR,
    important_effects_json VARCHAR,
    backup_policy_json VARCHAR,
    weights_version VARCHAR,
    status VARCHAR NOT NULL,
    UNIQUE (code, version)
);

CREATE TABLE IF NOT EXISTS dataset_snapshot (
    snapshot_id VARCHAR PRIMARY KEY,
    raw_manifest_hash VARCHAR NOT NULL,
    schema_version VARCHAR NOT NULL,
    normalizer_version VARCHAR NOT NULL,
    catalog_version VARCHAR NOT NULL,
    raid_profile_version VARCHAR NOT NULL,
    planner_version VARCHAR NOT NULL,
    snapshot_json VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raid_plan (
    plan_id VARCHAR PRIMARY KEY,
    raid_date DATE,
    boss_id VARCHAR,
    raid_format VARCHAR NOT NULL,
    target_size INTEGER NOT NULL,
    profile_id VARCHAR,
    dataset_snapshot_id VARCHAR,
    ruleset_version VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raid_slot (
    plan_id VARCHAR NOT NULL,
    slot_no INTEGER NOT NULL,
    player_id VARCHAR,
    character_id VARCHAR,
    build_snapshot_id VARCHAR,
    active BOOLEAN NOT NULL,
    locked BOOLEAN NOT NULL DEFAULT FALSE,
    assignment_json VARCHAR,
    PRIMARY KEY (plan_id, slot_no)
);

CREATE TABLE IF NOT EXISTS job (
    job_id VARCHAR PRIMARY KEY,
    job_type VARCHAR NOT NULL,
    state VARCHAR NOT NULL,
    progress DOUBLE NOT NULL DEFAULT 0,
    checkpoint_json VARCHAR,
    error_json VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review_issue (
    issue_id VARCHAR PRIMARY KEY,
    issue_type VARCHAR NOT NULL,
    entity_type VARCHAR NOT NULL,
    entity_id VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    evidence_json VARCHAR,
    resolution_json VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);
