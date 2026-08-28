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

Scalar-safe encounter evidence:

```text
evidence/real-data/coa-public-api-encounter-comparator-real.json
evidence/real-data/coa-report-encounter-source-correlation-real.json
evidence/real-data/coa-report-encounter-population-binding-real.json
```

## Persisted roster/build evidence — real proven

All currently persisted current-report roster/build scopes pass deterministic report-scoped player identity, build linkage and source provenance:

```text
report scopes reviewed: 2/2
report-scoped player identity complete: 2/2
observed build provenance complete: 2/2
characters: 52
snapshots: 70
talent entries: 3558
gear observations: 1195
complete timestamp coverage: 0/2
selected encounter reference present: false
selected reference same-report build binding proven: false
```

Receipt:

```text
evidence/real-data/coa-current-roster-build-provenance-real.json
```

This proof used existing persistence only and made zero network requests.

## Current trust boundary

Proven:

```text
report encounter -> population-context provenance binding
persisted report-scoped player identity 2/2
persisted observed build linkage/provenance 2/2
```

Not yet proven:

```text
selected encounter report -> roster/build same-report binding
cross-report player identity
current/latest build provenance/freshness
encounter mechanic/requirement semantics
player capability / composition fit
planner recommendation
```

Current next gate: establish roster/build evidence for the **selected encounter report itself**, reusing local first-party evidence first. After same-report binding exists, establish freshness/latest-snapshot semantics. Name equality is not cross-report identity proof.

## Privacy

Keep local/private:

```text
API key
query/profile values
report/encounter IDs in public receipts
boss/location/difficulty values in public receipts
player names/IDs in public receipts unless separately approved
private build/talent/gear values
snapshot hashes
source capture ids
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
