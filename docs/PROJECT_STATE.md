# Фактическое состояние проекта

Дата актуализации: **2026-08-04**.

Документ фиксирует operational state. Перед работой перепроверять GitHub, branch HEAD, PR, CI, code, local private artifacts и versioned receipts. HEAD не фиксируется здесь как постоянная истина.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

На последней live-проверке PR #7 был `open`, `Draft` и `mergeable`.

## Последний green checkpoint

```text
HEAD: 6a6a28aaf5a8cf6e4d9240e19b714073a0096282
Verify repository run: #551
public-release-audit: success
Ubuntu repository verifier: success
Windows: success
pytest: 335 passed, 1 warning
Doctor: success
clean DuckDB initialization: success
repeated DuckDB initialization: success
migrations: 0001–0008
```

Node.js deprecation warnings относятся к pinned third-party Actions и не являются failure.

## Текущий этап простыми словами

Подтверждены:

- identity гильдии Argentum;
- private comparison baseline из 17 отчётов;
- `/api/guilds/search` route и response schema;
- принятие параметра `limit`;
- стабильное multi-result ограничение выдачи: `1 / 7 / 7`;
- explicit limit-truncation review.

Но `/api/guilds/search` возвращает список гильдий, а не guild report corpus. Поэтому нельзя автоматически переходить к full-crawl pagination.

Recovered SPA asset содержит единственный дополнительный guild route candidate:

```text
/api/guilds/progression
```

Для него пока не доказаны HTTP method, request shape, response schema, связь с report membership, pagination или termination.

## Trust boundary

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

Parser/schema verification, identity verification, filtering и route/limit reviews не подтверждают gameplay mechanics. Planner scoring допускает только `corroborated` и `confirmed` mechanics.

## Report/encounter и combatants checkpoint

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants, 0 field conflicts
persisted through 0007: 77 canonical entity observations
combatants through 0008: 1343 parser observations
actor/build observations: 1339
linked actors: 11
combatants integrity checks: 14/14
```

## Public manifest, identity и filtering

```text
public reports: 6454
unique public report IDs: 6454
public-manifest integrity checks: 19/19
exact Argentum label reports: 17
identity-decision integrity checks: 16/16
guild identity verified: true
selected guild reports: 17
unique selected report IDs: 17
filter integrity checks: 14/14
```

Source guild ID, report IDs и selected rows остаются private.

## Full-crawl collection contract

```text
receipt: evidence/real-data/argentum-guild-full-crawl-contract.json
integrity checks: 12/12
full crawl collection contract reviewed: true
verified private comparison baseline: 17 reports
```

Contract определяет обязательные gates и future set comparison, но не разрешает full crawl.

## Guild-search route/schema checkpoint

```text
capture: evidence/real-data/argentum-guild-route-semantics-capture.json
review: evidence/real-data/argentum-guild-route-semantics-review.json
route: /api/guilds/search
route review integrity checks: 22/22
response envelope: guilds, success
guild fields: id, name, realm, report_count
limit parameter accepted: true
```

## Multi-result limit checkpoint

```text
capture: evidence/real-data/argentum-guild-limit-semantics-capture.json
capture SHA-256: 690d7d93d5e9c592877a4fa049d2638b0a5a523430f9205777ce4fa06e624e58
attempts: 3
completed: 3
HTTP 200: 3
result counts: 1 / 7 / 7
capture integrity checks: 15/15

review: evidence/real-data/argentum-guild-limit-semantics-review.json
review version: guild-limit-semantics-review-v1
review integrity checks: 30/30
limit truncation semantics verified: true
```

Confirmed relations:

```text
response schema consistent: true
low limit saturated: true
multi-result observed: true
high limit respected: true
high-limit repeat stable: true
source-ID order stable by hash: true
low result is exact high-result prefix by ID hash: true
```

## SPA asset route candidate evidence

Versioned profiled recovery:

```text
evidence/real-data/argentum-guild-asset-profiled-recovery.json
asset download completed: true
HTTP 200: true
asset bytes: 3881146
integrity checks: 15/15
all API route candidates: 79
guild route candidates: 3
```

Observed scalar-free guild route shapes:

```text
/api/guilds/progression
/api/guilds/search?q=<value>
/api/guilds/search?q=<value>&limit=<value>
```

Search routes уже reviewed. `/api/guilds/progression` остаётся lexical candidate без verified usage semantics.

## Implemented nearest bounded tool

```text
src/coa_workbench/collector/guild_progression_usage_inventory.py
scripts/inventory_guild_progression_usage.py
tests/unit/test_guild_progression_usage_inventory.py
```

Tool properties:

- offline-only: no network requests;
- validates public/private profiled recovery binding;
- resolves exact archived asset through payload SHA-256;
- verifies content manifest, gzip payload hash and byte count;
- inventories every bounded occurrence of `/api/guilds/progression`;
- keeps raw JavaScript context in private local output;
- public receipt contains only context hashes, call-style/method candidates and booleans;
- never promotes route, pagination, termination, completeness or full crawl.

Expected local outputs:

```text
private:
  data/extracted/report-discovery/argentum-guild-progression-usage-context.private.json

public:
  data/exchange/out/argentum-guild-progression-usage-context.json
```

## Current decision boundary

```text
guild identity verified: true
guild filtering completed: true
guild report manifest deduplicated: true
full crawl collection contract reviewed: true
guild-search route template verified: true
guild-search response schema verified: true
guild-search limit truncation semantics verified: true
progression route candidate observed: true
progression usage context reviewed: false
progression route semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Current blockers

1. Local progression usage-context inventory ещё не выполнен/versioned.
2. HTTP method и request shape `/api/guilds/progression` не reviewed.
3. Progression response schema и relation to guild report membership не verified.
4. Pagination, termination и completeness не подтверждены.
5. API-derived report membership не сравнивался с private 17-report baseline.
6. Multi-report character identity graph не построен.
7. Bounded report slice содержит `0` aura events.
8. Planner scoring остаётся disabled.

## Следующая evidence sequence

```text
offline SPA usage-context inventory
-> explicit usage-context review
-> bounded progression route probe only if method/request shape are unambiguous
-> response schema review
-> pagination/termination/completeness evidence
-> API-versus-private-baseline set comparison
-> explicit full-crawl promotion only if every gate passes
```

## Data and Git policy

Versioned: source code/tests, migrations, reviewed mappings, canonical documentation and scalar-free evidence receipts.

Local-only:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never commit source guild IDs, report IDs, source rows, private queries, private captures, raw JavaScript contexts, DuckDB, credentials, cookies, tokens, Authorization headers, browser profiles, `.env` or unsanitized HAR.
