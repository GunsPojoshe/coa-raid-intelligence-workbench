# Armory mapping review v1

Дата review: 2026-07-29.

## Scope

Проверены mappings:

- `config/mappings/coa_armory_character_v1.json`;
- `config/mappings/coa_armory_talent_grid_v1.json`.

Основание review:

- immutable endpoint-isolated capture manifest;
- mapping-review packet schema `2`;
- exact payload hashes;
- exact schema fingerprints;
- type/nullability/occurrence inventory без source scalar values;
- local structural validation пользователя;
- local raw-archive selector validation пользователя.

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
6. Absolute manifest URLs are normalized to URL paths before route-template comparison.

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

## Completed promotion gate

The validator executed every selected mapping field against the exact immutable gzip archives and confirmed:

1. payload hash;
2. schema fingerprint;
3. route template after URL-path normalization;
4. singleton selector presence and JSON type;
5. collection occurrence counts;
6. item, ancestor and index selector behavior;
7. required field presence;
8. no raw scalar values in the validation output.

User-local result:

```text
schema_version: 2
mapping_count: 2
raw_archive_count: 2
all_structurally_consistent: true
all_raw_archives_consistent: true
all_production_ready: false

coa-armory-character-v1:
  raw_payload_validated: true
  route_matched: true
  singleton_value_count: 19
  extracted_value_count: 328

coa-armory-talent-grid-v1:
  raw_payload_validated: true
  route_matched: true
  singleton_value_count: 2
  extracted_value_count: 2955
```

`all_production_ready: false` was the expected pre-promotion state because both files still had status `candidate` during that run.

## Promotion decision

Both mappings are promoted to `verified` on 2026-07-29 after:

- documented field-by-field structural review;
- successful type-only review-packet validation;
- successful raw-archive selector execution;
- exact hash/fingerprint/route checks;
- green Ubuntu and Windows repository verification.

Reviewer metadata stored in both mapping contracts:

```text
reviewed_by: GunsPojoshe (operator), OpenAI-assisted review
reviewed_at: 2026-07-29T15:34:00+03:00
```

A repeated local validator run after pulling the promotion commits must now produce:

```text
all_structurally_consistent: true
all_raw_archives_consistent: true
all_production_ready: true
```

## Interpretation boundary

A verified Armory mapping confirms reproducible extraction from the exact reviewed source schemas and payload hashes. It does not confirm talent magnitude, runtime behavior, stacking, overwrite, scope, provider equivalence or planner criticality.

Any new payload hash or schema fingerprint requires a new review decision. Deferred scopes remain unavailable for canonical normalization until separately observed and reviewed.
