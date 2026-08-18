# Parallel workstreams — 2026-08-19

This document records the intentional split into two independent continuation paths. It supplements, not replaces, `docs/PROJECT_STATE.md` and `docs/NEXT_CHAT_HANDOFF.md`.

## Shared baseline

Repository:

```text
GunsPojoshe/coa-raid-intelligence-workbench
```

Branch stack after the split:

```text
main
└── e2/log-evidence-refactor
    └── e3/real-log-capture                 canonical/current line
        └── e4/interactive-har-discovery    isolated UI -> Network experiment
```

Before doing anything in a new chat, read:

```text
docs/PROJECT_STATE.md
docs/NEXT_CHAT_HANDOFF.md
docs/PARALLEL_WORKSTREAMS_2026-08-19.md
```

Then check the live branch HEAD, PR and exact-head CI. The SHA values in handoff documents are historical checkpoints, not a substitute for live GitHub state.

## Why the split exists

The conservative E3 path has reached a precise evidence blocker:

```text
2 persisted reports
3 eligible structural peer cohorts
0 ambiguous cohorts
0 encounter-name uniqueness blockers
0 verified difficulty reports
0 cross-surface difficulty mismatches
```

`cross-report-equivalence-review-v1` returned `insufficient_evidence` because the two initially selected difficulty surfaces produced no usable difficulty scalar for the target reports. This is an evidence gap, not proof that the reports differ in difficulty.

E3 already has a read-only scalar-safe source-structure probe to inspect existing persisted evidence before asking for more network capture.

At the same time, a faster discovery method was identified: one continuous HAR captured while the operator deliberately changes UI state one factor at a time. That method can reveal UI -> request/response causality much faster than repeated static reload captures. Because it is experimental and can generate new candidate contracts, it is isolated in E4.

## Track A — canonical E3 continuation

Branch:

```text
e3/real-log-capture
```

PR:

```text
#7 -> e2/log-evidence-refactor
```

Purpose: continue the evidence-first product line without incorporating unverified conclusions from E4.

Immediate next action uses only the existing local DuckDB/raw archive:

```text
cross-report-source-structure-v1
-> inspect report-detail fixed fields/types
-> inspect encounter-row fixed fields/types
-> inspect public-report fixed fields/types
-> remember that earlier private structural evidence also observed encounter-catalog top-level reportDifficulty
```

Relevant code already exists:

```text
src/coa_workbench/analytics/cross_report_source_structure.py
scripts/review_cross_report_source_structure.py
tests/unit/test_cross_report_source_structure.py
```

The real structure result is still pending at this split point. No new HAR is required for Track A.

Decision rule after that result:

```text
existing independent difficulty evidence exists
-> prove stable scalar binding + corroboration
-> revise equivalence gate

existing evidence still insufficient
-> record exact missing source boundary
-> keep numeric scoring blocked
-> optionally consume only confirmed discoveries from E4 later
```

After real difficulty + encounter equivalence:

```text
fight-duration / comparison-unit semantics
-> guarded numeric cross-report benchmark
-> explicit cross-report character identity from stable source evidence
-> character history / rankings / statistics
-> Armory/talent-grid
-> BisBeard
-> planner scoring only from corroborated mechanics
```

Do not use character name as cross-report identity. Do not normalize totals by duration until units/linkage are proven.

## Track B — isolated E4 interaction-HAR experiment

Branch:

```text
e4/interactive-har-discovery
```

Base: E3 at the split point. E4 may move independently after that.

Purpose: accelerate source discovery by treating a HAR as an ordered interaction trace rather than a single page-load snapshot.

Core model:

```text
UI state A
-> one deliberate UI action
-> request burst OR no request
-> path/query/body delta
-> response structure/content delta
-> UI state B
```

The experiment must keep these concepts separate:

```text
report difficulty
boss / encounter selection
Summary or other analytical subpage/tab
client-side-only UI state
```

### Recommended interaction capture

Browser choice is not semantically important. Firefox/Mozilla is acceptable.

1. Open the target report.
2. DevTools -> Network.
3. Enable `Preserve log`.
4. Clear Network.
5. Reload the report and wait for the baseline to settle.
6. Change only one UI factor at a time, leaving roughly 2-3 seconds between actions.

Recommended sequence:

```text
baseline reload
-> difficulty A
-> boss 1
-> Summary
-> boss 2
-> Summary
-> boss 3
-> Summary
-> neighbouring subpage/tab
-> back to Summary
-> difficulty B
-> boss 1
-> Summary
-> boss 2
-> Summary
```

If the actual UI differs, preserve the principle: one changed factor at a time.

At the end use `Save all as HAR with content`.

Also provide the ordered action list and a small set of representative screenshots:

```text
overall report screen
difficulty control opened
boss selector/list
Summary
one neighbouring subpage
optionally a state after difficulty switch
```

Do not make a screenshot after every click. The action order plus HAR timestamps is sufficient for correlation.

### What E4 should implement/analyze

Build an ordered differential review, preferably as reusable project Python rather than a one-off PowerShell parser:

```text
HAR entries ordered by startedDateTime
-> same-origin reviewed request candidates
-> canonical path/query/body shapes
-> action-window request bursts
-> response structural fingerprints
-> adjacent-state deltas
-> repeated transition correlation
```

Questions to answer independently:

1. Where is difficulty actually represented or applied?
2. Does difficulty switching create network traffic or only client-side filtering/state changes?
3. Which request/path/query/body value is tied to boss selection?
4. Which calls are tied to Summary versus neighbouring tabs/subpages?
5. Which parameters shape the response rather than merely identify a request?
6. Which UI transitions are network-silent?

A network-silent transition is a valid result; do not invent an endpoint for it.

### Evidence promotion rules

Do not promote a candidate because a field or control is named `difficulty`, `boss` or `summary`.

Minimum desirable corroboration for a candidate UI/network contract:

```text
same control changed at least twice
+ repeatable request/response delta
+ neighbouring control does not produce the same delta
+ observation holds across at least two boss states or two difficulty states
```

Any newly discovered endpoint/profile/parameter must pass the existing reviewed-contract and privacy boundaries before it can be merged into E3.

### E4 deliverables

Expected branch outputs:

```text
reusable interaction-HAR parser/reviewer
ordered transition model
scalar-safe public review/receipt
verified source-contract/profile changes only where evidence supports them
focused tests for deterministic differential classification
branch documentation of merge candidates and unresolved hypotheses
```

The raw interaction HAR remains private. Git/public evidence must not include raw bodies, IDs, names, query values, private scope/profile values or hashes.

## Merge policy: E4 -> E3

E4 is a discovery branch, not a second source of truth.

Safe to merge back when proven:

```text
reviewed endpoint/parameter/profile contracts
deterministic parser/reviewer code
scalar-safe evidence receipts
focused tests
documentation
```

Do not merge:

```text
raw HAR/private screenshots
private identifiers or query values
UI-label-based semantic guesses
one-off report assumptions
unverified gameplay mechanics
```

If E4 disproves an E3 assumption, record the new observation and its provenance explicitly; do not silently rewrite history.

## Starting a new chat on Track A

Suggested first message:

```text
Продолжаем каноническую ветку e3/real-log-capture. Сначала прочитай docs/PROJECT_STATE.md, docs/NEXT_CHAT_HANDOFF.md и docs/PARALLEL_WORKSTREAMS_2026-08-19.md, проверь live GitHub HEAD/PR/CI и продолжи Track A. Ветка e4 развивается отдельно; не смешивай неподтверждённые результаты.
```

The agent should stay on E3 and obtain/analyze the real source-structure result first.

## Starting a new chat on Track B

Suggested first message:

```text
Начинаем e4/interactive-har-discovery. Сначала прочитай docs/PROJECT_STATE.md, docs/NEXT_CHAT_HANDOFF.md, docs/PARALLEL_WORKSTREAMS_2026-08-19.md и branch-specific INTERACTIVE_HAR_DISCOVERY.md, проверь live GitHub state. Дальше строим controlled interaction HAR: difficulty -> bosses -> Summary/subpages -> second difficulty, и анализируем UI -> Network differential evidence.
```

The agent should stay on E4, prepare the reusable differential-analysis path, inspect the new private HAR when supplied, and submit only corroborated merge candidates back toward E3.

## Shared engineering/safety constraints

Development rhythm:

```text
focused tests
-> coherent change
-> one verify_repo
-> one push
-> exact-head CI
```

Other invariants:

- private/raw inputs are valid for analysis; publication is the privacy boundary;
- do not publish low-entropy hashes of private scalar values;
- do not rewrite published migrations;
- do not delete unknown/untracked local files;
- reportId is a data scope, not an API schema version;
- high-cardinality IDs are not global source-change dimensions;
- unknown writes/destructive routes require an explicit gate;
- do not bypass anti-bot/challenges;
- browser Network evidence overrides stale historical assumptions;
- planner scoring remains fail-closed.
