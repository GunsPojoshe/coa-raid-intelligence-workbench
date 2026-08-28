# Фактическое состояние проекта

Дата актуализации: **2026-08-28**.

Canonical restart order:

```text
AGENTS.md
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
docs/CONTINUATION_PROMPT.md
```

## GitHub / workstreams

```text
main
└── e2/log-evidence-refactor        Draft PR #3 -> main
    └── e3/real-log-capture         Draft PR #7 -> e2
        └── e4/interactive-har-discovery  Draft PR #9 -> e3
```

The lower staged integration debt is separate from active E4 work. Always re-check live branch/PR/CI state; stored SHAs are checkpoints only.

## Product state

CoA-only localhost-first evidence-first raid intelligence.

Primary question:

> **Почему конкретный человек нужен именно текущему составу?**

Planner scoring remains blocked until its required identity, mechanic, encounter and composition semantics are separately proven.

## Current paradigm

```text
official documented public API
-> official documented site semantics
-> pinned executable Companion source
-> persisted first-party report/API evidence
-> narrow browser/network fallback
-> structural inference last
```

## Official API — real-proven aggregate vertical slice and bounded coverage

Reviewed contract:

```text
OpenAPI 3.1.0
API version 1.0.0
stats:read: /phases, /bosses, /statistics
```

Real scalar-safe catalog and single-slice evidence:

```text
phase records: 3
active/current candidate: 1
boss records: 285
unique stable boss_id values: 285
provenance-aware /statistics: HTTP 200, archived
response bytes: 21306
statistics top-level entries: 21
normalized class summaries: 21
normalized spec records: 62
normalized percentile scalar values: 806
population-prior records: 62
records with local_parse_share: 62
```

Real bounded population coverage v1:

```text
required slices: 4
covered before run: 1
missing before run: 3
network requests: 3
successful new captures: 3
new persisted profiles: 3
deterministic second replays: 3
covered after run: 4
missing after run: 0
coverage complete: true
aggregate class summaries: 60
aggregate spec records: 162
aggregate percentile scalar values: 2106
metric families represented: 3
role-qualified required slices: 3
role-omitted required slices: 1
bulk dataset mode: false
events:read used: false
```

Real Source Observatory / profile-reanalysis state after coverage:

```text
source observatory integrated: true
source_endpoint_profile dependency count: 4
legacy unscoped source_endpoint dependency count: 0
eligible source events examined: 3
created reanalysis requests: 0
pending reanalysis requests: 0
actionable open source changes: 0
source health attention required: false
planner scoring allowed: false
site Tier List algorithm verified: false
```

The observed profile/source events from the new acquisitions are provenance, not actionable source-health failures.

Canonical real receipts:

```text
evidence/real-data/coa-public-api-catalog-real.json
evidence/real-data/coa-public-api-statistics-capture-real.json
evidence/real-data/coa-public-api-statistics-shape-real.json
evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
evidence/real-data/coa-public-api-statistics-persistence-real.json
evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json
evidence/real-data/coa-public-api-population-coverage-real.json
```

All receipts remain scalar-safe: no query values, class/spec names, private dimensions, raw IDs/paths/fingerprints, metric scalar values or API credentials.

## Aggregate implementation

Implemented:

```text
src/coa_workbench/normalizer/public_api_statistics.py
src/coa_workbench/collector/public_api_archive.py
src/coa_workbench/collector/public_api_source_health.py
src/coa_workbench/collector/source_profile_reanalysis.py
src/coa_workbench/storage/public_api_statistics.py
src/coa_workbench/analytics/public_api_population_priors.py
src/coa_workbench/analytics/public_api_population_coverage.py
migrations/0013_public_api_statistics.sql
scripts/persist_public_api_statistics.py
scripts/capture_public_api_population_coverage.py
```

Capabilities:

```text
fail-closed exact StatisticsResponse parser
private request-scope provenance
normalized batch/class/spec persistence
deterministic insert-or-match replay
analysis_run provenance
raw_object artifact dependency
source_endpoint_profile artifact dependency
profile-scoped reanalysis resolver
population-prior read model
Source Observatory replay from existing RawArchive
scalar-safe aggregate Source & Analysis Health receipt
bounded missing-only population coverage workflow
```

`request_contract_changed` remains endpoint-global, while schema/profile-local changes target only matching private query profiles. Source events older than a dependency registration cannot back-trigger the new artifact.

### Current real gate

The following aggregate gates are closed on real local data:

```text
single-slice capture + exact normalization
DuckDB persistence + deterministic replay
Source Observatory integration
profile-scoped dependency migration
bounded population coverage v1
```

The next aggregate step must be **product-driven**, not cartesian completeness. Do not crawl all boss/location/week/realm/class/spec combinations.

Preferred next design gate:

```text
choose one concrete encounter/cohort need from the raid-planning workflow
-> bind it to reviewed official dimensions locally
-> capture only the minimal missing encounter-scoped aggregate slices
-> preserve the same RawArchive/provenance/profile-reanalysis/health chain
-> expose the result only as descriptive encounter population context
-> keep planner scoring blocked until player/encounter/composition semantics are separately proven
```

This should start with one explicitly selected encounter rather than all 285 bosses.

## Official API credential boundary

```text
data/private/coa-logs-api-key.txt
```

The API key is local/private and must never enter Git, RawArchive metadata, query strings, CLI values, public receipts, logs or screenshots.

Exact request dimension values are retained only in ignored/private RawArchive observation metadata because they are analytical provenance. They are never public evidence.

## Report-specific E3 runtime — retained proven state

Six current-report source families remain real-observed/reviewed:

```text
GET /api/reports/{reportId}
GET /api/reports/{reportId}/encounters?includeTrash=...
GET /api/reports/{reportId}/combatants-roster?encounterIds=...
GET /api/reports/{reportId}/encounters/{encounterId}/throughput-timeline?...
GET /api/reports/{reportId}/character_damage_taken_abilities?...
GET /api/reports/{reportId}/character_spell_healing?...
```

First report:

```text
derived observations: 2031, replay idempotent
analytics observations: 19660, replay idempotent
```

Second report:

```text
derived inserted: 2920
analytics inserted: 28213
throughput points: 16907
```

Structural benchmark:

```text
reports: 2
input profiles: 45
eligible peer cohorts: 3
eligible profiles: 6
eligible ranked rows: 133
```

Scope-aware repair:

```text
623 false/legacy events superseded
open events: 645 -> 22
new scoped schema changes on replay: 0
pending reanalysis: 0
```

## Historical difficulty/equivalence gate

```text
status: insufficient_evidence
verified difficulty reports: 0
numeric historical cross-report scoring: blocked
```

This does not block official aggregate analytics because `/statistics` has explicit documented dimensions.

## Upstream executable source

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Use executable code for client-state/capture/build/gear/telemetry evidence. Backend comments remain hypotheses until corroborated.

## Browser Observatory / HAR

Fallback for exact undocumented gaps only. No stealth/fingerprint/challenge-bypass behavior.

## Local workspace integrity

The Windows metadata inventory and the sole Git-visible untracked implementation candidate were reviewed. The historical helper patch is valuable incomplete WIP, depends on absent `coa_workbench.collector.guild_progression_js_lexical`, is preserved privately and must not be applied as-is.

Do not re-request the same inventory/patch unless material local state changes.

## Current boundary

```text
official API contract: reviewed
real phase/boss catalog: proven
real statistics capture/shape: proven
real provenance-aware statistics capture: proven
real statistics normalization: proven
real DuckDB persistence/idempotence: proven
population-prior read model: proven
aggregate Source Observatory/Health integration: proven real
profile-scoped aggregate invalidation: proven real
legacy broad aggregate dependency: inactive
bounded multi-profile population coverage v1: proven real, 4/4 complete
report pipeline generalization: proven on two reports
report analytics persistence: proven + idempotent
historical difficulty equivalence: insufficient evidence
cross-report identity: unproven
fight-duration comparison semantics: unproven
site Tier List algorithm: undocumented
historical helper lexical refactor: incomplete private WIP, not integrated
planner scoring: blocked
```
