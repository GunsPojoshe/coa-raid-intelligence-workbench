# Real CoA Logs capture protocol

## Purpose

This document defines privacy-safe real-data capture from `coa.ascensionlogs.gg`.

The goal is not to guess routes or mechanics. The goal is to:

1. obtain real response bodies;
2. archive them immutably;
3. record safe request shape and transport facts;
4. fingerprint JSON structures;
5. review mappings explicitly;
6. validate mappings against exact archives;
7. normalize reproducibly;
8. preserve supporting and contradicting evidence.

## Capture paths

### Preferred path: autonomous HTTP collector

Use the versioned same-origin profile:

```text
coa-fetch-context-v1
```

It includes the verified full header set and one persistent same-origin session with an in-memory cookie jar.

The collector must never archive cookie values or request-header values. Safe metadata may include:

- profile version;
- request header names;
- sanitized route shape;
- HTTP status;
- content type;
- transport warning;
- response byte count;
- payload hash;
- schema fingerprint.

### Fallback path: browser HAR

HAR remains a fallback when the autonomous collector cannot obtain a required payload.

A HAR may contain cookies, authorization headers, identifiers and private URLs.

- Never commit a HAR.
- Never attach an unsanitized HAR to GitHub or chat.
- Store it only under a gitignored local path such as `data/exchange/in/`.
- Do not copy authentication headers into configuration.
- The original HAR remains sensitive after import.

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

This full profile returned HTTP 200 for public reports, character search, Armory by-name, character detail and talent grid in the verified capture sequence.

Do not claim:

- the minimum header subset is known;
- cookies are unnecessary;
- request order is irrelevant;
- HTML bootstrap is required;
- authorization, browser TLS impersonation or HAR is always required.

## Autonomous collector rules

### Endpoint isolation

Real capture must be executable per endpoint.

Each endpoint attempt should:

1. use a bounded timeout;
2. use bounded retries only for retryable failures;
3. write progressive safe result state;
4. archive a completed body before interpretation;
5. preserve transport warnings;
6. continue or stop according to explicit policy;
7. allow resume without re-fetching successful payloads.

### Status is not body completion

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

If a transfer ends with `IncompleteRead`, timeout or disconnect:

- do not crash the entire batch;
- record the transport error;
- do not treat partial bytes as valid evidence unless they form complete valid JSON and policy explicitly permits it;
- never create a verified mapping from a transport-damaged payload.

## Current Armory checkpoint

Subject:

```text
character_id: 156120
class_slug: felsworn
```

### Character

```text
route: /api/armory/character/156120
HTTP: 200
bytes: 59910
payload hash: 2a9d752d7af72d41cd9d41836d670069c78e408df7260f5d9caa83b07430985f
schema fingerprint: efbcf618291d824667ba586c22af4ed031fa146d69b11a5539ec17a41d042621
top-level keys: capture, ci_resolved, stats_summary, success
```

### Talent grid

```text
route: /api/armory/talent-grid/felsworn
HTTP: 200
bytes: 63025
payload hash: 11be25407ec00898547c1b7f342d4596268b3164df9fe0f120bb911559cc5206
schema fingerprint: 7e3b3bfc3966ddc5d0160c8d466e5ba92edbe55440449619d7204102a25b3240
top-level keys: class_name, success, trees
```

Capture manifest:

```text
data/exchange/out/armory-endpoint-capture.json
```

The manifest and raw archives remain local and gitignored.

## Structural and mapping review

Structural review verifies archive integrity without exposing scalar values:

```powershell
uv run --no-sync python scripts/review_armory_capture.py `
    --manifest "data\exchange\out\armory-endpoint-capture.json" `
    --raw-root "data\raw" `
    --output "data\exchange\out\armory-structural-review.json"
```

Mapping-review packet:

```powershell
uv run --no-sync python scripts/build_armory_mapping_review.py `
    --manifest "data\exchange\out\armory-endpoint-capture.json" `
    --raw-root "data\raw" `
    --output "data\exchange\out\armory-mapping-review-v2.json" `
    --max-nodes 100000
```

Reviewed packet schema `2`:

```text
archive_verified: 2
field_path_count: 470
node_occurrence_count: 6106
numeric_map_path_count: 4
contains_source_scalar_values: false
ready_for_manual_mapping_review: true
```

Review decisions are recorded in:

```text
docs/ARMORY_MAPPING_REVIEW_V1.md
```

## Candidate mappings

```text
config/mappings/coa_armory_character_v1.json
config/mappings/coa_armory_talent_grid_v1.json
```

Candidate status is intentional. `require_verified()` rejects both mappings from production use.

Review preserves source-specific identifiers instead of inventing semantics:

- `cao_id` -> `source_cao_id`;
- `bisbeard_tree` -> `source_bisbeard_tree`.

Talent records, connection records and rank-text records preserve parent talent/tree relationships through ancestor selectors.

Deferred scopes include detailed gear, hero build, derived stat internals and item schemas for currently empty `lock_rules` and `rank_spell_ids` arrays.

## Raw-archive mapping validation

Type-only review is necessary but not sufficient for promotion.

Run the validator against the exact immutable archives:

```powershell
uv run --no-sync python scripts/validate_armory_mappings.py `
    --review "data\exchange\out\armory-mapping-review-v2.json" `
    --manifest "data\exchange\out\armory-endpoint-capture.json" `
    --raw-root "data\raw" `
    --output "data\exchange\out\armory-mapping-validation.json"
```

The validator checks:

1. review packet schema and privacy flags;
2. structural manifest against immutable archives;
3. payload SHA-256;
4. schema fingerprint;
5. route template;
6. singleton selector extraction;
7. collection occurrence counts;
8. `@item`, `@index` and `@ancestor[n]` selectors;
9. required field presence;
10. observed JSON types.

Expected result before promotion:

```text
schema_version: 2
all_structurally_consistent: true
all_raw_archives_consistent: true
all_production_ready: false
mapping_count: 2
```

`all_production_ready: false` remains correct while mappings are `candidate`.

The validation output contains counts and reproducibility identifiers, not source scalar values.

## Promotion gate

A candidate Armory mapping may be promoted only after:

1. exact archive validation succeeds;
2. compact output is reviewed;
3. mapping semantics remain bounded to source structure;
4. deferred scopes remain explicit;
5. a separate commit changes status to `verified`;
6. `reviewed_by` and `reviewed_at` are recorded;
7. repository CI is green.

Verified mapping means reproducible extraction from the reviewed source schema. It does not confirm runtime magnitude, stacking, overwrite, scope, provider equivalence or planner criticality.

## Browser HAR capture

Use Chrome or another Chromium browser only when the autonomous path is insufficient.

1. Open a real report with at least one completed encounter.
2. Sign in only if required.
3. Open Developer Tools with `F12`.
4. Open Network.
5. Enable Preserve log.
6. Enable Disable cache while DevTools is open.
7. Clear the request list.
8. Reload.
9. Open one completed encounter.
10. Visit relevant summary, roster, casts, aura/buff/debuff views.
11. Wait for visible requests to complete.
12. Save all as HAR with content.
13. Store locally under `data/exchange/in/`.

Do not rename the HAR to JSON and do not edit it before import.

## HAR import and inventory

```powershell
uv run coa-workbench init-db
uv run coa-workbench import-har data/exchange/in/coa-report-YYYYMMDD.har
uv run coa-workbench inventory-har data/exchange/in/coa-report-YYYYMMDD.har `
  --output data/exchange/out/coa-report-inventory.json
```

The import/inventory must:

- accept only the configured source host;
- archive non-empty response bodies by SHA-256;
- keep observations separate from payload bodies;
- sanitize URLs;
- record status/content type/fingerprint;
- avoid request headers and cookies;
- isolate malformed entries;
- retain skip reasons.

## Automated report capture target

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

Prefer report metadata, encounters, roster/combatants, aura timeline/detail/uptimes, casts and debuff sources.

Download full event streams only when compact endpoints cannot test the current hypothesis.

## First full checkpoint acceptance criteria

1. Real payloads retained locally and not committed.
2. Response bodies archived immutably.
3. Safe inventories generated.
4. Stable fingerprints recorded.
5. Mappings reviewed, raw-validated and marked `verified`.
6. One complete report/encounter normalized.
7. Actors, participants and aura events retain source pointers.
8. Aura State Engine output reproducible from archived hashes.
9. Anomalies and contradicting observations remain visible.
10. Independent supporting observations exist for promoted gameplay mechanics.
11. Ubuntu and Windows verification are green.

## Non-goals until the checkpoint

- raid-wide scope inference;
- overwrite/stacking rules;
- class/spec provider assignment from one observation;
- planner scoring from observed/candidate data;
- uploading private logs;
- treating parser correctness as mechanic confirmation.
