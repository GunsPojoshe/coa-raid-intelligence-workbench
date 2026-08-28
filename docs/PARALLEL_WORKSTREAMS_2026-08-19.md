# Parallel workstreams — 2026-08-19

This document records the intentional E3/E4 split and the current role of each branch.

## Branch stack

```text
main
└── e2/log-evidence-refactor
    └── e3/real-log-capture                 canonical evidence/product line
        └── e4/interactive-har-discovery    isolated accelerated source discovery
```

Always verify live branch HEAD, PR and exact-head CI before acting. SHAs in handoff documents are checkpoints, not live truth.

## Shared baseline

The split started after E3 had already proven:

```text
2 persisted independent reports
6 reviewed current-report source families
first-report derived persistence + replay
combat analytics persistence + replay
second-report generic ingestion
3 eligible / 0 ambiguous structural peer cohorts
scope-aware schema repair: 645 -> 22 open signals
0 encounter-name uniqueness blockers
```

The current canonical blocker remains semantic/evidence quality, not transport:

```text
cross-report difficulty/equivalence = insufficient_evidence
numeric cross-report scoring = blocked
planner scoring = blocked
```

## Track A — canonical E3

Branch:

```text
e3/real-log-capture
```

PR:

```text
#7 -> e2/log-evidence-refactor
```

E3 owns canonical product/evidence promotion.

Its current progression remains:

```text
existing local source-structure evidence
-> defensible difficulty corroboration
-> difficulty + encounter equivalence
-> fight-duration/comparison-unit semantics
-> guarded numeric cross-report benchmark
-> explicit cross-report character identity
-> rankings/statistics/history
-> Armory/talent-grid
-> BisBeard planning evidence
-> planner scoring only from corroborated mechanics
```

E3 must not consume an E4 hypothesis merely because it was observed in a browser UI.

## Track B — E4 Browser Observatory

Branch:

```text
e4/interactive-har-discovery
```

PR:

```text
#9 -> e3/real-log-capture
```

E4 originally tested one continuous interaction HAR. That experiment has evolved into a reusable Browser Observatory.

Current E4 operating document:

```text
docs/BROWSER_OBSERVATORY.md
```

Historical/fallback HAR document:

```text
docs/INTERACTIVE_HAR_DISCOVERY.md
```

Architecture:

```text
headed dedicated browser
-> explicit operator actions
-> live same-origin fetch/xhr capture
-> private HAR + trace + action manifest
-> NetworkObservation
-> action/network windows
-> intrinsic request-burst corroboration
-> negative controls
-> scenario coverage
-> scalar-safe receipt
```

### Why this remains isolated

Browser automation can discover contracts faster, but speed does not increase semantic trust.

E4 may automate:

```text
source discovery
private capture
structural normalization
request-burst correlation
scalar-free schema comparison
scenario coverage
negative-control review
```

E4 may not automatically promote:

```text
domain identity from labels alone
gameplay mechanic semantics
planner trust
numeric performance scoring
```

### Current E4 source boundary

The first scenario manifest covers only:

```text
source_code = coa_ascension_logs
host = coa.ascensionlogs.gg
```

Armory/talent-grid/BisBeard will get separate source manifests/host boundaries while reusing the same engine.

### Current E4 gate

The implementation is ready for its first real private Browser Observatory run.

First recommended scenario:

```text
report.difficulty
```

After the run:

```text
scalar-safe receipt
-> scenario coverage
-> exact unresolved relation review
-> only corroborated deterministic knowledge may become an E3 merge candidate
```

Manual DevTools HAR export is now fallback/forensic, not the default workflow.

## Local/private boundary

GitHub is not the complete operational corpus.

Known local/private classes are documented in:

```text
docs/LOCAL_WORKSPACE_BOUNDARY.md
```

Important rules:

```text
never delete unknown/untracked local files
never git clean private project state
preserve historical patches/helpers unless explicitly reviewed
browser profile/HAR/trace/private actions never enter Git
public-safe receipts live under data/exchange/out locally
```

## Merge policy: E4 -> E3

Safe candidates after evidence review:

```text
provider-neutral observation code
deterministic reviewers
reviewed endpoint/parameter/profile contracts
focused tests
scalar-safe receipts
documentation
```

Do not merge:

```text
raw HAR/trace/browser profile
private screenshots
IDs/names/query/body scalar values
UI-label guesses
one-report assumptions
unverified gameplay mechanics
```

If E4 contradicts an E3 assumption, preserve old provenance and record the new evidence explicitly.

## Engineering rhythm

Both tracks keep:

```text
focused tests
-> coherent commit
-> repository verification
-> push
-> exact-head CI
```

Shared invariants:

- browser/network evidence outranks stale assumptions;
- high-cardinality IDs are data scope, not schema versions;
- private/raw files are valid analysis inputs but are not public artifacts;
- published migrations are not rewritten;
- unknown writes/destructive routes require an explicit gate;
- no anti-bot bypass;
- planner scoring remains fail-closed.

## New-chat startup

E3:

```text
Продолжаем e3/real-log-capture. Прочитай docs/PROJECT_STATE.md, docs/NEXT_CHAT_HANDOFF.md и docs/PARALLEL_WORKSTREAMS_2026-08-19.md. Проверь live GitHub HEAD/PR/CI и продолжи канонический evidence path. Не повышай неподтвержденные E4 hypotheses.
```

E4:

```text
Продолжаем e4/interactive-har-discovery. Прочитай docs/PROJECT_STATE.md, docs/NEXT_CHAT_HANDOFF.md, docs/PARALLEL_WORKSTREAMS_2026-08-19.md, docs/BROWSER_OBSERVATORY.md и docs/LOCAL_WORKSPACE_BOUNDARY.md. Проверь live GitHub HEAD/PR/CI. Следующий gate — первый real private Browser Observatory scenario и анализ scalar-safe receipt.
```
