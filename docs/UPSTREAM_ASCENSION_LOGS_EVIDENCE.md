# Upstream Ascension Logs evidence — E4 source-first discovery

Status date: **2026-08-19**.

This document records a new high-leverage E4 evidence source discovered after the Browser Observatory pivot.

## Pinned upstream sources

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

The Companion revision was current on 2026-08-19 and was committed upstream on 2026-08-18. Always re-check the live upstream revision before treating this pin as current.

The source pin is provenance, not automatic truth promotion. Executable code, inline comments, upstream README claims and our own captured observations have different evidence strength.

## Why this source changes E4 priority

The Companion is not merely a UI addon. It is an executable description of a large part of the data-acquisition contract that feeds Ascension Logs:

```text
WoW client APIs / combat events
-> per-player and per-encounter capture
-> structured records
-> serialization / compression / frame transport
-> WoWCombatLog.txt
-> uploader
-> server-side ingest / parsing
-> report UI
```

The public uploader README independently describes the desktop application as a thin transport that tails `WoWCombatLog.txt`, uses a durable outbox, and sends fresh lines over HTTPS while parsing, fight detection and rankings occur server-side.

This means browser/network reverse engineering is no longer the default first step for facts that can be obtained from the executable Companion source.

## Evidence classes

### A. Strong executable client-side evidence

These facts are directly represented by executable Lua and may be promoted after source review plus version pinning:

```text
which client API is called
which event triggers a capture
record field names and structural nesting
client-side scope and gating rules
per-pull / per-session cache scope
transport record type and envelope construction
which observations are direct versus fallback-derived inside the addon
```

Examples already identified:

- server/profile detection includes Conquest of Azeroth realms as Ascension-family clients;
- local Combatant Info contains player identity, guild, specialization/build data, gear, arena teams, pet, instance information and optional Ascension enrichments;
- inspected peers can contribute gear, guild/race, vanilla talents, Character Advancement data and mystic enchants when the relevant inspect paths succeed;
- Character Advancement capture uses `C_CharacterAdvancement`, including inspected build/rank APIs rather than guessed globals;
- gear capture parses itemstrings into item/enchant/gem/suffix identity and contains explicit vanity/transmog handling;
- `GetInstanceInfo()` is captured structurally as instance name/type, difficulty index/name, max players, player difficulty, dynamic flag and map id;
- encounter tracking is per pull and boss-aware;
- telemetry captures encounter/map context, roster dynamics, positions, targets, vitals and hostile NPC identity/state at a low cadence;
- controlled pets and slot-less guardians have explicit owner-attribution pipelines;
- Mythic+ has direct lifecycle/progress capture through `C_MythicPlus`, including level, dungeon id, affixes, time budget/remaining, encounter/trash/champion progress, timed/depleted outcome and durable per-run SavedVariables;
- CoA Manastorm has an explicit `C_Manastorm` event-driven lifecycle capture;
- the current frame transport includes typed CI/PP/TS records, CI keyframes and keyframe references, with KS intentionally isolated from the shared frame fate.

### B. High-value upstream claims requiring corroboration

Inline comments contain unusually rich operational findings, including live probes, backend behavior, historic report examples and parser expectations. They are extremely useful hypotheses, but they are not equivalent to the executable code that surrounds them.

Examples include claims about:

```text
friendly difficulty interpretation of raw indices
backend difficulty fallback behavior
specific historical report failures
backend creatures-table synchronization
server-side demux/reassembly behavior
server-side keyframe resolution
rankings/parser behavior
```

Promotion rule:

```text
upstream comment
+ matching executable field/event path where applicable
+ independent local/site/raw evidence when the claim is backend-semantic
= reviewed canonical evidence candidate
```

Do not promote a backend mechanic merely because an upstream comment describes it confidently.

### C. Public uploader documentation

The public `ascension-logs-uploader` repository contains documentation rather than the closed desktop client source.

It is useful evidence for the high-level ingestion boundary:

```text
WoWCombatLog.txt
-> tail/batch
-> durable outbox
-> HTTPS transport
-> server-side ingest/parser
```

It also explicitly lists a Conquest of Azeroth site and states that the heavy parsing/fight-detection/ranking logic is server-side.

It does **not** expose the uploader's concrete HTTP implementation or the server parser code, so it cannot replace network/source observation for those contracts.

## What this can replace

Before probing the report UI, first consult the pinned Companion source for:

```text
client-side difficulty observations
encounter and pull boundaries
boss registry / zone identity
character build structure
gear and enchant structure
pet / guardian ownership
position and target telemetry
Mythic+ lifecycle/progress
Manastorm lifecycle
capture reliability and fallback rules
wire/frame record structure
```

Do not spend Browser Observatory cycles rediscovering these from field names in website JSON when the upstream executable code already defines the source-side observation.

## What this does not solve by itself

The Companion does not establish all product semantics. Remaining independent evidence domains include:

```text
report website API route contracts and query semantics
server parser / aggregation implementation
server-side damage/healing attribution details not visible from capture code
rankings algorithms and percentile semantics
guild progression data contracts
cross-report encounter equivalence rules
static item/spell/talent effect semantics beyond captured ids/ranks
planner semantics: why a particular player is needed by a particular composition
UI-only state and presentation rules
```

Browser/network discovery remains useful for these unresolved server/UI surfaces.

## Revised E4 discovery order

Use the following order for a question that may touch Ascension Logs:

```text
1. Check pinned upstream executable Companion source.
2. Classify the finding: executable fact vs inline claim vs inferred behavior.
3. Compare with already persisted RawArchive / observations / report evidence.
4. If server/UI semantics remain unresolved, acquire the narrowest manual-browser HAR or reviewed browser observation needed.
5. Promote only the corroborated relation into source contracts / analytics.
```

This is source-first, not source-only.

## Difficulty gate revision

The current cross-report blocker should no longer begin with "find the Difficulty UI request".

The upstream client source already shows a direct instance observation boundary around `GetInstanceInfo()` and persists the raw difficulty-related fields into Combatant Info and telemetry. Therefore the next difficulty investigation should be:

```text
upstream client instance fields
+ existing persisted report evidence
+ one known report/encounter where client-side difficulty capture landed
-> determine whether the site exposes or transforms the same signal
-> prove mapping/equivalence only when independently corroborated
```

The upstream comments about friendly labels or backend fallback are hypotheses until matched against real local/report evidence.

## Network-environment boundary

Site reachability is environment-dependent. A report route may succeed through one operator network path while another route yields only a shell document or stalls.

Do not commit proxy/VPN credentials, host details or operator network configuration.

For private acquisition, the preferred fallback is the operator's already-working normal browser plus manual DevTools HAR. That HAR can feed the existing provider-neutral `HARObservationSource` and interaction differential pipeline without requiring the site to be navigated by Playwright.

Browser Observatory remains reusable infrastructure for sources/environments where live automated acquisition is appropriate and reliable; it is no longer a prerequisite for Ascension Logs evidence discovery.

## Immediate implementation direction

Next E4 code should treat upstream source as a first-class evidence provider rather than copying facts into prose by hand.

Target shape:

```text
pinned upstream source manifest
-> reviewed source-file inventory
-> extracted evidence candidates
   - client API names
   - emitted field paths
   - event names
   - record/stream types
   - source-code locations
-> evidence-strength classification
-> comparison against local Source Observatory facts
-> scalar-safe review receipt
```

The extractor must not infer gameplay mechanics from Lua identifiers or comments. It should automate inventory and provenance; semantic promotion remains reviewed and corroborated.
