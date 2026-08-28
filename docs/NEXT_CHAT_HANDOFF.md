# Next chat handoff — 2026-08-28

## Resume

```text
repo: GunsPojoshe/coa-raid-intelligence-workbench
canonical branch: e4/interactive-har-discovery
Draft PR #9 -> e3/real-log-capture
```

Perform live GitHub HEAD / PR #9 / exact-head CI audit first.

## Current source priority

```text
official documented public API
-> official documented site semantics
-> pinned Companion executable source
-> persisted first-party report/API evidence
-> Browser/HAR only for exact gaps
-> structural inference last
```

## Real aggregate proof complete through comparator

```text
/phases + /bosses catalog: proven
/statistics exact normalization: proven
DuckDB persistence/idempotence: proven
Source Observatory/profile-scoped reanalysis: proven
bounded population coverage: 4/4
encounter context: 4/4
location comparator: 4/4
```

Comparator checkpoint:

```text
encounter: 59 class summaries / 148 specs / 1924 percentile values
location: 59 class summaries / 150 specs / 1950 percentile values
matched records: 148
encounter-only: 0
location-only: 2
exact dimension match: true
temporal day_number match: true
missing spec treated as zero: false
profile dependencies: 12
pending reanalysis: 0
actionable source changes: 0
attention_required: false
planner scoring: false
```

Receipt:

```text
evidence/real-data/coa-public-api-encounter-comparator-real.json
```

Do not rerun population coverage, encounter context or comparator proof just to reconfirm them.

## Binding boundary

Current aggregate proof still relies on an operator-reviewed encounter scope.

```text
report URL shape: proven
boss/location -> unique official boss record: proven
report encounter -> boss from independent report source: not proven
report encounter -> difficulty from independent report source: not proven
```

## Current gate — implementation ready, real proof pending

Implementation:

```text
src/coa_workbench/analytics/report_encounter_source_correlation.py
scripts/capture_report_encounter_source_correlation.py
```

Execution order:

```text
persisted current_encounter_observation catalog evidence
-> reviewed /api/reports/{reportId}/encounters?includeTrash=false response
-> fail closed
```

The previous operator implementation used `/api/reports/{reportId}/encounters/{encounterId}`. Its first real run timed out while reading the body after two 30-second attempts. Treat that as transport evidence only. Do not retry the heavy endpoint merely with a larger timeout.

The compact encounter catalog is already real-observed in the E3 current-report runtime. Its scalar-free structural receipt shows the selected-row field family includes `id`, `name`, `boss_id`, `difficulty`, `is_boss_encounter` and `zone`.

Trust rules:

```text
exact report identity required
exactly one selected encounter row required
boss name + is_boss_encounter checked independently
difficulty checked independently
conflicting persisted observations fail closed
network never overrides persisted conflicts
no events:read
no Browser/HAR
no historical difficulty-v4 heuristic
planner scoring blocked
```

Operator command after fast-forwarding canonical E4:

```powershell
uv run --no-sync python scripts/capture_report_encounter_source_correlation.py `
    --reference-url "https://coa.ascensionlogs.gg/reports/31135/encounters?encounters=703971" `
    --boss-name "Basalthane" `
    --difficulty ascended
```

Review only:

```text
data/exchange/out/coa-report-encounter-source-correlation-review.json
```

Do not request API key, RawArchive, DuckDB, private query values, class/spec names, metric scalars or additional report IDs from the operator.

## Retained blockers

```text
historical two-report difficulty equivalence: insufficient_evidence
cross-report player identity: unproven
site Tier List algorithm: undocumented
planner scoring: blocked
```

## Local WIP boundary

Historical helper patch remains private incomplete WIP because `guild_progression_js_lexical` is absent. Preserve it; do not apply as-is.
