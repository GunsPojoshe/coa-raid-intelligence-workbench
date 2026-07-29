# Real CoA Logs capture and persistence protocol

Дата актуализации: **2026-07-30**.

## Purpose

Этот документ определяет безопасный и воспроизводимый путь от real response `coa.ascensionlogs.gg` до canonical observations.

Цель:

1. получить complete real response;
2. сохранить его immutably;
3. зафиксировать safe transport facts;
4. вычислить exact SHA-256 и schema fingerprint;
5. выполнить structural/field review;
6. создать и проверить mapping;
7. вручную разрешить publication;
8. нормализовать и реконструировать;
9. сохранить provenance;
10. не превращать parser result в gameplay claim.

## Canonical pipeline

```text
HTTP response
-> immutable raw payload
-> retrieval observation manifest
-> structural review
-> mapping review / field selection
-> candidate mapping or dedicated extractor design
-> exact raw validation
-> manual promotion/publication
-> normalization/extraction
-> deterministic reconstruction/deduplication
-> atomic persistence
-> scalar-free receipt
```

## Capture paths

### Preferred: autonomous HTTP collector

Use:

```text
coa-fetch-context-v1
```

Requirements:

- persistent same-origin session;
- in-memory cookie jar only;
- bounded timeout;
- at most bounded retry policy;
- endpoint-isolated execution;
- progressive safe manifest;
- archive complete body before interpretation;
- distinguish HTTP status from complete body read;
- preserve transport errors;
- never store cookie/header values.

Safe metadata may include:

- profile version;
- request header names;
- sanitized route shape;
- status and content type;
- byte count;
- transport warning;
- payload hash;
- schema fingerprint.

### Fallback: browser HAR

HAR is sensitive even in a private repository.

- store under `data/exchange/in/`;
- never commit unsanitized HAR;
- never paste cookies, Authorization headers or tokens;
- inventory/import only through the safe tooling;
- archive only allowed-host non-empty response bodies;
- keep skip reasons for malformed entries.

## Raw archive contract

Raw payload:

- immutable;
- content-addressed by SHA-256;
- gzip-compressed when JSON;
- one body per content hash;
- separate observation per retrieval;
- schema-fingerprinted when valid JSON;
- linked to sanitized request metadata.

Do not alter archived bytes to satisfy tests.

## Mapping contract

Mapping may be published only when:

```text
exact archived payload
+ exact payload hash
+ exact schema fingerprint
+ explicit collection/field selectors
+ reviewed occurrence/type/nullability facts
+ manual reviewer metadata
+ successful dry run
+ mapping status verified
```

Unknown hash/fingerprint must be rejected and reviewed separately.

A verified mapping confirms parser compatibility only.

## Current verified Armory checkpoint

Mappings:

```text
config/mappings/coa_armory_character_v1.json
config/mappings/coa_armory_talent_grid_v1.json
```

Both are exact-archive validated and production-ready for their reviewed schemas.

Deferred gear, hero-build and empty-array item schemas remain outside the verified contract.

## Current verified public-report discovery

Observed request:

```text
GET /api/reports/public
page=1
limit=5
sortBy=created_at
sortOrder=desc
```

Mapping:

```text
config/mappings/coa_public_report_discovery_v1.json
status: verified
selected fields: 7
```

The collector performs one explicit page per invocation and does not infer pagination/category semantics.

## Current report-slice capture

Observed routes:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

No separate `/roster` route was observed.

### Exact payload bindings

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

## Report and encounter production parser

Published mappings:

```text
config/mappings/coa_report_detail_v1.json
config/mappings/coa_encounter_detail_v1.json
```

The publication gate verified 54 field contracts and enabled selected-parser normalization only for the exact reviewed routes/hashes/fingerprints.

It did not enable combatants or aura semantics.

### Normalization result

```text
reports:       2
encounters:   15
actors:       31
participants: 31
aura_events:   0
rejects:       0
```

### Reconstruction result

```text
reports:       1
encounters:   14
actors:       31
participants: 31
aura_events:   0
rejects:       0
field conflicts: 0
```

### Persistence result

Migration:

```text
0007_selected_parser_persistence
```

```text
reports:                       1
encounters:                   14
actors:                       31
participants:                 31
canonical entity observations:77
transaction committed:         true
```

The local normalized/reconstructed files and DuckDB contain private source scalars and remain gitignored.

## Combatants-info review pipeline

Stages completed:

```text
full-root structural review
-> deep bounded scope review
-> manual field selection
-> storage-aware mapping design
-> dedicated candidate extraction dry run
```

Deep review:

```text
scope candidates: 12
present:          10
required:          4/4
direct fields:    56
```

Selection:

```text
groups:          8
selected fields:37
deferred fields:19
```

Design:

```text
6 dedicated extractors
immutable canonical_entity_observation targets
core actor mutation forbidden
```

### Candidate extraction result

```text
source matches:       1350
output observations:  1343
deduplicated matches: 7
linked actors:        11
actor-name matches:   11
integrity checks:     12/12
core mutations:       0
```

Per unit:

```text
actor enrichment:       11
instance context:         4
talent container:        11
classless talent ranks: 564
hero build entries:     564
gear slots:             189
```

The private extraction batch is local. The scalar-free receipt is versioned at:

```text
evidence/real-data/observed-combatants-info-candidate-extraction.json
```

### Combatants boundary

Verified for exact payload:

- archive and observation manifest;
- route context;
- persisted report/encounter references;
- stable actor IDs;
- exact existing actor names;
- selected JSON types;
- source counts;
- record hashes;
- no core mutation.

Not verified:

- companion-addon provenance;
- nested ID uniqueness;
- gameplay meaning of talents/gear;
- canonical build snapshot semantics;
- automatic persistence/promotion;
- planner scoring.

## Next persistence protocol

The next implementation must:

1. validate the versioned candidate extraction receipt and private file hash;
2. create a manual promotion packet for parser observations;
3. verify that migration `0007` can preserve all required provenance;
4. add a new migration only for a demonstrated storage gap;
5. persist the six observation types atomically and idempotently;
6. never mutate core actor rows;
7. create a scalar-free persistence receipt;
8. keep all semantic/trust boundaries closed.

## Aura capture gap

The current report slice contains no aura events.

Separate real fixtures for spell `968746` validate Aura State Engine technical behavior, but they do not complete the report slice and do not prove gameplay mechanics.

Future aura work must:

- observe exact aura-related route(s);
- archive exact payloads;
- review event fields/types;
- publish verified mappings;
- normalize source-linked aura events;
- reconstruct intervals;
- compare supporting and contradicting observations.

## Local commands by stage

Repository verification:

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Capture/review scripts are intentionally explicit and versioned under `scripts/`. Run their `--help` before a new payload/schema and never reuse a receipt with a mismatched hash.

## Data policy

The repository is private and full local data may be used for development, but Git remains evidence-minimal.

Versioned:

- mappings;
- code/tests;
- migrations;
- documentation;
- scalar-free receipts.

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

Never commit credentials, cookies, tokens, browser profiles, `.env` secrets or unsanitized HAR.

## Acceptance criteria for E3

- exact real payloads retained locally;
- stable hashes/fingerprints;
- reviewed/published required parsers;
- persisted report/encounter/actors/participants;
- reviewed combatants observations;
- aura observations for the bounded report slice;
- deterministic interval reconstruction;
- independent supporting observations;
- contradicting evidence review;
- versioned provenance;
- green Ubuntu and Windows CI.
