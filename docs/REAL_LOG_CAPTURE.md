# Real CoA Logs capture protocol

## Purpose

This document defines privacy-safe real-data capture from `coa.ascensionlogs.gg`.

The goal is not to guess routes or mechanics. The goal is to:

1. obtain real response bodies;
2. archive them immutably;
3. record safe request shape and transport facts;
4. fingerprint JSON structures;
5. review mappings explicitly;
6. normalize reproducibly;
7. preserve supporting and contradicting evidence.

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

This full profile returned HTTP 200 for public reports, character search and Armory by-name in the verified diagnostic sequence.

Do not claim:

- the minimum header subset is known;
- cookies are unnecessary;
- request order is irrelevant;
- HTML bootstrap is required;
- authorization, browser TLS impersonation or HAR is always required.

## Autonomous collector rules

### Endpoint isolation

Real capture should be executable per endpoint.

Avoid a long all-or-nothing chain when one endpoint can block every later result.

Each endpoint attempt should:

1. use a bounded timeout;
2. use bounded retries only for retryable failures;
3. write a progressive safe result immediately;
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
- a partial body may be retained only under explicit diagnostic policy;
- do not treat partial bytes as valid evidence unless they form complete valid JSON and the policy explicitly permits it;
- never create a verified mapping from a transport-damaged payload.

## Current Armory checkpoint

Subject:

```text
Gunspojoshe
Vol'Jin
Tyrant
phase 0
World Bosses
normal
```

Identity:

```text
character_id: 156120
character_class: Felsworn
has_armory: true
identity_source: by_name
```

Successfully archived:

### by_name

```text
payload hash: a81bb54342ee1573017b314af418e54da3ec56c51131f62bd2dd5efe826d5cff
fingerprint: 108ea5ed6a659d7161904ab087b4631df0f5c2ec69f94e1f2d90cbbaeaea0c37
```

### captures

```text
payload hash: 34192051026d918ec0dcb311efc236c5873fda2f7748bc2acad128e5f5ec7851
fingerprint: e03d3b0d7c308ab4740280720cbaaaf60740a19e50826d23eb2194124397b814
```

Still missing:

```text
/api/armory/character/156120
/api/armory/talent-grid/felsworn
```

Both returned status 200 before body-read timeout. One run also produced an incomplete chunked transfer. The next capture implementation should request these endpoints independently with progressive output.

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
13. Store locally, for example:

```text
data/exchange/in/coa-report-YYYYMMDD.har
```

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

## Safe inventory fields

One row per response candidate may contain:

- ordinal;
- method;
- sanitized path;
- query key names only;
- HTTP status;
- content type;
- body encoding;
- uncompressed bytes;
- payload SHA-256;
- schema fingerprint;
- top-level JSON kind and keys;
- candidate collection paths;
- neutral candidate label;
- raw and observation IDs;
- duplicate flag;
- skip reason.

It must not contain:

- request or response header values;
- cookies;
- tokens;
- request bodies;
- query values;
- absolute local paths or usernames.

## Mapping gate

A mapping may be created only after selected payload inspection.

Required fields:

- exact schema fingerprint;
- explicit collection paths;
- explicit field mappings;
- provenance type;
- mapping ID/version;
- status `verified`;
- reviewed payload hash or equivalent source pointer.

Candidate or mismatched mappings remain rejected.

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

Prefer:

- report metadata;
- encounters;
- roster/combatants;
- aura timeline/detail/uptimes;
- casts;
- debuff sources.

Download full event streams only when compact endpoints cannot test the current hypothesis.

## First full checkpoint acceptance criteria

1. Real payloads retained locally and not committed.
2. Response bodies archived immutably.
3. Safe inventory generated.
4. Report and encounter payloads identified.
5. Roster/participant and aura candidates identified or explicitly absent.
6. Stable fingerprints recorded.
7. Mapping manually reviewed and marked `verified`.
8. One complete report/encounter normalized.
9. Actors, participants and aura events retain source pointers.
10. Aura State Engine output reproducible from archived hashes.
11. Anomalies and contradicting observations remain visible.
12. Independent supporting observations exist for any promoted gameplay mechanic.
13. Ubuntu and Windows verification are green.

## Non-goals until the checkpoint

- raid-wide scope inference;
- overwrite/stacking rules;
- class/spec provider assignment from one observation;
- planner scoring from observed/candidate data;
- uploading private logs;
- treating parser correctness as mechanic confirmation.
