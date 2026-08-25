# Current paradigm — CoA Raid Intelligence Workbench

Status: **canonical operating model**  
Updated: **2026-08-26**

This document defines the current project paradigm. If an older milestone/handoff document describes a different acquisition priority, this document and `docs/PROJECT_STATE.md` take precedence.

## Product question

The product exists to answer, with traceable evidence:

> **Почему конкретный человек нужен именно текущему составу?**

The answer is not allowed to collapse into a raw DPS ranking. It must eventually combine composition state, player/build state, encounter needs, population evidence and corroborated mechanic/utility knowledge.

## Evidence-first rule

The system may automate:

```text
source discovery
-> reviewed source/request contracts
-> immutable raw capture
-> structural/schema observation
-> deterministic normalization
-> provenance + dependency tracking
-> scoped reanalysis
-> reproducible analytics
-> Source & Analysis Health
```

The system must not automatically promote:

```text
field name -> gameplay meaning
UI label -> backend contract
character name -> cross-report identity
one report -> universal mechanic
one structural match -> semantic equivalence
population metric -> planner recommendation
```

Unknown semantics remain unknown until separately corroborated.

## Source priority

For facts covered by more than one source, prefer the strongest available evidence in this order:

```text
1. official documented CoA Ascension Logs public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API responses
5. narrow browser/network observation for undocumented gaps
6. structural inference only after stronger sources are exhausted
```

This is a priority order, not a replacement policy. Different sources answer different questions.

## Four acquisition lanes

### A. Official aggregate statistics — primary population lane

Official API contract:

```text
https://coa.ascensionlogs.gg/api/public/v1/openapi.json
OpenAPI 3.1.0
API version 1.0.0
```

Self-service `stats:read`:

```text
GET /phases
GET /bosses
GET /statistics
```

Use this lane for documented aggregate dimensions and population priors. It does not prove individual mechanics and does not expose the site Tier List algorithm.

Current real evidence proves:

```text
3 phase records
1 active/current phase candidate
285 bosses
285 unique stable boss_id values
successful current-phase /statistics capture
real StatisticsResponse shape reviewed
statistics normalization ready
```

The exact statistics normalization, migration-0013 persistence and population-prior read model are now implemented and deterministic-test verified. The remaining real gate is one new bounded capture with complete private request-scope provenance followed by two-pass persistence replay.

### B. First-party report evidence — private report-specific lane

The existing E3 report pipeline remains valid for report-specific evidence, deterministic analytics and source-observability work. Historical two-report difficulty equivalence is still `insufficient_evidence`; do not use those two reports for numeric cross-report scoring until that independent gate is proven.

### C. Pinned Companion source — client-state lane

`FangYuanWoW/AscensionLogsCompanion` is a strong executable source for what the client can observe and emit. It is especially valuable for client-state fields not exposed by public API v1: build/talent/gear state, capture lifecycle, telemetry and transport structures.

Executable code is evidence of client behavior. Comments/backend notes are hypotheses until corroborated.

### D. Browser/HAR — fallback gap lane

Browser Observatory and HAR tooling are retained as reusable forensic/discovery tools, but are no longer the default way to learn Ascension Logs contracts. Use them only when official documentation, pinned source and persisted evidence do not answer the exact unresolved question.

Do not add stealth, fingerprint spoofing, challenge bypass or other anti-automation evasion.

## Official API access boundary

Local credential default:

```text
data/private/coa-logs-api-key.txt
```

`data/private/**` is ignored by Git. The API key must never enter:

```text
Git
RawArchive metadata
request URL/query string
CLI value
public receipt
logs/screenshots
```

Exact request **dimension values** are not credentials but are still private source scalars. For provenance-aware `/statistics` captures they may be stored in ignored/private RawArchive observation metadata so the later analysis scope can be proven. They remain forbidden from public receipts and Git evidence.

API-derived raw payloads remain local. Public display of API-derived data must respect the published visible-attribution requirement; bulk dataset redistribution is not part of the project.

## Current statistics model evidence

The first real current-phase `/statistics` response is an object whose private dynamic keys are intentionally not published. Scalar-safe structural review observed:

```text
statistics top-level entries: 21
max observed nested depth: 5
objects carrying documented metric fields: 83
metric-bearing leaf/spec-like objects observed: 62
```

Documented static fields observed include:

```text
avg
median
max
min
total_parses
percentiles
```

Dynamic class/spec keys remain private runtime values and must be iterated, not hardcoded.

The historical real observation does not retain its requested `role` scalar even though `role` is one of its query keys and is not echoed by the response. Therefore that observation proves shape but cannot prove a complete request-scoped normalized batch. The correct response is a bounded recapture, not default-value reconstruction.

Implemented aggregate path:

```text
reviewed StatisticsResponse + private request scope
-> fail-closed exact parser
-> normalized batch/class/spec model
-> migration 0013 DuckDB persistence
-> analysis_run + raw-object dependency
-> population-prior read model
-> scalar-safe persistence/replay receipt
```

The read model may derive `local_parse_share` from `total_parses` within one batch. This is descriptive population evidence only, not the site's Tier List score and not a planner score.

## Planner trust states

Current state:

```text
population aggregate collection: allowed
population aggregate normalization: implemented, real replay pending
population aggregate persistence/read model: implemented, real replay pending
historical two-report numeric comparison: blocked
cross-report player identity: blocked
mechanic semantics: evidence-specific / not globally proven
site Tier List semantics: undocumented
planner scoring: blocked
```

A source being official does not automatically make a derived scoring formula valid.

## Privacy model

Public-safe artifacts may expose:

```text
endpoint codes
route templates
static field/key names
types and scalar-free shapes
counts and booleans
review/algorithm version names
```

Public artifacts must not expose private report/encounter/player/guild identities, query values, dynamic class/spec keys, private scope/profile values, difficulty scalar values, raw payloads, secret values or low-entropy hashes of them.

## Branch/workstream topology

```text
e3/real-log-capture
  canonical stable evidence/product baseline

e4/interactive-har-discovery
  current isolated discovery/source-contract branch
  Draft PR #9 -> e3/real-log-capture
```

Despite its historical branch name, E4 is **official-API + upstream-source-first**. Browser/HAR work is only one fallback component.

## Current next sequence

```text
statistics normalization/persistence implementation complete
-> one bounded provenance-aware /statistics recapture
-> exact normalization on real archived payload
-> persist the same capture twice and prove idempotence
-> review/promote scalar-safe real persistence receipt
-> review Source & Analysis Health for aggregate artifact
-> only then evaluate how population priors contribute to planner reasoning
```

In parallel, undocumented player/build surfaces can continue through pinned Companion source and narrow first-party/source discovery. No new difficulty-v4 heuristic, HAR or Playwright session is required for the statistics gate.
