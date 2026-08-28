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
report encounter boss/difficulty source correlation v2: proven
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

Canonical scalar-safe receipts:

```text
evidence/real-data/coa-public-api-encounter-comparator-real.json
evidence/real-data/coa-report-encounter-source-correlation-real.json
```

Do not repeat generic population coverage, encounter-context, comparator or report-correlation capture merely because a session restarted.

## Encounter binding boundary — machine correlation proven

Proven:

```text
report/encounter URL shape
operator-reviewed boss/location/difficulty
unique official /bosses binding
encounter-scoped population context
matched same-location comparator
exact first-party report + encounter identity
report encounter -> selected boss identity
report encounter -> selected difficulty
boss encounter flag = true
```

Real source correlation:

```text
correlation version: report-encounter-source-correlation-v2
parser version: report-encounter-catalog-parser-v1
source kind: live_first_party_encounter_catalog
network request count: 1
persisted observation used: false
normalized encounter count: 1
reject count: 0
verified field contract count: 5
exact reference identity verified: true
boss source correlated: true
difficulty source correlated: true
complete: true
encounter detail used: false
events:read used: false
Browser/HAR used: false
no historical difficulty heuristic: true
planner scoring allowed: false
public release safe: true
```

The old heavy `/api/reports/{reportId}/encounters/{encounterId}` timeout remains transport evidence only and must not be retried merely by raising timeout.

## Current exact gate — correlated encounter population binding

Create a deterministic local proof that the machine-correlated encounter identity and the already-proven encounter-context/comparator evidence refer to the same locally selected scope.

Target:

```text
source-correlation complete = true
encounter-context complete = true
matched comparator complete = true
same private selected scope verified locally
private IDs/dimensions remain excluded from public output
mechanic semantics verified = false
planner scoring allowed = false
```

The output should be a scalar-safe receipt with counts/booleans/version markers only.

Do not ask the operator for API key, RawArchive, DuckDB, private query values, class/spec names, metric scalars or additional report/encounter IDs. Reuse local state and existing receipts/evidence.

After this gate:

```text
separately prove current/cross-report player identity + build evidence
separately prove encounter mechanic/requirement semantics
then build capability/composition-fit reasoning
planner scoring remains blocked until those gates close
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
