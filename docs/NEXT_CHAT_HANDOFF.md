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

## Real API evidence

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

Existing public shape receipt:

```text
evidence/real-data/coa-public-api-statistics-shape-real.json
```

## Statistics code gate — implemented

```text
exact fail-closed StatisticsResponse parser
private request-scope provenance for new captures
migration 0013_public_api_statistics
normalized aggregate persistence
analysis_run + raw_object dependency
insert-or-match replay
population-prior read model
scalar-safe persistence receipt CLI
```

Deterministic tests prove the code path, but the old real capture cannot prove its exact request scope: it records `role` as a query key while the response does not echo the role value. Do not infer it from CLI defaults.

## Next real gate

After syncing exact E4 HEAD:

```powershell
uv run --no-sync python scripts/capture_current_public_api_statistics.py
uv run --no-sync python scripts/persist_public_api_statistics.py
```

Review/share only:

```text
data/exchange/out/coa-public-api-statistics-persistence-review.json
```

Do not upload raw payloads, exact query values, API key or DuckDB. If the safe receipt proves second-pass matching, promote it to `evidence/real-data/` and mark real aggregate persistence/idempotence proven.

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

The real Windows workspace metadata manifest and its sole Git-visible untracked implementation candidate were reviewed. The candidate was a valuable but incomplete historical helper-analysis patch depending on absent `coa_workbench.collector.guild_progression_js_lexical`.

Preserve that patch privately and do not apply it as-is. Do not request the same inventory/patch again merely because a chat restarted.

## Branch chain note

```text
main <- e2 (#3) <- e3 (#7) <- e4 (#9)
```

Resolve staged integration deliberately; do not blindly accept an older documentation side.
