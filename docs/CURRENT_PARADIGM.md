# Current paradigm — CoA Raid Intelligence Workbench

Status: **canonical operating model**  
Updated: **2026-08-27**

If an older milestone/handoff describes a different acquisition priority or next gate, this document and `docs/PROJECT_STATE.md` take precedence.

## Product question

> **Почему конкретный человек нужен именно текущему составу?**

The answer must combine actual composition state, player/build evidence, encounter needs, population context and corroborated mechanics. It must not collapse into a raw DPS ranking.

## Evidence-first architecture

```text
strongest available source
-> reviewed source/request contract
-> immutable raw capture
-> acquisition observation
-> schema/profile/scope observation
-> deterministic normalization
-> provenance + dependency tracking
-> source change detection
-> scoped reanalysis
-> reproducible analytics
-> Source & Analysis Health
-> planner reasoning only after explicit trust gates
```

Never promote automatically:

```text
field name -> gameplay meaning
UI label -> backend contract
character name -> cross-report identity
one report -> universal mechanic
one structural match -> semantic equivalence
population metric -> planner recommendation
```

## Source priority

```text
1. official documented CoA Ascension Logs public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API responses
5. narrow browser/network observation for undocumented gaps
6. structural inference only after stronger sources are exhausted
```

This is a priority order, not a single-source architecture.

## Evidence lanes

### A. Official aggregate statistics — primary population lane

Self-service `stats:read`:

```text
GET /phases
GET /bosses
GET /statistics
```

Real evidence now proves the full first aggregate vertical slice:

```text
phase/boss catalog: proven
current-phase statistics capture: proven
private request-scope provenance: proven
exact StatisticsResponse normalization: proven
DuckDB persistence: proven
second-pass replay idempotence: proven
population-prior read model: proven
```

Real normalized checkpoint:

```text
21 class summaries
62 spec records
806 percentile scalar values
62 population-prior records
62 records with local_parse_share
```

The aggregate artifact is now being integrated with Source Observatory / Source & Analysis Health. That integration replays the already archived response; it does not require another network request.

### B. First-party report evidence — private report-specific lane

The E3 report pipeline remains valid for report-specific evidence, deterministic analytics and source observability. Historical two-report difficulty equivalence remains `insufficient_evidence`, so numeric comparison of that historical pair remains blocked.

### C. Pinned Companion source — client-state lane

`FangYuanWoW/AscensionLogsCompanion` is strong executable evidence for client-observed/build/gear/capture/telemetry structures that public API v1 does not expose.

Executable code establishes client behavior; comments/backend notes require corroboration.

### D. Browser/HAR — fallback gap lane

Browser Observatory/HAR remains a provider-neutral forensic fallback for an exact undocumented gap. It is not the default way to learn Ascension Logs contracts.

No stealth, fingerprint spoofing, challenge bypass or anti-bot evasion.

## Official API privacy/provenance boundary

Credential:

```text
data/private/coa-logs-api-key.txt
```

The API key never enters Git, RawArchive metadata, request URLs, CLI values, logs, screenshots or public receipts.

Exact request dimension values are not credentials but remain private source scalars. They may be retained in ignored RawArchive observation metadata because reproducible `/statistics` normalization requires the true request scope. Public receipts do not contain them.

## Aggregate model and Source Observatory

The official `/statistics` path is:

```text
reviewed OpenAPI contract
-> bounded authenticated capture
-> immutable RawArchive + private request scope
-> exact fail-closed parser
-> normalized batch/class/spec persistence
-> analysis_run
-> raw_object dependency
-> source_endpoint dependency
-> population-prior read model
-> Source Observatory replay
-> Source & Analysis Health
```

Request-shaping `/statistics` dimensions are private schema-profile keys. This prevents different phase/difficulty/metric/role/filter scopes from being compared as if they were one schema baseline.

The artifact declares both:

```text
raw_object dependency
  exact source payload provenance

source_endpoint = public_api_statistics dependency
  logical source-change / scoped-reanalysis provenance
```

The initial Source Observatory registration may create an informational `endpoint_added` event. A baseline informational event is not treated as an actionable source problem; warning/error changes remain actionable.

## Population-prior semantics

Documented metric fields are preserved exactly by the normalized model. The read model may derive:

```text
local_parse_share = spec total_parses / sum(spec total_parses within the same persisted batch)
```

This is descriptive participation within one explicit API scope. It is not evidence of the site's Tier List algorithm and not planner scoring.

## Planner trust states

```text
population aggregate collection: proven
population aggregate normalization: proven
population aggregate persistence/idempotence: proven
population-prior read model: proven
aggregate Source Observatory/Health: implementation current gate
historical two-report numeric comparison: blocked
cross-report player identity: blocked
mechanic semantics: evidence-specific / not globally proven
site Tier List algorithm: undocumented
planner scoring: blocked
```

Official source status does not validate a derived scoring formula by itself.

## Branch/workstream topology

```text
e3/real-log-capture
  stable report-evidence baseline

e4/interactive-har-discovery
  active official-API / upstream-source branch
  Draft PR #9 -> e3/real-log-capture
```

The E4 branch name is historical.

## Current next sequence

```text
real aggregate normalization/persistence/idempotence: complete
-> replay the existing private statistics capture into Source Observatory
-> prove scalar-safe Source & Analysis Health for the aggregate artifact
-> verify source_endpoint dependency/reanalysis wiring
-> then design bounded population-prior coverage across documented dimensions
-> combine population context with separately verified player/build/encounter evidence
```

No new HAR, Playwright, difficulty-v4 heuristic or `events:read` permission is required for the current gate.
