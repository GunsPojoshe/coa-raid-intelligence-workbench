# Armory mapping review v1

Дата review: 2026-07-29.

## Scope

Проверены candidate mappings:

- `config/mappings/coa_armory_character_v1.json`;
- `config/mappings/coa_armory_talent_grid_v1.json`.

Основание review:

- immutable endpoint-isolated capture manifest;
- mapping-review packet schema `2`;
- exact payload hashes;
- exact schema fingerprints;
- type/nullability/occurrence inventory без source scalar values;
- local structural validation пользователя.

## Reviewed payloads

### Character

```text
route: /api/armory/character/156120
payload hash: 2a9d752d7af72d41cd9d41836d670069c78e408df7260f5d9caa83b07430985f
schema fingerprint: efbcf618291d824667ba586c22af4ed031fa146d69b11a5539ec17a41d042621
field paths in review packet: 445
node occurrences: 3312
numeric-map paths: 4
```

### Talent grid

```text
route: /api/armory/talent-grid/felsworn
payload hash: 11be25407ec00898547c1b7f342d4596268b3164df9fe0f120bb911559cc5206
schema fingerprint: 7e3b3bfc3966ddc5d0160c8d466e5ba92edbe55440449619d7204102a25b3240
field paths in review packet: 25
node occurrences: 2794
```

## Review decisions

### Accepted as structurally unambiguous

Character mapping:

- capture and encounter identifiers;
- player GUID, display identity, realm, class, race and level;
- upstream role and active specialization index;
- `resolved_ca_talent_ranks` records;
- compact primary/offensive/defensive/resistance summaries.

Talent-grid mapping:

- class name and success flag;
- tree identity and class-tree flag;
- talent IDs, spell IDs, display fields, coordinates, node type and max ranks;
- nullable `group_id` and `category_name` according to the reviewed shape;
- connected talent IDs;
- rank text observations.

### Corrections made during review

1. Character `cao_id` is retained as `source_cao_id`, not renamed to a generic talent ID.
2. Character `bisbeard_tree` is retained as `source_bisbeard_tree`.
3. Talent records retain their parent `tree_slug` through an ancestor selector.
4. Connection records retain both the source talent ID and tree slug.
5. Rank-text records retain both the source talent ID and tree slug.
6. Candidate mappings remain blocked by `require_verified()`.

These changes avoid losing relationships and avoid assigning unverified gameplay semantics to source-specific identifiers.

## Deferred scopes

Character:

- detailed gear;
- hero build numeric map;
- nested character talent presentation trees;
- `_gearOnly` decomposition;
- derived/raw stat internals;
- `sourcesByStat`.

Talent grid:

- `lock_rules` item schema;
- `rank_spell_ids` item schema.

The latter arrays were empty in the reviewed payload, so their future item structures are not established.

## Promotion gate

The type-only review packet is necessary but not sufficient for `verified` status.

Before promotion, the validator must execute every selector against the exact immutable gzip archives and confirm:

1. payload hash;
2. schema fingerprint;
3. route template;
4. singleton selector presence and JSON type;
5. collection occurrence counts;
6. item, ancestor and index selector behavior;
7. required field presence;
8. no raw scalar values in the validation output.

Command:

```powershell
uv run --no-sync python scripts/validate_armory_mappings.py `
    --review "data\exchange\out\armory-mapping-review-v2.json" `
    --manifest "data\exchange\out\armory-endpoint-capture.json" `
    --raw-root "data\raw" `
    --output "data\exchange\out\armory-mapping-validation.json"
```

Expected gate before promotion:

```text
all_structurally_consistent: true
all_raw_archives_consistent: true
all_production_ready: false
```

`all_production_ready: false` remains expected while status is `candidate`.

## Interpretation boundary

A verified Armory mapping would confirm reproducible extraction from the reviewed source schemas. It would not confirm talent magnitude, runtime behavior, stacking, overwrite, scope, provider equivalence or planner criticality.
