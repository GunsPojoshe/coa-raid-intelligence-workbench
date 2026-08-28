# CoA Raid Intelligence Workbench

Localhost-first, evidence-first raid intelligence for **Ascension WoW / Conquest of Azeroth**.

Primary product question:

> **Почему конкретный человек нужен именно текущему составу?**

The project is not a DPS-ranking scraper. Important conclusions preserve provenance from source observation through reviewed transformation to analytical claim.

## Current workstream

```text
e3/real-log-capture
  stable report-evidence baseline

e4/interactive-har-discovery
  active official-API / upstream-evidence workstream
  Draft PR #9 -> e3/real-log-capture
```

The E4 branch name is historical. Browser/HAR is fallback only.

## Source priority

```text
1. official documented CoA Ascension Logs public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API responses
5. narrow browser/network observation for exact undocumented gaps
6. structural inference only after stronger sources are exhausted
```

## Encounter/population evidence — real proven through binding

Self-service `stats:read` routes:

```text
GET /phases
GET /bosses
GET /statistics
```

Closed real gates:

```text
phase/boss catalog
provenance-aware statistics capture
exact normalization
DuckDB persistence + deterministic replay
population-prior read model
Source Observatory + profile-scoped reanalysis
bounded population coverage v1: 4/4
bounded encounter context v1: 4/4
matched encounter/location comparator v1: 4/4
report encounter boss/difficulty source correlation v2: proven
machine-correlated encounter population binding v1: proven
```

Retained implementation anchors:

```text
scripts/inventory_local_workspace.py
forward-only migrations 0001-0013
scripts/persist_public_api_statistics.py
scripts/capture_public_api_population_coverage.py
second-pass replay:            idempotent
legacy broad endpoint dependency: inactive
```

Binding checkpoint:

```text
report catalog source: archived_first_party_encounter_catalog
network requests: 0
source correlation complete: true
encounter context complete: true
location comparator complete: true
differential built: true
matched records: 148
encounter-only: 0
location-only: 2
exact dimension match: true
temporal scope match: true
same private scope inputs reused: true
machine-correlated encounter population binding complete: true
player identity verified: false
mechanic semantics verified: false
planner scoring allowed: false
```

Scalar-safe evidence:

```text
evidence/real-data/coa-public-api-encounter-comparator-real.json
evidence/real-data/coa-report-encounter-source-correlation-real.json
evidence/real-data/coa-report-encounter-population-binding-real.json
```

The binding workflow reused the archived first-party report encounter catalog plus already-persisted official `/statistics` data and made zero network requests.

## Current trust boundary

Proven:

```text
report/encounter URL shape
operator-reviewed boss/location/difficulty
unique official /bosses binding
exact report + encounter identity from first-party catalog
report encounter -> boss identity
report encounter -> difficulty
encounter-scoped population context 4/4
same-location matched comparator 4/4
machine-correlated encounter -> population-context provenance binding
```

Not yet proven:

```text
cross-report player identity
current player build provenance/freshness
encounter mechanic/requirement semantics
player capability / composition fit
planner recommendation
```

Current next gate: player/current-build identity. Name equality is not cross-report identity proof, and population metrics are not individual capability evidence.

## Privacy

Keep local/private:

```text
API key
query/profile values
report/encounter IDs in public receipts
boss/location/difficulty values in public receipts
player names/IDs in public receipts unless separately approved
private build values
class/spec names
metric/parse-share scalars
raw IDs/paths
request/schema/profile fingerprints
DuckDB/raw payloads
```

## Historical report lane

E3 report persistence/analytics/generalization remains proven on two reports. Historical two-report difficulty equivalence remains `insufficient_evidence`; numeric comparison of that historical pair stays blocked.

## Pinned Companion source

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Executable source can establish client behavior. Comments/backend claims require corroboration.

## Verification

Python requirement: **3.12+**.

```powershell
uv sync --frozen --extra dev --no-build-package ruff
uv run --no-sync python scripts/verify_repo.py
```

Required exact-head CI jobs:

```text
public-release-audit
ubuntu
windows
```

## Documentation

Start with:

```text
AGENTS.md
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
docs/CONTINUATION_PROMPT.md
docs/NEXT_CHAT_HANDOFF.md
```
