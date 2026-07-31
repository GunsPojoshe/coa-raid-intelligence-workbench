# Фактическое состояние проекта

Дата актуализации: **2026-07-31**.

Документ фиксирует изменяемое operational state. Перед работой перепроверять GitHub, код, local private artifacts, versioned receipts и CI.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Проверенный implementation baseline перед текущим documentation refresh:

```text
HEAD: 297895c5ce3b26ce2911befd9addf474ef3e1138
PR #7: open, Draft, mergeable
base: e2/log-evidence-refactor
commits: 449
changed files: 225
Verify repository run: #464
public-release-audit: success
Ubuntu: success
Windows: success
reported tests: 300 passed
```

Documentation refresh продвигает HEAD. Перед любой следующей задачей фактический HEAD и новый CI перепроверить.

PR #3:

```text
state: open
Draft: true
base: main
head: e2/log-evidence-refactor
head SHA: 4b42a7d0735ba1125e4f0ef14dd01422d4b55afc
```

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
- repository verifier, public-release audit и Ubuntu/Windows CI.

Normalization разрешена только при exact immutable payload, exact SHA-256, exact schema fingerprint и reviewed mapping/extractor contract. Parser/schema verification не подтверждает игровую механику. Planner scoring допускает только `corroborated` и `confirmed` mechanics.

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

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events, 0 rejects
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants, 0 field conflicts
persisted through 0007: 77 canonical entity observations
```

## Completed combatants persistence

```text
migration: migrations/0008_combatants_observation_persistence.sql
receipt: evidence/real-data/observed-combatants-info-persistence.json
immutable observations: 1343
actor/build observations: 1339
distinct linked actors: 11
integrity checks: 14/14
core actor mutations: 0
```

Read models:

```text
combatants_parser_observation_v1
combatants_actor_build_observation_v1
```

Still unverified: companion-addon provenance, nested collection semantics, global nested-ID uniqueness, talent/gear gameplay semantics, canonical build projection and planner use.

## Completed exhaustive public-report manifest

```text
receipt: evidence/real-data/argentum-public-report-manifest.json
route: /api/reports/public
limit: 25
sortBy: created_at
sortOrder: desc
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
terminal page reports: 4
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

The current versioned manifest SHA-256 is represented by the binding in downstream receipts. Do not reuse the older documentation-only SHA claim `ed2c...`; the snapshot review binds the current public receipt as:

```text
source_public_manifest_receipt_sha256:
aaad2a9301bdb6a8e2af62a04fc74083a3d1fcd255c293b72dba3d4953b49e57
```

## Completed snapshot identity review

```text
receipt: evidence/real-data/argentum-guild-identity-snapshot-review.json
exact label reports: 17
candidate guild-ID reports: 17
distinct exact-label guild IDs: 1
conflicting non-empty names: 0
integrity checks: 10/10
snapshot internal identity consistent: true
ready for independent source identity review: true
```

This verifies consistency inside the bound public/private snapshot. It does not independently verify that the candidate is the intended operator guild.

## Completed guild route and transport investigation

Initial route discovery could not retrieve the required application asset. The failures were classified rather than treated as identity evidence:

```text
asset timeout
curl TLS/network failure
HTTP Range ignored / partial-probe mismatch
minimal request profile: HTTP 403
```

Profiled recovery then succeeded:

```text
receipt: evidence/real-data/argentum-guild-asset-profiled-recovery.json
selected profile: http1_1
HTTP status: 200
asset bytes: 3881146
API route candidates: 79
guild route candidates: 3
```

Observed guild route shapes:

```text
/api/guilds/progression
/api/guilds/search?q=<value>
/api/guilds/search?q=<value>&limit=<value>
```

These are reviewed route candidates. Guild API route semantics remain unverified.

## Completed guild-search capture and mapping chain

Access diagnostic showed:

```text
minimal_http1_1: HTTP 403
spa_fetch_context: HTTP 200
```

The captured search response contains one `guilds[]` object. Schema inventory:

```text
receipt: evidence/real-data/argentum-guild-search-schema-inventory.json
guild objects: 1
field entries: 5
casefold label matches: 1
source ID matches: 1
integrity checks: 15/15
```

Reviewed object shape:

```text
guilds[]
├── id           integer
├── name         string
├── realm        string
└── report_count string
```

Mapping review:

```text
receipt: evidence/real-data/argentum-guild-search-mapping-review.json
mapped fields: 4
guild search results: 1
source ID matches: 1
name casefold matches: 1
integrity checks: 13/13
cross-endpoint candidate: true
```

Reviewed semantic mapping:

```text
$.guilds[].id           -> guild_id
$.guilds[].name         -> guild_name
$.guilds[].realm        -> realm
$.guilds[].report_count -> report_count
```

The manifest candidate and guild-search object share the same source ID in private evidence, and the names match after Unicode casefold. Raw payload, guild ID and other source scalars are absent from the public receipts.

## Implemented explicit guild identity decision

Code:

```text
scripts/decide_guild_identity.py
src/coa_workbench/collector/guild_identity_decision.py
```

The decision cannot run without:

```text
--promote-identity
```

It revalidates:

- public manifest contract;
- exact private manifest SHA-256;
- all 6454 private report rows and uniqueness;
- 17 target rows and single source ID;
- absence of conflicting names;
- public/private snapshot review bindings;
- public/private guild-search mapping bindings;
- cross-endpoint ID equality;
- name equality after casefold;
- scalar-free public decision boundary.

Expected successful boundary:

```text
independent_source_identity_verified: true
guild_identity_verified: true
ready_for_guild_filtering: true
guild_api_route_semantics_verified: false
ready_for_full_guild_crawl: false
ready_for_multi_report_character_graph: false
ready_for_performance_model: false
ready_for_bis25_scoring: false
planner_scoring_allowed: false
```

## Current boundary

Verified now:

- exhaustive public snapshot and pagination contract;
- snapshot-internal Argentum candidate consistency;
- profiled asset recovery;
- candidate guild-search route shape;
- one reviewed guild-search object;
- reviewed four-field mapping;
- cross-endpoint identity candidate;
- explicit non-automatic promotion mechanism.

Not yet verified:

```text
guild identity verified: false
ready for guild filtering: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

The only missing step for the identity boundary is the local explicit decision receipt. Do not claim identity verification from code existence alone.

## Next bounded task

Run locally:

```text
scripts/decide_guild_identity.py --promote-identity
```

Then review only:

```text
data/exchange/out/argentum-guild-identity-decision.json
```

Do not upload or commit:

```text
data/extracted/report-discovery/argentum-guild-identity-decision.private.json
```

After a successful scalar-free receipt:

1. validate all integrity checks and source bindings;
2. add the public receipt to `evidence/real-data/`;
3. update docs and PR #7 to the promoted identity boundary;
4. implement deterministic filtering by verified source guild ID;
5. produce a deduplicated guild report manifest;
6. keep full crawl and scoring closed until their separate contracts are satisfied.

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

Versioned: code/tests, migrations, reviewed mappings, canonical documentation and scalar-free evidence receipts.

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

Never commit secrets, cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR, source-scalar private packets or absolute user paths.

## Completion gate

PR #7 remains Draft. Identity promotion opens only guild filtering. Full guild crawl, character graph, performance model, mechanics promotion and planner scoring require separate verified evidence and boundaries.