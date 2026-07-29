# Фактическое состояние проекта

Дата актуализации: **2026-07-30**.

Этот документ фиксирует изменяемое operational state. Перед работой всегда перепроверять GitHub, код, local receipts и CI.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Green baseline перед обновлением документации:

```text
commit: 2b92b3d02339a3748d146c1b15a6718f84494e6f
workflow: Verify repository
run: #280
Ubuntu: success
Windows: success
```

PR #7 остаётся open, Draft и mergeable.

## Реализованный фундамент

### Product runtime

- localhost FastAPI application;
- browser raid constructor FLEX / 10 / 25 / 40;
- Python validation;
- class/spec/role catalog;
- DuckDB raid-plan persistence;
- create/read/update/delete plans;
- request IDs и diagnostic logging;
- localhost-only bind по умолчанию.

### Evidence runtime

- source registry;
- safe source probe;
- immutable content-addressed raw archive;
- repeated retrieval observation отдельно от deduplicated payload body;
- JSON/HAR import;
- deterministic privacy-safe HAR inventory;
- archived gzip JSON inspection;
- schema fingerprints;
- versioned mapping contracts;
- mandatory `verified` mapping gate;
- canonical report/encounter/actor/participant/aura records;
- normalization rejects;
- Aura State Engine;
- hypotheses и evidence links;
- trust/weighting policies;
- migrations `0001`–`0007`;
- repository verifier;
- Ubuntu/Windows CI.

## Trust boundary

Normalization разрешена только при:

```text
immutable archived payload
+ exact payload SHA-256
+ exact schema fingerprint
+ reviewed mapping
+ mapping status verified
```

Parser/schema verification не подтверждает игровую механику. В canonical planner scoring допускаются только `corroborated` и `confirmed` mechanics.

## Verified Armory checkpoint

Verified mappings:

```text
config/mappings/coa_armory_character_v1.json
config/mappings/coa_armory_talent_grid_v1.json
```

Reviewer metadata:

```text
reviewed_by: GunsPojoshe (operator), OpenAI-assisted review
reviewed_at: 2026-07-29T15:34:00+03:00
```

Post-promotion validation:

```text
schema_version: 2
mapping_count: 2
raw_archive_count: 2
all_structurally_consistent: true
all_raw_archives_consistent: true
all_production_ready: true
```

Deferred scopes remain documented in `docs/ARMORY_MAPPING_REVIEW_V1.md`.

## Verified public-report discovery checkpoint

Observed request:

```text
GET /api/reports/public
page=1
limit=5
sortBy=created_at
sortOrder=desc
```

Exact binding:

```text
payload hash:       2203e52709fad4fbc8d5235bc3699abeec6b85cf1e13b9df3e24091ddf8775c2
schema fingerprint: 4f47885820e6931cd76db538cabd68405b4969778c1bede9dee53a7f1e005ed4
mapping:            config/mappings/coa_public_report_discovery_v1.json
mapping status:     verified
selected fields:    7
production_ready:   true
```

Unverified: source category semantics, additional-page policy and pagination stopping rules.

## Observed report slice

Observed route shapes:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

Отдельный `/roster` route не наблюдался.

### Report detail

```text
payload hash:       161739896f0b8321f884bcc24d1896efb894a9c6e05166269189f9871c64cba9
schema fingerprint: 3d533a4178b67957bbd31544ddf5484bd5959635ebd5edcdd0c7689a4bace216
bytes:              3562
```

### Encounter detail

```text
payload hash:       955437d6c9c287cc7db280dd2388b88603af2785508061b95c7811dcd272fe22
schema fingerprint: 567f36824efb37a29b835df01ce9b1fcc79eae57d6230202d16a6265c6ca0e85
bytes:              734084
```

### Combatants info

```text
payload hash:       45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14
schema fingerprint: 41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff
bytes:              637520
```

## Completed report/encounter parser gate

Published mappings:

```text
config/mappings/coa_report_detail_v1.json
config/mappings/coa_encounter_detail_v1.json
```

Publication boundary:

```text
published mappings:                    2
field contracts:                       54
selected parser normalization allowed: true
mechanic semantics verified:           false
combatants-info available:             false
aura normalization available:          false
full report slice complete:            false
```

## Completed selected-parser normalization

Aggregate normalized input:

```text
reports:       2
encounters:   15
actors:       31
participants: 31
aura_events:   0
rejects:       0
```

All mapping hashes, raw archives, counts and six cross-payload checks passed.

Local normalized batches contain source-derived scalar values and remain gitignored.

## Completed deterministic reconstruction

Output:

```text
reports:       1
encounters:   14
actors:       31
participants: 31
aura_events:   0
rejects:       0
```

Merge facts:

```text
duplicate reports merged:    1
duplicate encounters merged: 1
field conflicts:             0
linkage checks:              9/9
```

The reconstructed file is private and local-only.

## Completed selected-parser persistence

Migration:

```text
migrations/0007_selected_parser_persistence.sql
```

Persisted local DuckDB state:

```text
reports:                       1
encounters:                   14
actors:                       31
participants:                 31
canonical entity observations:77
normalization mappings:        2
normalization runs:            2
observation batches:           2
rejects:                       0
transaction committed:         true
```

Core parser entities are persisted with reproducible provenance. The database remains local and private.

## Combatants-info review and design

### Deep structural review

```text
bounded scope candidates: 12
present scopes:           10
required scopes:           4/4
direct fields:             56
missing optional scopes:    2
```

Missing:

```text
/combatants/*/ci_resolved/mystic_enchants/*
/combatants/*/ci_resolved/specialization/talents/trees/*
```

### Manual field selection

```text
selection groups:       8
selected fields:       37
deferred fields:       19
actor linkage path:     /combatants/*/character_id
candidate mappings:     not created
```

### Storage-aware mapping design

Six dedicated immutable observation units:

```text
coa-combatants-actor-enrichment-v1
coa-combatants-instance-context-v1
coa-combatants-talent-container-v1
coa-combatants-classless-talent-rank-v1
coa-combatants-hero-build-entry-v1
coa-combatants-gear-slot-v1
```

All target `canonical_entity_observation`; core actor mutation is forbidden.

### Candidate extraction dry run

Exact result:

```text
source matches:       1350
output observations:  1343
deduplicated matches: 7
linked actors:        11
actor name matches:   11
integrity checks:     12/12
core mutations:       0
```

Per design:

```text
actor enrichment:       11 -> 11
instance context:        11 -> 4   (7 exact duplicates)
talent container:        11 -> 11
classless talent rank:  564 -> 564
hero build entry:       564 -> 564
gear slot:              189 -> 189
```

Verified for the exact payload:

- raw archive;
- observation manifest;
- route context;
- persisted report/encounter references;
- 11 stable actor links;
- exact existing actor names;
- selected JSON types;
- record hashes;
- source match counts;
- no core mutation.

Still unverified:

- companion-addon provenance;
- semantic meaning and global uniqueness of nested identifiers;
- talent/gear gameplay semantics;
- automatic persistence policy;
- promotion;
- normalization as canonical player/build state;
- planner scoring.

The scalar-free receipt is versioned at:

```text
evidence/real-data/observed-combatants-info-candidate-extraction.json
```

## Real aura checkpoint

Separate real-aura fixtures validate normalizer/Aura State Engine behavior for report `2987`, spell `968746`:

```text
encounter 64795: 6 events -> 3 intervals, 0 rejects, 0 anomalies
encounter 64796: 3 events -> 2 intervals, 0 rejects, 0 anomalies
```

This does not verify numeric effect, stacking, overwrite, scope, provider equivalence or planner criticality.

## Data and Git policy

The user has authorized use of all local private context while the repository remains private. This allows local analysis but does not make secrets or bulky raw data appropriate Git artifacts.

Versioned:

- source code and tests;
- migrations;
- reviewed mappings;
- canonical documentation;
- scalar-free evidence receipts.

Local-only by default:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never commit cookies, tokens, Authorization headers, browser profiles, `.env` secrets or unsanitized HAR.

## Current blockers

1. Candidate combatants extraction has not passed a separate manual promotion gate.
2. The 1343 extracted observations are not persisted.
3. No read model exists yet for actor build/talent/gear observations.
4. Companion-addon provenance is not verified.
5. Nested collection semantics and identifier uniqueness are not verified.
6. The report slice contains no aura events and is not complete.
7. Evidence coverage is insufficient for any new corroborated gameplay mechanic.
8. Planner scoring remains correctly disabled for observed/candidate data.

## Next bounded tasks

1. Validate the exact candidate extraction receipt as the input to a manual promotion decision.
2. Define immutable persistence contracts for the six combatants observation types.
3. Add an idempotent migration only if the existing observation table cannot represent required provenance.
4. Persist candidate observations atomically without mutating core actor rows.
5. Add deterministic queries/read models for actor enrichment and build observations.
6. Investigate exact aura-related endpoints for the observed report slice.
7. Gather independent supporting and contradicting observations before mechanic promotion.

## Completion gate

PR #7 remains Draft until the relevant evidence checkpoint includes:

- exact immutable payloads and fingerprints;
- verified report/encounter parsers;
- persisted report/encounter/actors/participants;
- reviewed combatants observations;
- aura observations and reconstructed intervals for the report slice;
- independent supporting observations;
- contradicting evidence review;
- reproducible versioned provenance;
- green Ubuntu and Windows verification.
