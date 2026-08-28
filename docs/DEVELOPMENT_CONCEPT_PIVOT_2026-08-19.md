# Development concept pivot — 2026-08-19

## Purpose

This document is the explicit savepoint for changing the E4 discovery workflow from manual HAR-first iteration to a reusable Browser Observatory architecture.

The evidence-first trust model is **not** being relaxed. The pivot changes how observations are acquired, correlated and handed to deterministic project code.

## Pre-pivot checkpoints

Canonical E3 baseline:

```text
78127a990966a599d7b67cb1a56746aa2701d0bd
Make continuation handoff branch-aware
```

E4 pre-pivot savepoint:

```text
b01dfdaa3d9c52ac93ee1a7e57de91a15f9c464a
Document isolated interactive HAR discovery track
```

Exact-head E4 CI before this pivot:

```text
Verify repository #859
ubuntu               success
windows              success
public-release-audit success
```

`b01dfdaa...` is the immutable conceptual rollback point for the original controlled interaction-HAR experiment.

## Why the workflow changes

The current project has already proven the expensive foundations:

```text
reviewed browser/network contracts
immutable RawArchive
Source Observatory
schema/profile/scope observation
source-change registry
scoped dependency/reanalysis
first-report derived persistence
combat analytics persistence
second-report generalization
cross-report structural cohorts
scope-aware schema repair
```

The limiting factor is now the unit of discovery work:

```text
question
-> one-off diagnostic
-> operator downloads/runs helper
-> one small receipt
-> next question
-> another diagnostic
```

That pattern was useful while proving the first unknown source contracts. It is not appropriate for systematic coverage of Reports, Rankings, Statistics, Characters, Guild, Armory, talent-grid and BisBeard.

## New target architecture

Primary model:

```text
instrumented browser session
-> ordered UI/action timeline
-> NetworkObservation stream
-> immutable raw capture
-> Source Observatory
-> structural/relation profiling
-> scenario coverage
-> deterministic evidence gates
-> scalar-safe receipt
```

HAR remains supported as:

```text
forensic artifact
interchange format
fallback observation adapter
replay input
```

HAR is no longer intended to be the only primary acquisition unit.

## Stable core that must be preserved

Do not replace or bypass:

```text
RawArchive
source registry / contract versioning
provenance
scope-aware schema boundaries
profile-aware schema boundaries
dependency and reanalysis graph
public/private publication boundary
fail-closed mechanic/planner trust
real-data proof receipts
published migrations
```

The Browser Observatory feeds these components; it does not create a competing source of truth.

## New components

### 1. NetworkObservation abstraction

Define one provider-neutral internal observation model that can be produced by:

```text
HAR adapter
live browser adapter
future archived/replay adapters
```

Private request/response values may exist internally. Public summaries must remain scalar-safe.

### 2. Browser Observatory

Target: headed browser with a dedicated private automation profile.

Capture at least:

```text
page/session context
action markers
request method and URL
query/body key shapes
response status/content type
response body for immutable private archive
timestamps
request/response ordering
```

Unknown write/destructive actions remain gated. No anti-bot bypass.

### 3. Action timeline

Network traffic must be correlatable with explicit operator actions rather than inferred only from rough HAR timestamps.

Example conceptual unit:

```text
action N
-> stable before-state label
-> one operator action
-> request burst or network-silent window
-> stable after-state label
```

UI labels are evidence context, not semantic proof.

### 4. Scenario manifest and coverage

Discovery becomes scenario-oriented rather than file-oriented.

Example families:

```text
reports.list
reports.filters
report.overview
report.encounters
report.roster
report.damage
report.healing
report.throughput
character.profile
guild.profile
guild.progression
rankings
statistics
armory
talent_grid
bisbeard
```

Each scenario can track observed actions, endpoint families, unresolved relations and coverage state.

### 5. Generic structural/relation profiler

Prefer one reusable profiler over chains of narrow diagnostics. Candidate structural checks include:

```text
field paths and JSON types
nullability/cardinality
constant-within-scope
candidate identifiers
exact equality/subset relations
one-to-one and one-to-many structural relations
cross-surface equality
cross-report stability
value-change correlation
field co-occurrence
```

Structural relations may be automated. Gameplay mechanic semantics still require their own evidence and trust promotion.

### 6. Operator runner

The operator should not remain a transport layer for a succession of downloaded PowerShell helpers.

Target one stable project entry point for local/private tasks and one stable result location under ignored local data.

## Trust layers

Keep separate:

```text
transport / structure
    observed endpoint, key, schema, request correlation

domain identity
    report/encounter/difficulty/character identity established by repeatable invariants

gameplay semantics
    mechanic or utility meaning supported by combat/domain evidence
```

Automation may accelerate the first two layers. It must not silently promote the third.

## Development sequence after this checkpoint

```text
A. workspace/private boundary + pre-pivot savepoint
B. provider-neutral NetworkObservation + HAR adapter
C. action/session manifest format
D. interaction-trace differential analyzer
E. dedicated browser profile + live browser adapter
F. scenario coverage manifest
G. generic relation profiler
H. stable operator command / localhost Source Lab
I. migrate proven discovery flows onto the new adapters
```

Every coherent code slice keeps the project rhythm:

```text
focused tests
-> coherent commit
-> repository verification
-> exact-head CI
```

## Promotion boundary back to E3

E4 remains an isolated child of E3 until real evidence proves the accelerated workflow.

Mergeable outputs:

```text
provider-neutral observation interfaces
reviewed deterministic adapters/reviewers
focused tests
reviewed source contracts/profiles
scalar-safe evidence receipts
documentation
```

Do not merge raw browser state, HAR bodies, screenshots, private IDs/values, or unreviewed semantic hypotheses.
