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

Correlate the selected report encounter to boss and difficulty from an independent report-side source.

Source order:

```text
official documented report API if already accessible
-> official site semantics / persisted first-party report response
-> pinned executable Companion source
-> Browser/HAR only for the exact unresolved undocumented gap
```

Requirements:

```text
use the already selected local report/encounter
fail closed on ambiguity
boss correlation and difficulty correlation are separate booleans
publish counts/booleans/version markers only
no API key/raw archive/DuckDB/private values requested from operator
no historical difficulty-v4 heuristic
planner remains blocked
```

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
