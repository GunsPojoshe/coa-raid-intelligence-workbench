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

Public receipt:

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

## Local audit — completed

The real Windows workspace metadata manifest and its sole Git-visible untracked implementation candidate were reviewed.

Checkpoint:

```text
modified tracked files: 0
missing tracked files: 0
Git-visible untracked files: 1
local-only exact file audit: complete/classified
```

The sole candidate was a historical helper-analysis patch. It is valuable but incomplete and must not be applied as-is: three modified modules import a missing shared `coa_workbench.collector.guild_progression_js_lexical` module that is absent from both the patch and tracked Git history.

Preserve the patch privately. If helper discovery becomes active again, reconstruct/review the lexical scanner as a separate task and port the useful behavior/tests deliberately. Do not restart that lane before the current official-API statistics gate merely because the patch exists.

Do not request the same local inventory/patch again on chat restart. Re-inventory only after material workspace changes or a new unknown modified/untracked implementation candidate appears.

Do not request or bulk-upload RawArchive, DuckDB, API-key, Browser Observatory profile/session state or HAR inputs for repository integrity.

Inventory schema v3 skips `.venv-capture` and `*.egg-info` tooling noise and flags raw-transport candidates under local `data/exchange/out/`. `data/exchange/out/` is local staging, not automatically publication-safe.

## Branch chain note

```text
main <- e2 (#3) <- e3 (#7) <- e4 (#9)
```

At audit time #9 and #7 were mergeable; lower PR #3 had conflict/integration debt. Do not resolve by blindly accepting an old documentation side.
