-- Materialized current Source Observatory dimension index.
-- Values stay in the local warehouse; public/source-health views expose counts only.

CREATE TABLE IF NOT EXISTS source_dimension_index_value (
    analysis_run_id VARCHAR NOT NULL,
    artifact_key VARCHAR NOT NULL,
    source_code VARCHAR NOT NULL,
    endpoint_code VARCHAR NOT NULL,
    dimension_name VARCHAR NOT NULL,
    dimension_value VARCHAR NOT NULL,
    PRIMARY KEY (
        analysis_run_id,
        source_code,
        endpoint_code,
        dimension_name,
        dimension_value
    )
);

CREATE INDEX IF NOT EXISTS idx_source_dimension_index_artifact
    ON source_dimension_index_value (artifact_key, source_code, dimension_name);

CREATE INDEX IF NOT EXISTS idx_source_dimension_index_run
    ON source_dimension_index_value (analysis_run_id, endpoint_code);
