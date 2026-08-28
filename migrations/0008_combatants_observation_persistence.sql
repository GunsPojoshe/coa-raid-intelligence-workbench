-- Persistence envelope and deterministic read models for manually promoted combatants-info observations.
-- These rows verify parser structure and linkage only. They do not establish build strength,
-- gameplay mechanics, semantic uniqueness, or planner-scoring eligibility.

CREATE TABLE IF NOT EXISTS combatants_observation_persistence_run (
    persistence_run_id VARCHAR PRIMARY KEY,
    promotion_receipt_sha256 VARCHAR NOT NULL,
    promotion_version VARCHAR NOT NULL,
    private_extraction_sha256 VARCHAR NOT NULL,
    source_payload_hash VARCHAR NOT NULL,
    schema_fingerprint VARCHAR NOT NULL,
    source_code VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    design_counts_json VARCHAR NOT NULL,
    observation_count INTEGER NOT NULL,
    reviewed_by VARCHAR NOT NULL,
    reviewed_at TIMESTAMP NOT NULL,
    metadata_json VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (private_extraction_sha256, promotion_version)
);

CREATE INDEX IF NOT EXISTS idx_combatants_persistence_payload
    ON combatants_observation_persistence_run (source_payload_hash, schema_fingerprint);

CREATE OR REPLACE VIEW combatants_parser_observation_v1 AS
SELECT
    observation_id AS storage_observation_id,
    persistence_run_id,
    entity_type,
    entity_key AS source_observation_id,
    entity_hash,
    provenance_type,
    trust_status,
    json_extract_string(entity_json, '$.design_id') AS design_id,
    json_extract_string(entity_json, '$.report_id') AS report_id,
    json_extract_string(entity_json, '$.encounter_id') AS encounter_id,
    json_extract_string(entity_json, '$.actor_id') AS actor_id,
    json_extract_string(entity_json, '$.source_actor_id') AS source_actor_id,
    json_extract_string(entity_json, '$.raw_match_path') AS raw_match_path,
    json_extract_string(entity_json, '$.selected_record_sha256') AS selected_record_sha256,
    CAST(json_extract(entity_json, '$.selected_fields') AS VARCHAR) AS selected_fields_json,
    CAST(json_extract(entity_json, '$.linked_actor_ids') AS VARCHAR) AS linked_actor_ids_json,
    CAST(json_extract(entity_json, '$.linked_source_actor_ids') AS VARCHAR)
        AS linked_source_actor_ids_json,
    CAST(json_extract(entity_json, '$.source_raw_match_paths') AS VARCHAR)
        AS source_raw_match_paths_json,
    entity_json
FROM canonical_entity_observation
WHERE entity_type IN (
    'actor_enrichment_observation',
    'combatants_instance_context_observation',
    'combatants_talent_container_observation',
    'combatants_classless_talent_rank_observation',
    'combatants_hero_build_entry_observation',
    'combatants_gear_slot_observation'
)
AND trust_status = 'verified_parser_observation';

CREATE OR REPLACE VIEW combatants_actor_build_observation_v1 AS
SELECT
    storage_observation_id,
    persistence_run_id,
    entity_type,
    source_observation_id,
    entity_hash,
    provenance_type,
    trust_status,
    design_id,
    report_id,
    encounter_id,
    actor_id,
    source_actor_id,
    raw_match_path,
    selected_record_sha256,
    selected_fields_json,
    entity_json
FROM combatants_parser_observation_v1
WHERE actor_id IS NOT NULL;
