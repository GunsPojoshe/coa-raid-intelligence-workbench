# Next chat handoff — 2026-08-26

This is a compact restart card. The authoritative detailed state is in:

```text
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
docs/CONTINUATION_PROMPT.md
```

## Resume

Repository:

```text
GunsPojoshe/coa-raid-intelligence-workbench
active branch: e4/interactive-har-discovery
Draft PR #9 -> e3/real-log-capture
```

Perform live GitHub HEAD/PR/CI checks first.

## Current paradigm

```text
official public API first
-> official semantics
-> pinned Companion executable source
-> persisted first-party report/API evidence
-> browser/HAR only for exact gaps
-> inference last
```

## Real API evidence complete

```text
/phases + /bosses archived/reviewed
3 phases
1 active/current candidate
285 bosses / 285 unique stable boss_id values
current-phase /statistics HTTP 200 archived
statistics shape reviewed
21 top-level statistics entries
83 objects carrying documented metric fields
normalization_ready = true
```

Public receipt added:

```text
evidence/real-data/coa-public-api-statistics-shape-real.json
```

## Next code gate

```text
StatisticsResponse exact parser
-> normalized population-statistics model
-> DuckDB persistence migration
-> real replay/idempotence proof
-> population prior read model
```

No HAR/Playwright/new historical difficulty heuristic is needed for this gate.

## Important blockers retained

```text
historical two-report difficulty equivalence: insufficient_evidence
numeric historical cross-report scoring: blocked
cross-report player identity: blocked
fight-duration semantics: unproven
site Tier List algorithm: undocumented
planner scoring: blocked
```

## Local audit

Tracked Git state has been audited. Exact ignored/untracked workstation files are still pending one read-only manifest:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

Do not delete unknown local files.

## Branch chain note

```text
main <- e2 (#3) <- e3 (#7) <- e4 (#9)
```

At audit time #9 and #7 are mergeable; lower PR #3 has conflict/integration debt. Do not resolve by blindly accepting an old documentation side.
