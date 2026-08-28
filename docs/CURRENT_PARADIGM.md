# Current paradigm — CoA Raid Leader Companion

Status: **canonical operating model**  
Updated: **2026-08-28**

## Product model

The workbench is an independent local BI/decision-support system for a CoA raid leader. Ascension Logs, Companion and other first-party observations supply evidence; they do not define our analytical model or UI.

Primary product question:

> **Почему конкретный человек нужен именно текущему составу?**

The answer must be explainable from composition state, encounter evidence, player/build provenance and relevant population context. It must not collapse into a static DPS ranking.

## Architecture

```text
external evidence
-> reviewed source contract
-> immutable local capture
-> deterministic normalization
-> DuckDB facts/read models
-> independent analytics
-> source/dependency health
-> trust-gated raid-leader recommendations
```

## Source priority

```text
1. official documented CoA Ascension Logs public API
2. official documented semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API observations
5. narrow browser/network observation for exact undocumented gaps
6. structural inference last
```

Browser/HAR is fallback tooling, not the acquisition strategy.

## Official API lanes

Self-service `stats:read` is the current proven aggregate source:

```text
GET /phases
GET /bosses
GET /statistics
```

The public contract also documents experimental/on-request `events:read` routes for reports, actors and encounter events. That scope is useful for future independent combat BI (deaths, casts, auras, interrupts, dispels, damage/healing timelines), but it is a separate optional capability and is never assumed available.

## Proven aggregate chain

```text
phase/boss catalog: proven
bounded /statistics capture: proven
exact normalization: proven
DuckDB persistence/idempotence: proven
population-prior read model: proven
aggregate Source Observatory/Health: proven
profile-scoped aggregate invalidation: proven
bounded multi-profile population coverage: proven 4/4
bounded encounter context: proven 4/4
matched encounter/location comparator: proven 4/4
report encounter source correlation: proven
encounter/population provenance binding: proven
```

Population metrics are descriptive context. They are not player capability, mechanic proof, the site's tier-list algorithm or planner scoring.

## Report/build evidence

Two persisted report scopes have deterministic report-scoped player identity and observed build provenance. This remains scoped evidence:

```text
report-scoped identity/build provenance: proven 2/2
cross-report identity: unproven
current/latest build freshness: unproven
player capability semantics: unproven
```

The official public API v1.0.0 does not document builds/talents/gear endpoints. Those gaps may use pinned executable Companion evidence or narrowly scoped retained first-party observations.

## Trust boundary

Never promote automatically:

```text
field/UI label -> mechanic semantics
character name -> cross-report identity
one report -> universal mechanic
one combat result -> stable capability
population aggregate -> composition recommendation
```

Planner scoring remains blocked until mechanic/requirement semantics and player/composition evidence are independently corroborated.

## Source observability

Maintained source pipeline:

```text
reviewed contract
-> RawArchive
-> acquisition observation
-> schema/profile/scope observation
-> dependency registration
-> source-change detection
-> scoped reanalysis
-> Source & Analysis Health
```

For `/statistics`, source shape is compared only inside compatible private request profiles.

## Privacy

Raw payloads, API keys, cookies, DuckDB, private query values, report/encounter/player identifiers, build values and private fingerprints remain local. Public receipts contain only reviewed scalar-safe fields such as static endpoint/field names, counts, booleans and algorithm versions.
