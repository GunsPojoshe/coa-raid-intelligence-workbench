ALTER TABLE aura_state_interval ADD COLUMN IF NOT EXISTS state_status VARCHAR;
ALTER TABLE aura_state_interval ADD COLUMN IF NOT EXISTS metadata_json JSON;
