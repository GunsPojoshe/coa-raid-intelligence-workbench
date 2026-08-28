-- Normalize one reviewed official public /statistics response into replayable aggregate evidence.
-- Source values remain local/private; public receipts expose counts and trust flags only.

CREATE TABLE IF NOT EXISTS public_api_statistics_batch (
    batch_id VARCHAR PRIMARY KEY,
    raw_id VARCHAR NOT NULL,
    source_code VARCHAR NOT NULL,
    endpoint_code VARCHAR NOT NULL,
    normalizer_version VARCHAR NOT NULL,
    phase_number INTEGER NOT NULL,
    difficulty VARCHAR NOT NULL,
    metric VARCHAR NOT NULL,
    bracket VARCHAR,
    location VARCHAR,
    boss_id INTEGER,
    damage_mode VARCHAR,
    role VARCHAR,
    class_filter VARCHAR,
    spec_filter VARCHAR,
    week_number INTEGER,
    realm VARCHAR,
    day_number INTEGER,
    class_count INTEGER NOT NULL,
    spec_record_count INTEGER NOT NULL,
    percentile_value_count INTEGER NOT NULL,
    output_fingerprint VARCHAR NOT NULL,
    metadata_json VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (raw_id, normalizer_version)
);

CREATE INDEX IF NOT EXISTS idx_public_api_statistics_batch_scope
    ON public_api_statistics_batch (
        phase_number, difficulty, metric, boss_id, damage_mode, role, created_at
    );

CREATE TABLE IF NOT EXISTS public_api_statistics_class (
    batch_id VARCHAR NOT NULL,
    class_name VARCHAR NOT NULL,
    total_parses BIGINT NOT NULL,
    PRIMARY KEY (batch_id, class_name)
);

CREATE TABLE IF NOT EXISTS public_api_statistics_spec (
    batch_id VARCHAR NOT NULL,
    class_name VARCHAR NOT NULL,
    spec_name VARCHAR NOT NULL,
    avg DOUBLE NOT NULL,
    median DOUBLE NOT NULL,
    max DOUBLE NOT NULL,
    min DOUBLE NOT NULL,
    total_parses BIGINT NOT NULL,
    percentiles_json VARCHAR NOT NULL,
    PRIMARY KEY (batch_id, class_name, spec_name)
);

CREATE INDEX IF NOT EXISTS idx_public_api_statistics_spec_lookup
    ON public_api_statistics_spec (batch_id, class_name, spec_name);

CREATE VIEW public_api_population_prior_v1 AS
SELECT
    batch.batch_id,
    batch.phase_number,
    batch.difficulty,
    batch.metric,
    batch.bracket,
    batch.location,
    batch.boss_id,
    batch.damage_mode,
    batch.role,
    batch.class_filter,
    batch.spec_filter,
    batch.week_number,
    batch.realm,
    batch.day_number,
    spec.class_name,
    spec.spec_name,
    spec.avg,
    spec.median,
    spec.max,
    spec.min,
    spec.total_parses,
    spec.percentiles_json,
    CASE
        WHEN SUM(spec.total_parses) OVER (PARTITION BY spec.batch_id) > 0
        THEN CAST(spec.total_parses AS DOUBLE)
             / CAST(SUM(spec.total_parses) OVER (PARTITION BY spec.batch_id) AS DOUBLE)
        ELSE NULL
    END AS local_parse_share
FROM public_api_statistics_spec AS spec
JOIN public_api_statistics_batch AS batch
  ON batch.batch_id = spec.batch_id;
