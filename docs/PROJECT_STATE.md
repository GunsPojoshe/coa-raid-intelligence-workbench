# Project state

Updated: **2026-08-28**.

## Product

CoA Raid Leader Companion: localhost-first raid composition, evidence and analytics system backed by DuckDB.

Canonical integrated branch is `main`; project state is described by code/config/migrations/evidence, not by a stacked feature-branch chain.

## Proven capabilities

```text
local raid-plan persistence/UI: implemented
official API contract inventory: reviewed
stats:read phase/boss catalog: proven
bounded statistics capture: proven
real statistics normalization: proven
real DuckDB persistence/idempotence: proven
population-prior read model: proven
aggregate Source Observatory/Health integration: proven real
profile-scoped aggregate invalidation: proven real
bounded multi-profile population coverage v1: proven 4/4
bounded encounter context v1: proven 4/4
matched encounter/location comparator v1: proven 4/4
report encounter source correlation: proven
encounter/population provenance binding: proven
persisted report-scoped player identity: proven 2/2
persisted observed build provenance: proven 2/2
```

Canonical scalar-safe receipts are indexed in `docs/DOCUMENTATION_INDEX.md` and `evidence/real-data/README.md`.

## Official API capability model

Documented public API v1.0.0:

```text
stats:read
  /phases
  /bosses
  /statistics

events:read (experimental / on-request)
  /reports
  /reports/{reportId}
  /reports/{reportId}/encounters/{encounterId}/actors
  /reports/{reportId}/encounters/{encounterId}/events
```

`events:read` is not a self-service assumption. The product must capability-check it at runtime and remain useful with `stats:read` only.

## Current analytical gaps

```text
official public build/talent/gear surface: not documented
official public guild-progression surface: not documented
cross-report player identity: unproven
current/latest build freshness semantics: unproven
player capability semantics: unproven
encounter mechanic requirements: incomplete/unproven
site tier-list algorithm: undocumented
planner scoring: blocked
```

Event-level combat analytics is a future independent BI lane when the documented capability is available; it is not required for the existing aggregate/statistics lane.

## Retained first-party report evidence

Historical report-specific acquisition/persistence remains valuable because it already proved generic parsing/persistence and report-scoped build observations. It is now a retained gap/fallback lane rather than the primary integration strategy.

Browser Observatory/HAR remains reusable fallback tooling only for an exact undocumented gap. No stealth/challenge bypass/anti-bot evasion is part of the project.

## Pinned upstream evidence

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Executable client code can establish emitted structures/client behavior; it does not automatically prove backend or gameplay semantics.

## Storage / migrations

Forward-only migration sequence is `0001` through `0013`. Do not rewrite published migrations.

## Product direction

```text
maintain official aggregate API pipeline
-> expand independent BI only for concrete product questions
-> add official event-level ingestion when the documented capability is available and useful
-> close build/gear identity/freshness gaps with strongest available evidence
-> model encounter requirements/mechanics with explicit corroboration
-> enable explainable attendance-aware planner scoring only after trust gates close
```
