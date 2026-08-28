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

## Machine-correlated encounter population binding — proven

Real binding checkpoint:

```text
binding_version: report-encounter-population-binding-v1
report_catalog_source_kind: archived_first_party_encounter_catalog
archived_report_catalog_reused: true
report_catalog_observation_count: 1
existing_public_api_persistence_reused: true
network_request_count: 0
source_correlation_complete: true
exact_reference_identity_verified: true
report_encounter_boss_source_correlated: true
report_encounter_difficulty_source_correlated: true
encounter_context_complete: true
encounter_context_slice_count: 4
location_comparator_complete: true
location_comparator_slice_count: 4
differential_built: true
matched_record_count: 148
encounter_only_record_count: 0
location_only_record_count: 2
exact_dimension_match_verified: true
temporal_scope_match_verified: true
same_private_scope_inputs_reused: true
machine_correlated_encounter_population_binding_complete: true
player_identity_verified: false
mechanic_semantics_verified: false
site_tier_list_algorithm_verified: false
planner_scoring_allowed: false
public_release_safe: true
```

The binding command used zero network requests. It reused the archived first-party report encounter catalog and existing official `/statistics` persistence. No Browser/HAR, `events:read` or historical difficulty heuristic was involved.

## Current exact gate — player/current-build identity

Encounter scope provenance is closed. The next independent gate is to establish deterministic player identity and build freshness/provenance before capability reasoning.

Requirements:

```text
start from already persisted current-report roster/actor evidence when available
keep current-report identity separate from cross-report identity
name equality alone never proves cross-report identity
cross-report identity requires explicit corroboration or remains false
build/talent/gear observations need a reviewed source and freshness marker
missing/stale build evidence fails closed
population aggregates do not establish individual capability
mechanic semantics remain a separate later gate
planner scoring remains blocked
```

Prefer persisted first-party report evidence and pinned executable Companion source before Browser/HAR. Do not request API keys/new scopes merely to repeat existing local facts.

Public review must remain scalar-safe and exclude player/report/encounter IDs, names, private build values, raw IDs/paths and fingerprints.

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
private build values
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
