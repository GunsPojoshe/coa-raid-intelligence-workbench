# Фактическое состояние проекта

Дата актуализации: **2026-08-27**.

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

## Official API — real-proven aggregate vertical slice

Reviewed contract:

```text
OpenAPI 3.1.0
API version 1.0.0
stats:read: /phases, /bosses, /statistics
```

Real scalar-safe evidence:

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

Real persistence proof:

```text
first pass:
  batch inserted: true
  class rows inserted: 21
  spec rows inserted: 62

second pass:
  batch matched: true
  class rows inserted: 0
  class rows matched: 21
  spec rows inserted: 0
  spec rows matched: 62
  idempotent: true
```

Also proven by the real receipt:

```text
request context complete: true
analysis_run registered: true
raw source dependency registered: true
documented dimensions persisted: true
population-prior read model available: true
site Tier List algorithm verified: false
planner scoring allowed: false
```

Canonical real receipts:

```text
evidence/real-data/coa-public-api-catalog-real.json
evidence/real-data/coa-public-api-statistics-capture-real.json
evidence/real-data/coa-public-api-statistics-shape-real.json
evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
evidence/real-data/coa-public-api-statistics-persistence-real.json
```

The last two are the real provenance-aware capture and real persistence/idempotence proof. They contain no query values, class/spec names, private dimensions, raw IDs/fingerprints or API credentials.

## Aggregate implementation

Implemented:

```text
src/coa_workbench/normalizer/public_api_statistics.py
src/coa_workbench/collector/public_api_archive.py
src/coa_workbench/collector/public_api_source_health.py
src/coa_workbench/storage/public_api_statistics.py
src/coa_workbench/analytics/public_api_population_priors.py
migrations/0013_public_api_statistics.sql
scripts/persist_public_api_statistics.py
```

Capabilities:

```text
fail-closed exact StatisticsResponse parser
private request-scope provenance
normalized batch/class/spec persistence
deterministic insert-or-match replay
analysis_run provenance
raw_object artifact dependency
source_endpoint=public_api_statistics artifact dependency
population-prior read model
Source Observatory replay from existing RawArchive
scalar-safe aggregate Source & Analysis Health receipt
```

The `source_endpoint` dependency is important: future compatible changes observed on `/statistics` can target the aggregate artifact for scoped reanalysis. Request-shaping dimensions are schema-profile keys so unrelated API scopes do not share one schema baseline.

### Current real gate

The aggregate data itself no longer needs recapture. Remaining proof is local replay of the **already archived** successful response through the new Source Observatory integration:

```text
existing RawArchive statistics response
-> reviewed request reconstruction from private provenance
-> source capture/schema/acquisition observation
-> endpoint dependency registration
-> existing normalized batch matched idempotently
-> scalar-safe Source & Analysis Health receipt
```

No network request is required for this gate.

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
aggregate Source Observatory/Health integration: implemented/tested; real local replay pending
report pipeline generalization: proven on two reports
report analytics persistence: proven + idempotent
historical difficulty equivalence: insufficient evidence
cross-report identity: unproven
fight-duration comparison semantics: unproven
site Tier List algorithm: undocumented
historical helper lexical refactor: incomplete private WIP, not integrated
planner scoring: blocked
```
