# CoA Raid Leader Companion — durable project context

Updated: **2026-08-28**.

## Product goal

Build a localhost-first raid leader companion for **Conquest of Azeroth** that combines actual roster state, verified player/build observations, encounter evidence and population context to explain composition decisions.

The product is an independent BI/decision-support system. It is not a mirror of Ascension Logs and not a permanent optimal-roster list.

Primary question:

> **Почему конкретный человек нужен именно текущему составу?**

## Domain boundary

CoA-only. Shared Ascension/Classless/Mystic/Hero Architect material is not a CoA fact without exact evidence.

## Truth model

```text
observation != universal mechanic
field name != semantic proof
UI label != backend contract
character name != cross-report identity
one result != stable capability
population aggregate != planner recommendation
```

## Architecture

```text
Browser -> FastAPI -> Planner / Analytics -> DuckDB

source contract
-> local immutable evidence
-> deterministic normalization
-> provenance/dependencies
-> independent analytics
-> Source & Analysis Health
-> trust-gated recommendations
```

## Source hierarchy

```text
1. official documented CoA Ascension Logs public API
2. official documented semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API observations
5. narrow browser/network fallback
6. structural inference last
```

## Official public API

Self-service aggregate lane:

```text
GET /phases
GET /bosses
GET /statistics
```

Experimental/on-request event lane is documented separately for reports, actors and encounter events. It is a potential raw-fact source for our own combat analytics, not a dependency of the aggregate lane.

## Proven data platform

```text
forward-only migrations 0001-0013
RawArchive + source acquisition observations
Source Observatory + schema/profile/scope cycles
source_endpoint_profile dependency
profile-scoped reanalysis
public_api_population_prior_v1
bounded public population coverage model/workflow
encounter context + matched location comparator
report encounter/population provenance binding
report-scoped roster/build observations
localhost read models/API
```

## Report/build boundary

Persisted report evidence proves report-scoped identity/build linkage for two report scopes. It does not prove cross-report identity, current/latest build freshness, mechanic requirements or player capability.

The official public API v1.0.0 does not document builds/talents/gear/enchants, Armory or guild-progression endpoints, so those remain explicit evidence gaps with Companion/first-party fallback options.

## Pinned Companion

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

## Privacy/publication boundary

Private/raw data stays local by default. Do not commit API keys, cookies, raw payloads, DuckDB, private query values, player/report identifiers, build values or private fingerprints. Public receipts are scalar-safe reviewed summaries.

## Development model

`main` is canonical. Use short-lived branches and coherent PRs. Published migrations are immutable. Exact-head CI must pass before integration.

## Long-term product path

```text
raid composition state
+ population context
+ encounter facts
+ player/build evidence
+ corroborated mechanics/requirements
-> explainable roster recommendations and alternatives
```

Planner scoring remains fail-closed until the required semantic gates are proven.
