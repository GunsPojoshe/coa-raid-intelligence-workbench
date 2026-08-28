# Continuation prompt — current project state

Updated: **2026-08-28**.

## Repository

```text
GunsPojoshe/coa-raid-intelligence-workbench
local: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
canonical workstream: e4/interactive-har-discovery
Draft PR #9 -> e3/real-log-capture
```

Perform live GitHub branch HEAD, PR #9 mergeability and exact-head CI checks first. Stored SHAs/run numbers are checkpoints only.

## Read in order

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

## Product question

> **Почему конкретный человек нужен именно текущему составу?**

Maintain fail-closed semantics: observation, field, UI label or population metric is not automatic mechanic/planner proof.

## Source priority

```text
official documented public API
-> official documented site semantics
-> pinned executable Companion source
-> persisted first-party report/API evidence
-> narrow browser/network fallback
-> structural inference last
```

## Closed real aggregate gates

```text
/phases + /bosses catalog
exact /statistics normalization
DuckDB persistence + idempotence
population-prior read model
Source Observatory integration
source_endpoint_profile dependencies
profile-scoped reanalysis
bounded population coverage v1: 4/4
bounded encounter context v1: 4/4
matched encounter/location comparator v1: 4/4
```

Comparator real result:

```text
encounter context: 59 class summaries / 148 specs / 1924 percentile values
location comparator: 59 class summaries / 150 specs / 1950 percentile values
matched records: 148
encounter-only records: 0
location-only records: 2
avg/median/parse-share delta+ratio records: 148 each
exact dimension match verified: true
temporal day_number match verified: true
missing spec treated as zero: false
source_endpoint_profile dependency count: 12
pending reanalysis: 0
actionable source changes: 0
source health attention_required: false
planner scoring allowed: false
```

Canonical scalar-safe comparator receipt:

```text
evidence/real-data/coa-public-api-encounter-comparator-real.json
```

Do not repeat generic population coverage, encounter-context proof or comparator capture merely because a session restarted.

## Comparator semantics

```text
same phase
+ same concrete difficulty
+ same location
+ same metric
+ same role
+ same bracket
+ same damage mode
+ same capture day_number
+ bossId omitted only
```

Missing specs are not zero. A zero denominator yields no ratio. Metric/share scalars remain private. The differential is descriptive only.

## Encounter binding boundary

Proven:

```text
report/encounter URL shape
operator-reviewed boss/location/difficulty
unique official /bosses binding
encounter-scoped population context
matched same-location comparator
```

Not independently proven:

```text
report encounter -> selected boss identity
report encounter -> selected difficulty
```

Do not claim machine-verified encounter identity yet.

## Current exact gate — independent report correlation

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

The previous operator implementation used the heavier `/api/reports/{reportId}/encounters/{encounterId}` payload. The first real run timed out during body reading after two 30-second attempts. Treat that as transport evidence only. Do not retry the heavy route merely by increasing timeout.

The compact encounter catalog is already real-observed in the E3 current-report runtime. Scalar-free structural evidence shows fields including:

```text
id
name
boss_id
difficulty
is_boss_encounter
zone
```

Requirements:

```text
use the already selected local report/encounter
prefer persisted first-party catalog evidence
require exact report identity
require exactly one selected encounter row
boss correlation and difficulty correlation are separate booleans
conflicting persisted observations fail closed
network never overrides persisted conflicts
publish counts/booleans/version markers only
no API key/raw archive/DuckDB/private values requested from operator
no events:read
no Browser/HAR
no historical difficulty-v4 heuristic
planner remains blocked
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

Do not request RawArchive, DuckDB, private source values or additional report/encounter IDs from the operator.

## Historical report evidence

E3 report persistence/analytics/generalization remains proven on two reports. Historical two-report difficulty equivalence remains `insufficient_evidence`; numeric comparison of that pair stays blocked.

## Upstream source

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Use executable code for client behavior; comments/backend claims remain hypotheses.

## Browser/HAR

Fallback only for an exact undocumented gap. No anti-bot evasion.

## Local workspace

The historical helper patch is private incomplete WIP because `guild_progression_js_lexical` is absent. Preserve it and do not apply it as-is.

## Privacy boundary

Keep local/private:

```text
API key
query/profile values
report/encounter IDs in public receipts
boss/location/difficulty values in public receipts
class/spec names
metric/parse-share scalars
raw IDs/paths
request/schema/profile fingerprints
DuckDB/raw payloads
```

## Verification

```powershell
uv sync --frozen --extra dev --no-build-package ruff
uv run --no-sync python scripts/verify_repo.py
```

Then verify exact pushed HEAD CI:

```text
public-release-audit
ubuntu
windows
```
