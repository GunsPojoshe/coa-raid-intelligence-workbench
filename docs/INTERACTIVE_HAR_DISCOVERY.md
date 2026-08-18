# Interactive HAR discovery — E4

Дата фиксации: **2026-08-19**.

Branch:

```text
e4/interactive-har-discovery
```

This is an isolated discovery branch based on the canonical E3 evidence line. It exists to accelerate UI -> Network source discovery without weakening E3 trust rules.

Before continuing E4, read:

```text
docs/PROJECT_STATE.md
docs/NEXT_CHAT_HANDOFF.md
docs/PARALLEL_WORKSTREAMS_2026-08-19.md
docs/INTERACTIVE_HAR_DISCOVERY.md
```

Then verify the live E4 HEAD and exact-head CI. Do not assume the SHA in any handoff document is still current.

## Shared baseline inherited from E3

Already proven and not to be rediscovered in E4:

```text
current report runtime: 6 reviewed dynamic source families
first report derived persistence: 2031 real observations, idempotent
first report analytics: 19660 real observations, idempotent
second independent report: generic pipeline proven
structural cross-report benchmark: 3 eligible / 0 ambiguous peer cohorts
scope-aware schema cleanup: 645 -> 22 open signals
current difficulty equivalence gate: insufficient_evidence, no mismatch proven
planner scoring: blocked/fail-closed
```

The current E3 blocker is not transport. It is difficulty evidence: the first conservative cross-surface rule found no usable scalar difficulty for the two target reports.

E3 already has `cross-report-source-structure-v1` for a read-only scalar-safe review of existing persisted evidence. E4 must not replace that canonical path; it is an independent discovery experiment whose confirmed results may later be merged back.

## Goal of E4

Treat one HAR as an **ordered interaction trace** instead of a static page-load capture.

Model:

```text
UI state A
-> one deliberate user action
-> request burst OR no request
-> path/query/body delta
-> response structure/content delta
-> UI state B
```

Primary questions:

```text
1. Where is report difficulty represented or applied?
2. Is difficulty switching network-backed or client-side-only?
3. Which request delta is tied to boss/encounter selection?
4. Which calls are tied to Summary versus neighbouring analytical tabs/subpages?
5. Which request parameters actually shape a response?
6. Which UI transitions are network-silent?
```

A network-silent transition is a valid result. Do not invent an endpoint when no request occurs.

## Concepts that must remain separate

Do not merge these concepts just because UI labels are nearby:

```text
report difficulty
boss / encounter selection
Summary or another analytical subpage/tab
client-side-only UI state
```

A candidate must be tied to repeatable network evidence, not a label.

## Recommended operator capture

Browser choice is not semantically important. Firefox/Mozilla is acceptable.

Preparation:

```text
open target report
DevTools -> Network
Preserve log = ON
clear Network
reload report
wait until baseline traffic settles
```

Then change **one factor at a time**, preferably leaving roughly 2-3 seconds between actions so request bursts remain separable.

Recommended interaction sequence:

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

If the actual UI differs, preserve the method rather than the exact labels: one independent change at a time, repeated enough to establish a pattern.

At the end:

```text
Save all as HAR with content
```

Also keep an ordered text list of the performed actions. A small number of representative screenshots is useful:

```text
overall report screen
difficulty control opened
boss selector/list
Summary state
one neighbouring subpage/tab
optionally one state after switching difficulty
```

Do not create a screenshot after every click. HAR timestamps + ordered actions are the primary correlation evidence.

## Private/public handoff

The interaction HAR and screenshots are private analysis inputs and may be inspected locally/within the chat.

Do not publish to Git:

```text
raw HAR
raw response bodies
private screenshots with IDs/names unless separately sanitized
report/encounter/player/guild IDs or names
query values
request-body private scalar values
scope/profile scalar values or hashes
private input/output fingerprints
```

Public-safe receipts may contain endpoint codes, route templates, query/body **key names**, field names, scalar-free JSON types/shapes, counts, booleans and reviewed algorithm/version names.

## Reusable analyzer to build/use

Prefer project Python, not a one-off PowerShell parser.

The differential review should derive an ordered trace such as:

```text
HAR entries sorted by startedDateTime
-> same-origin candidates
-> canonical method/path/query-key/body-key shape
-> response structural fingerprint
-> temporal request bursts
-> adjacent-state/request deltas
-> repeated-transition correlation
-> scalar-safe review
```

Useful internal/private observations can include concrete values during analysis, but the public output must remove them.

The analyzer should distinguish at least:

```text
new request family
same request shape, changed query/body value
same request identity, changed response structure
repeated request burst with same transition
network-silent action window
unclassified background/operational request
```

Known static/operational routes must not be mistaken for new dynamic contracts. The existing Source Observatory/static-route exclusion remains authoritative.

## Corroboration threshold

Do not promote a candidate because one click coincides with one request.

Minimum desirable evidence for a UI/network relationship:

```text
same control transition repeated at least twice
+ same request/response delta repeats
+ a neighbouring unrelated control does not produce that delta
+ relation holds across at least two boss states or two difficulty states when applicable
```

For a new response-shaping parameter/profile, prove that changing that parameter changes the reviewed response mode/shape or content in a stable way. High-cardinality IDs remain data scope, not global source dimensions.

## Difficulty-specific strategy

The canonical E3 structural evidence already knows field names:

```text
report detail: difficulty
encounter catalog top level: reportDifficulty
encounter rows: difficulty
public reports: highest_difficulty
```

Those names are **not semantic proof**.

E4 should use controlled UI transitions to answer:

```text
Does switching difficulty change a request?
If yes: which path/query/body key changes?
Does the same delta repeat when switching back/again?
Does encounter selection alter a different key independently?
Does the returned report/encounter structure expose a stable difficulty representation tied to the switch?
```

If difficulty switching is network-silent, record that explicitly. Then inspect whether the browser loaded all difficulties earlier and the UI only filters local state; do not invent a difficulty API.

## Boss / encounter strategy

Repeat boss selection at the same difficulty and, when possible, across two difficulties.

A valid boss-binding candidate should demonstrate:

```text
boss A -> one concrete request scope
boss B -> same contract with a changed encounter scope OR a distinct reviewed request
switch back -> corresponding repeatable delta
```

Do not treat reportId, encounterId or another high-cardinality value as a schema version/dimension.

## Summary/subpage strategy

Compare Summary with at least one neighbouring analytical tab/subpage while holding report, difficulty and boss constant.

Questions:

```text
Does tab change issue a new request family?
Does it only change metric/perspective/profile parameters?
Does it trigger no network request because data is already loaded?
```

This is the fastest way to discover analytical source families without guessing from static JS.

## E4 outputs

Expected branch deliverables after a real interaction capture:

```text
reusable interaction-HAR parser/reviewer
ordered private transition model
scalar-safe public review/receipt
focused deterministic tests
reviewed source-contract/profile changes only where evidence supports them
branch documentation of confirmed merge candidates and unresolved hypotheses
```

Do not add a production collector for an uncorroborated candidate.

## Promotion back to E3

E4 is a discovery branch, not a second source of truth.

Safe merge candidates:

```text
reviewed endpoint/parameter/profile contracts
reusable deterministic parser/reviewer code
scalar-safe evidence receipts
focused tests
documentation
```

Do not merge:

```text
raw HAR/private screenshots
private scalar values
UI-label-based semantic guesses
one-report assumptions
unverified gameplay mechanics
```

If E4 disproves an E3 assumption, record the new observation and provenance explicitly. Do not silently rewrite old evidence.

## Engineering rules inherited from E3

```text
focused tests
-> coherent change
-> one verify_repo
-> one push
-> exact-head CI
```

Other invariants:

- browser Network evidence outranks stale historical assumptions;
- private/raw files are valid analysis inputs; publication is the privacy boundary;
- do not publish low-entropy hashes of private scalar values;
- do not rewrite published migrations;
- do not delete unknown/untracked local files;
- unknown writes/destructive routes require an explicit gate;
- no anti-bot bypass;
- planner scoring remains fail-closed.

## Exact new-chat startup for E4

```text
Продолжаем экспериментальную ветку e4/interactive-har-discovery.
Сначала прочитай docs/PROJECT_STATE.md, docs/NEXT_CHAT_HANDOFF.md,
docs/PARALLEL_WORKSTREAMS_2026-08-19.md и docs/INTERACTIVE_HAR_DISCOVERY.md.
Проверь live E4 HEAD и exact-head CI.
Не смешивай неподтвержденные выводы E4 с канонической e3.
Следующая задача E4: controlled interaction HAR — difficulty -> bosses -> Summary/subpages -> second difficulty,
после чего строим повторяемую UI -> Network differential correlation и передаем в E3 только подтвержденные contracts.
```
