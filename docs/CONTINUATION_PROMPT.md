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

Maintain fail-closed semantics: observation, field, UI label, name equality or population metric is not automatic identity/mechanic/planner proof.

## Source priority

```text
official documented public API
-> official documented site semantics
-> pinned executable Companion source
-> persisted first-party report/API evidence
-> narrow browser/network fallback
-> structural inference last
```

## Closed real encounter/population chain

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
machine-correlated encounter population binding v1: proven
```

Canonical scalar-safe receipts:

```text
evidence/real-data/coa-public-api-encounter-comparator-real.json
evidence/real-data/coa-report-encounter-source-correlation-real.json
evidence/real-data/coa-report-encounter-population-binding-real.json
```

Do not repeat population coverage, encounter-context, comparator, report-correlation or binding proof merely because a session restarted.

## Persisted roster/build provenance — proven real

Receipt:

```text
evidence/real-data/coa-current-roster-build-provenance-real.json
```

Real checkpoint:

```text
catalog_version: current-roster-build-provenance-catalog-v1
persisted_report_count: 2
reviewed_report_scope_count: 2
report_scope_with_roster_count: 2
report_scoped_player_identity_complete_count: 2
observed_build_linkage_complete_count: 2
source_provenance_complete_count: 2
observed_build_provenance_complete_count: 2
character_count: 52
snapshot_count: 70
talent_entry_count: 3558
gear_slot_observation_count: 1195
observed_timestamp_coverage_complete_count: 0
selected_reference_present: false
selected_reference_report_scoped_player_identity_complete: false
selected_reference_observed_build_provenance_complete: false
selected_reference_same_report_build_binding_proven: false
current_build_freshness_verified: false
latest_snapshot_semantics_verified: false
cross_report_identity_verified: false
mechanic_semantics_verified: false
planner_scoring_allowed: false
public_release_safe: true
```

This closes **report-scoped identity + observed build provenance for all persisted report scopes only**. It does not close selected-report linkage, cross-report identity or freshness.

The operator run used existing current-report persistence only, with `network_request_count = 0`, no Browser/HAR and no `events:read`.

## Current exact gate — selected encounter report -> roster/build same-report binding

The selected encounter report is absent from persisted roster/build report scopes. Do not silently substitute one of the two proven persisted reports.

Next sequence:

```text
1. inspect existing local persisted/raw first-party evidence for the selected report
2. if roster/build evidence is already archived, normalize/persist it deterministically
3. otherwise inspect official documented site semantics and pinned executable Companion source for the narrow acquisition contract
4. acquire only the missing selected-report evidence if required
5. Browser/HAR only for an exact undocumented gap
6. prove selected encounter report -> roster/build same-report binding
7. only then establish current/latest build freshness semantics
```

Freshness remains separately blocked because `observed_timestamp_coverage_complete_count = 0`. Never infer latest/current from row order or name equality.

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
