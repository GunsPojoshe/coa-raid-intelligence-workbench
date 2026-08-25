# Upstream Ascension Logs evidence

Status date: **2026-08-26**.

This document defines the pinned executable-client evidence lane. It is subordinate to the official public API where that API documents the same information, and stronger than speculative frontend inference for client-side behavior.

## Pinned sources

Primary executable reference:

```text
FangYuanWoW/AscensionLogsCompanion
branch: main
revision: 0f63fe9c50b470402e3a29fba2e0322095856fd4
version in .toc: 0.67.2
license: MIT
```

Public uploader documentation:

```text
FangYuanWoW/ascension-logs-uploader
branch: master
revision: 52e25780ade0c0b3ea954d649a875ea2f7d8c9bd
```

Pins provide reproducible provenance. Re-check live upstream before calling a pin “current”.

## Evidence strength

### Executable Lua

Strong evidence for:

```text
client API calls
event triggers
record field names/nesting
client-side gating/scope
capture lifecycle
serialization/frame construction
direct vs fallback-derived client observations
```

### Inline comments/backend notes

Useful hypotheses only when they describe server/parser/ranking behavior. Promote them only after independent corroboration.

### Uploader documentation

Supports the high-level boundary:

```text
WoWCombatLog.txt
-> tail/batch/outbox
-> HTTPS transport
-> server-side ingest/parser/ranking
```

It does not expose closed server parser logic.

## High-value executable areas already identified

The pinned Companion contains client-side evidence for:

```text
CoA/Ascension server profile detection
Combatant Info identity/spec/build/gear structures
Character Advancement capture
gear item/enchant/gem/suffix parsing
GetInstanceInfo structural capture
per-pull encounter tracking
position/target/vitals/NPC telemetry
pet/guardian ownership
Mythic+ lifecycle/progress
CoA Manastorm lifecycle
CI/PP/TS frame transport and keyframe relationships
```

These are observation/capture structures, not automatic mechanic semantics.

## Deterministic project tooling

The repository already contains durable upstream-source tooling, including:

```text
config/upstream_evidence_sources.yaml
scripts/review_upstream_lua_source.py
scripts/review_upstream_lua_lineage.py
```

Use these instead of copying unreviewed source facts manually into product logic.

## What the official API now replaces

Do not use Companion/browser work to rediscover API-v1 facts already documented for:

```text
phases
boss catalog
aggregate statistics dimensions/metric fields
event units/types when experimental schema documentation alone is sufficient
```

## What Companion remains best for

Use the pinned source for gaps such as:

```text
client-side build/talent/gear observation
capture lifecycle and reliability
client event/source provenance
telemetry fields
pet/guardian ownership
client difficulty/instance raw observations
wire/frame record structure
```

## What it does not solve

Independent evidence is still required for:

```text
server parser/aggregation implementation
site Tier List algorithm
rankings percentile implementation beyond published contract
Guild progression contracts
cross-report identity/equivalence
static spell/item/talent gameplay effects
why one player is needed by one composition
```

## Current source order

```text
official public API
-> official site semantics
-> pinned executable Companion
-> persisted first-party report/API evidence
-> narrow browser/network fallback
-> inference last
```

## Difficulty history

The Companion's `GetInstanceInfo()` observations are useful independent client-side evidence, but they have not resolved the historical two-report semantic equivalence gate. Backend-friendly-label/fallback comments remain hypotheses.

Do not resume difficulty work merely because a field exists. Reopen it only when a concrete product decision requires cross-report equivalence and the exact independent binding evidence is available.

## Network/browser relationship

Browser/network acquisition remains useful only for server/UI contracts not covered by official API, executable source or existing persisted evidence.

Do not use stealth or anti-bot bypass. If a permitted browser observation is needed, capture the narrowest evidence necessary and preserve the public/private boundary.

## Current direction

The immediate active E4 gate is official `/statistics` normalization/persistence. Companion source work proceeds in parallel only for unresolved client-state/build/capture surfaces; it is not the blocker for population-statistics implementation.
