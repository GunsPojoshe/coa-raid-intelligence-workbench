# Real CoA Logs capture protocol

## Purpose

This document defines privacy-safe real-data capture from `coa.ascensionlogs.gg`.

The pipeline is:

1. obtain a real response body;
2. archive it immutably;
3. record safe request and transport facts;
4. fingerprint the JSON structure;
5. review mappings explicitly;
6. normalize only through a verified mapping;
7. preserve supporting and contradicting evidence.

Do not guess routes, fields, pagination or gameplay mechanics.

## Preferred capture path

Use the autonomous collector with the versioned same-origin profile:

```text
coa-fetch-context-v1
```

The implementation uses one persistent same-origin session and an in-memory cookie jar.

Safe output may contain:

- HTTP profile version;
- request header names, never values;
- sanitized route shape;
- HTTP status;
- content type;
- transport warning;
- response byte count;
- payload SHA-256;
- schema fingerprint;
- relative archive path.

Never archive or emit cookie values, authorization values or private query values.

## HAR fallback

HAR remains a fallback only when autonomous capture cannot obtain a required payload.

A HAR can contain cookies, credentials, identifiers and private URLs.

- Never commit a HAR.
- Never attach an unsanitized HAR to GitHub or chat.
- Store it under a gitignored local path such as `data/exchange/in/`.
- Do not copy authentication headers into configuration.
- Treat the original HAR as sensitive after import.

## Verified HTTP profile

```text
Accept: application/json, text/plain, */*
Accept-Language: en-US,en;q=0.9
Cache-Control: no-cache
Pragma: no-cache
User-Agent: Chromium-like
Referer: https://coa.ascensionlogs.gg/
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
```

The complete profile has returned HTTP 200 for public reports, character search, Armory by-name and the endpoint-isolated character/talent-grid capture sequence.

Do not claim:

- the minimum required header subset is known;
- cookies are unnecessary;
- request order is irrelevant;
- HTML bootstrap is required;
- authorization, browser TLS impersonation or HAR is always required.

## Autonomous collector rules

### Endpoint isolation

Real capture must be executable per endpoint. Avoid a long all-or-nothing chain.

Each endpoint attempt must:

1. use a bounded timeout;
2. use bounded retries only for retryable failures;
3. write progressive safe state immediately;
4. archive a completed body before interpretation;
5. preserve transport warnings;
6. support resume without re-fetching already verified payloads;
7. verify reused gzip, SHA-256, byte count and fingerprint.

### HTTP status is not body completion

These are separate facts:

```text
HTTP status received
response body read completed
valid JSON parsed
raw payload archived
schema fingerprint recorded
```

HTTP 200 alone is not a successful evidence capture.

### Partial bodies

For `IncompleteRead`, timeout or disconnect:

- do not crash the whole batch;
- record the transport error;
- do not treat partial bytes as valid evidence;
- never create a verified mapping from transport-damaged data.

## Current Armory checkpoint

Subject:

```text
character_id: 156120
character_class: Felsworn
realm: Vol'Jin
class_slug: felsworn
http_profile_version: coa-fetch-context-v1
```

### character

```text
route: /api/armory/character/156120
HTTP: 200
bytes: 59910
payload hash: 2a9d752d7af72d41cd9d41836d670069c78e408df7260f5d9caa83b07430985f
schema fingerprint: efbcf618291d824667ba586c22af4ed031fa146d69b11a5539ec17a41d042621
top-level keys: capture, ci_resolved, stats_summary, success
```

### talent_grid

```text
route: /api/armory/talent-grid/felsworn
HTTP: 200
bytes: 63025
payload hash: 11be25407ec00898547c1b7f342d4596268b3164df9fe0f120bb911559cc5206
schema fingerprint: 7e3b3bfc3966ddc5d0160c8d466e5ba92edbe55440449619d7204102a25b3240
top-level keys: class_name, success, trees
```

Both payloads were:

- captured independently;
- written to a progressive/resumable manifest;
- stored locally as immutable gzip JSON;
- verified by hash, byte count, fingerprint and relative archive path;
- kept out of Git.

Earlier timeout and incomplete-transfer observations remain valid historical transport observations, but they are no longer current blockers.

## Structural review

The structural review verifies:

- manifest endpoint state;
- expected payload hash;
- expected schema fingerprint;
- uncompressed byte count;
- safe relative archive location;
- candidate collection paths.

It does not claim gameplay semantics.

## Type-only mapping review packet

The mapping review packet reads only verified local archives and emits no source scalar values.

Current packet:

```text
schema_version: 2
endpoint_count: 2
archive_verified: 2
field_path_count: 470
node_occurrence_count: 6106
numeric_map_path_count: 4
contains_source_scalar_values: false
ready_for_manual_mapping_review: true
```

Endpoint summary:

```text
character: 445 paths, 3312 node occurrences, 4 numeric maps
talent_grid: 25 paths, 2794 node occurrences
```

Numeric object maps such as gear slots and build entries are represented with wildcard paths rather than one schema path per numeric key.

## Candidate Armory mappings

```text
config/mappings/coa_armory_character_v1.json
config/mappings/coa_armory_talent_grid_v1.json
```

Both mappings:

- are bound to exact payload hash and schema fingerprint;
- record review packet schema version `2`;
- declare paths, observed types, nullability and occurrence counts;
- retain `upstream_derived` provenance;
- have status `candidate`;
- are rejected by the production gate until explicitly verified.

Local validation checkpoint:

```text
all_structurally_consistent: true
all_production_ready: false
mapping_count: 2
```

`all_production_ready: false` is expected for candidate mappings.

### Character mapping scope

Included:

- capture and encounter context;
- player identity/basic context;
- active specialization index;
- selected talent ranks;
- primary, offensive, defensive and resistance summaries.

Deferred:

- detailed gear semantics;
- hero-build semantics;
- internal character talent-tree representation;
- `_gearOnly`, `derived`, `raw` and `sourcesByStat` computational internals.

### Talent-grid mapping scope

Included:

- trees;
- talent nodes;
- talent/spell IDs;
- names and icons;
- coordinates and node type;
- maximum ranks;
- nullable group ID;
- connected node IDs;
- rank text.

Deferred:

- `lock_rules` item schema;
- `rank_spell_ids` item schema.

Both arrays were empty in the reviewed payload, so their future element structure is not established.

## Mapping gate

A mapping may become production-ready only after manual review.

Required:

- exact schema fingerprint;
- reviewed payload hash;
- explicit paths and field contracts;
- provenance type;
- mapping ID/version;
- status `verified`;
- explicit reviewer and review timestamp.

Candidate or mismatched mappings remain rejected.

A verified mapping confirms parser/schema compatibility only. It does not confirm a gameplay mechanic.

## Validation commands

Build review packet:

```powershell
uv run --no-sync python scripts/build_armory_mapping_review.py `
  --manifest data/exchange/out/armory-endpoint-capture.json `
  --raw-root data/raw `
  --output data/exchange/out/armory-mapping-review-v2.json
```

Validate candidate mappings:

```powershell
uv run --no-sync python scripts/validate_armory_mappings.py `
  --review data/exchange/out/armory-mapping-review-v2.json `
  --output data/exchange/out/armory-mapping-validation.json
```

The generated review and validation files remain local and gitignored.

## Automated report capture target

The target is not manual download of every full log.

```text
/api/reports/public
-> verified filters and pagination
-> deterministic bounded selection, default up to 5 reports/category
-> encounter discovery
-> selected analytical endpoints
-> immutable archive
-> fingerprint
-> reviewed endpoint/schema parser
-> canonical normalization
```

Prefer report metadata, encounters, roster/combatants, aura timeline/detail/uptimes, casts and debuff sources. Download full event streams only when compact endpoints cannot test the current hypothesis.

## First full checkpoint acceptance criteria

1. Real payloads retained locally and not committed.
2. Response bodies archived immutably.
3. Stable fingerprints recorded.
4. Mapping manually reviewed and marked `verified`.
5. One complete report/encounter normalized.
6. Actors, participants and aura events retain source pointers.
7. Aura State Engine output is reproducible from archived hashes.
8. Anomalies and contradicting observations remain visible.
9. Independent supporting observations exist for any promoted gameplay mechanic.
10. Ubuntu and Windows verification are green.

## Non-goals until the checkpoint

- raid-wide scope inference;
- overwrite/stacking rules;
- provider assignment from one observation;
- planner scoring from observed/candidate data;
- uploading private logs;
- treating parser correctness as mechanic confirmation.
