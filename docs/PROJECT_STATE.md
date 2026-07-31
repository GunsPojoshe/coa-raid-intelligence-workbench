# Фактическое состояние проекта

Дата актуализации: **2026-07-31**.

Этот документ фиксирует изменяемое operational state. Перед работой перепроверять GitHub, код, local private artifacts, versioned receipts и CI.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Green baseline перед documentation refresh:

```text
commit: 00bae9ac4deb457eebc41cd50bdff6305bf3fe42
workflow: Verify repository
run: #372
Ubuntu: success
Windows: success
```

PR #7 остаётся open, Draft и mergeable.

## Реализованный фундамент

### Product runtime

- localhost FastAPI application;
- browser raid constructor FLEX / 10 / 25 / 40;
- Python validation и class/spec/role catalog;
- DuckDB raid-plan persistence и CRUD;
- request IDs и diagnostic logging;
- localhost-only bind по умолчанию.

### Evidence runtime

- source registry и safe probes;
- immutable content-addressed raw archive;
- отдельные retrieval observations;
- JSON/HAR import и privacy-safe inventory;
- schema fingerprints;
- versioned verified mappings;
- report/encounter/actor/participant/aura records;
- normalization rejects и Aura State Engine;
- hypotheses, supporting/contradicting evidence и trust policies;
- migrations `0001`–`0008`;
- repository verifier и Ubuntu/Windows CI.

## Trust boundary

Normalization разрешена только при exact immutable payload, exact SHA-256, exact schema fingerprint и reviewed mapping со статусом `verified`.

Parser/schema verification не подтверждает игровую механику. Canonical planner scoring допускает только `corroborated` и `confirmed` mechanics.

## Verified mappings and routes

Production-ready mappings:

```text
config/mappings/coa_armory_character_v1.json
config/mappings/coa_armory_talent_grid_v1.json
config/mappings/coa_public_report_discovery_v1.json
config/mappings/coa_report_detail_v1.json
config/mappings/coa_encounter_detail_v1.json
```

Observed report routes:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

Отдельный `/roster` route не наблюдался.

## Completed report/encounter parser slice

Exact payload bindings:

```text
report_detail
payload:     161739896f0b8321f884bcc24d1896efb894a9c6e05166269189f9871c64cba9
fingerprint: 3d533a4178b67957bbd31544ddf5484bd5959635ebd5edcdd0c7689a4bace216

encounter_detail
payload:     955437d6c9c287cc7db280dd2388b88603af2785508061b95c7811dcd272fe22
fingerprint: 567f36824efb37a29b835df01ce9b1fcc79eae57d6230202d16a6265c6ca0e85

combatants_info
payload:     45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14
fingerprint: 41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff
```

Normalization:

```text
reports: 2
encounters: 15
actors: 31
participants: 31
aura events: 0
rejects: 0
```

Reconstruction:

```text
reports: 1
encounters: 14
actors: 31
participants: 31
aura events: 0
rejects: 0
field conflicts: 0
linkage checks: 9/9
```

Persistence through migration `0007_selected_parser_persistence`:

```text
reports: 1
encounters: 14
actors: 31
participants: 31
canonical entity observations: 77
normalization mappings: 2
normalization runs: 2
observation batches: 2
rejects: 0
transaction committed: true
```

## Completed combatants persistence

Migration:

```text
migrations/0008_combatants_observation_persistence.sql
```

Versioned receipt:

```text
evidence/real-data/observed-combatants-info-persistence.json
```

Persisted state:

```text
immutable observations: 1343
persistence runs: 1
actor/build observations: 1339
parser observations: 1343
distinct linked actors: 11
integrity checks: 14/14
core actor mutations: 0
```

Per entity type:

```text
actor enrichment: 11
instance context: 4
talent container: 11
classless talent rank: 564
hero build entry: 564
gear slot: 189
```

Read models:

```text
combatants_parser_observation_v1
combatants_actor_build_observation_v1
```

Still unverified:

- companion-addon provenance;
- nested collection semantics and global identifier uniqueness;
- talent/gear gameplay semantics;
- canonical player/build projection policy;
- mechanic semantics and planner scoring.

## Completed exhaustive public-report manifest

Versioned receipt:

```text
evidence/real-data/argentum-public-report-manifest.json
receipt SHA-256: ed2c8884ce8d9a96b26d25eea269f71a85aadd34c5e2a6f42362dbd41be19796
```

Request contract:

```text
route: /api/reports/public
limit: 25
sortBy: created_at
sortOrder: desc
first page: 1
terminal page: 259
successor page: 260
```

Manifest result:

```text
completed pages: 259
full pages: 258
terminal page reports: 4
expected reports: 6454
report occurrences: 6454
unique report IDs: 6454
duplicates: 0
integrity checks: 19/19
sentinels: 5/5 stable
```

Guild-field result:

```text
reports with both guild fields: 1171
distinct guild identity pairs: 88
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

Decision boundary:

```text
manifest complete: true
guild identity verified: false
ready for guild identity review: true
ready for guild filtering: false
ready for full guild crawl: false
ready for multi-report character graph: false
planner scoring allowed: false
```

The receipt proves completeness and integrity of the captured public snapshot. It does not prove that the one guild ID associated with the `Argentum` label is the operator's intended guild.

## Aura checkpoint

Separate real fixtures for report `2987`, spell `968746` verify technical normalizer/Aura State Engine behavior:

```text
encounter 64795: 6 events -> 3 intervals
encounter 64796: 3 events -> 2 intervals
0 rejects
0 anomalies
```

The selected report slice still contains zero aura events and does not verify gameplay mechanics.

## Data and Git policy

Versioned:

- source code and tests;
- migrations;
- reviewed mappings;
- canonical documentation;
- scalar-free evidence receipts.

Local-only:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never commit secrets, cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR or absolute user paths.

## Current blockers

1. The source guild identity behind the 17 exact `Argentum` reports is not manually verified.
2. Guild filtering and full guild crawl remain disabled.
3. Multi-report character identity has not been reviewed.
4. Companion-addon provenance and nested combatants semantics remain unverified.
5. The bounded report slice contains no aura events.
6. No new gameplay mechanic has independent supporting and contradicting evidence.
7. Planner scoring remains correctly disabled for observed/parser data.

## Next bounded task

Perform a local guild-identity review:

1. load the exact private manifest bound by `source_private_manifest_sha256`;
2. isolate the 17 rows whose normalized `guild_name` exactly equals `Argentum`;
3. verify all 17 map to the same non-null source guild ID;
4. inspect available independent source evidence for that ID;
5. do not use title, uploader or nickname as identity proof;
6. produce a scalar-free review receipt containing hashes, counts and the decision, not the raw guild ID;
7. enable guild filtering only after explicit manual promotion.

## Completion gate

PR #7 remains Draft until the relevant checkpoint includes reviewed guild identity, deterministic guild filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows verification.
