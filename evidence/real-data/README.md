# Real-data evidence checkpoint

Дата актуализации: **2026-08-14**.

Каталог содержит versioned scalar-free receipts и explicit trust boundaries. Private payloads, source
rows, queries, raw JavaScript contexts, browser HAR, cookies, headers, private IDs and DuckDB remain
local-only unless an explicit reviewed publication contract says otherwise.

## Current canonical Network-first receipts

```text
coa-guild-phase-progression-browser-network.json
source-observatory-network-baseline-2026-08-14.json
source-observatory-derived-baseline-2026-08-14.json
```

Current runtime progression evidence:

```text
GET /api/phases                                      -> 200 JSON
GET /api/guilds/phase-progression?phase=...&difficulty=... -> 200 JSON
```

Current real local Observatory state recorded structurally by the derived receipt:

```text
observed endpoints: 2
active dependencies: 2
dimension names represented: 5
dimension values represented: 19
completed source_dimension_index runs: 1
same existing HAR replayed: true
new change events from replay: 0
new reanalysis requests from replay: 0
```

The actual dimension values are not published.

## Current progression correction

The historical guessed direct `POST /api/guilds/progression` helper/owner path is superseded.

Archived SPA evidence still contains alternate GET contracts:

```text
GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

They remain reviewed alternate contracts, not proof of current runtime use.

Older helper/call-site/owner receipts remain audit history and must not override the real browser
Network evidence.

## Guild/report baseline retained from earlier evidence

```text
public reports: 6454
unique report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
```

Private source guild ID and report IDs remain local.

## Source Observatory trust boundary

Current chain:

```text
browser/network observation
-> reviewed contract
-> immutable capture
-> schema/dimension snapshot
-> source change event
-> artifact dependency
-> scoped reanalysis request
-> deterministic derived analysis
```

The first real derived artifact is `source_dimension_index`.

A repeated identical HAR does not create fake change/reanalysis work. A genuinely later source change is
still required to prove the real end-to-end changed-input path.

## Local-only artifacts

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never commit credentials, cookies, tokens, Authorization headers, browser profiles, `.env`,
unsanitized HAR, private source identifiers, report IDs, private query values, raw JavaScript contexts
or raw private receipts.
