# Фактическое состояние проекта

Дата актуализации: **2026-08-26**.

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

During the documentation-integrity audit, live checks showed:

```text
PR #9 E4 -> E3: mergeable
PR #7 E3 -> E2: mergeable
PR #3 E2 -> main: integration conflict debt
```

The screenshot-reported conflict therefore belongs to the lower staged integration chain, not to the active E4→E3 workstream. Do not merge Draft PRs merely to clear UI warnings.

Always re-check live state; stored SHAs/run numbers are checkpoints only.

## Product state

CoA-only localhost-first evidence-first raid intelligence.

Primary question:

> **Почему конкретный человек нужен именно текущему составу?**

Planner scoring remains blocked until its required semantics are independently proven.

## Current paradigm

```text
official documented public API
-> official documented site semantics
-> pinned executable Companion source
-> persisted first-party report/API evidence
-> narrow browser/network fallback
-> structural inference last
```

This supersedes the old Browser-first/difficulty-first operating priority.

## Official API — real proven

Contract:

```text
OpenAPI 3.1.0
API version 1.0.0
stats:read: /phases, /bosses, /statistics
```

Real public-safe evidence:

```text
phase records: 3
active/current candidate: 1
boss records: 285
unique stable boss_id values: 285
/statistics capture: HTTP 200, archived
statistics top-level entries: 21
statistics max depth: 5
objects with documented metric fields: 83
statistics normalization ready: true
```

Canonical receipts:

```text
evidence/real-data/coa-public-api-catalog-real.json
evidence/real-data/coa-public-api-statistics-capture-real.json
evidence/real-data/coa-public-api-statistics-shape-real.json
```

Current next gate:

```text
exact StatisticsResponse parser
-> normalized aggregate model
-> DuckDB persistence
-> replay/idempotence proof
-> population-prior read model by documented dimensions
```

No new HAR/Playwright/difficulty heuristic is required for this gate.

## Official API credential boundary

Default local key file:

```text
data/private/coa-logs-api-key.txt
```

The key is local/private only and must never be copied into Git, query strings, CLI values, RawArchive metadata, public receipts, logs or screenshots.

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

First-report generic persistence:

```text
derived observations: 2031
replay matched all 2031
analytics observations: 19660
replay matched all 19660
```

Second independent report:

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

Still:

```text
status: insufficient_evidence
verified difficulty reports: 0
numeric historical cross-report scoring: blocked
```

This is an evidence gap, not proof of different difficulties. No v4 heuristic is planned simply to force equivalence.

The aggregate public `/statistics` lane is independent and may progress because it has explicit documented dimensions.

## Upstream executable source

Pinned evidence provider:

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Use for client-state/capture/build/gear/telemetry evidence. Backend comments remain hypotheses until corroborated.

## Browser Observatory / HAR

Retained as fallback for undocumented gaps only. It is not the current default Ascension Logs path.

Do not add stealth/fingerprint/challenge-bypass behavior.

## Local workspace integrity

Tracked Git tree has been audited against the new paradigm. Exact ignored/untracked workstation state cannot be remotely enumerated.

New read-only inventory:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

Private exact manifest:

```text
data/private/local-workspace-inventory.json
```

Until that manifest is reviewed, project integrity is:

```text
tracked repository audit: complete
local-only exact file audit: pending operator manifest
```

Unknown/untracked files must not be deleted.

## Current boundary

```text
official API contract: reviewed
real phase/boss catalog: proven
real current statistics capture: proven
real statistics structural review: proven
statistics normalization: next gate
statistics persistence/idempotence: not yet proven
report pipeline generalization: proven on two reports
report analytics persistence: proven + idempotent
scope-aware source schema repair: proven
historical difficulty equivalence: insufficient evidence
cross-report identity: unproven
fight-duration comparison semantics: unproven
site Tier List algorithm: undocumented
planner scoring: blocked
```
