# Фактическое состояние проекта

Дата актуализации: **2026-08-04**.

Перед любой работой перепроверять live-состояние GitHub, HEAD ветки, PR, CI, versioned receipts и local-only artifacts. HEAD не фиксируется в этом документе как постоянная истина: обновление документа само создаёт новый commit.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #7 должен оставаться `open`, `Draft` и `mergeable`, пока не закрыты evidence gates.

## Подтверждённые checkpoints

- public manifest: `6454` уникальных отчёта;
- Argentum identity decision;
- private comparison baseline: `17` отчётов;
- full-crawl collection contract;
- `/api/guilds/search` route/schema review;
- bounded multi-result limit capture `1 / 7 / 7`;
- explicit limit-truncation review;
- offline SPA usage-context inventory для `/api/guilds/progression`;
- explicit usage-context review без semantic overclaim.

## Guild-search limit evidence

```text
capture: evidence/real-data/argentum-guild-limit-semantics-capture.json
capture SHA-256: 690d7d93d5e9c592877a4fa049d2638b0a5a523430f9205777ce4fa06e624e58
capture checks: 15/15
review checks: 30/30
limit truncation semantics verified: true
```

Это доказывает только стабильное ограничение списка результатов guild search. Guild-report pagination этим не подтверждена.

## Progression usage inventory

```text
inventory: evidence/real-data/argentum-guild-progression-usage-context.json
inventory version: guild-progression-usage-context-inventory-v1
inventory SHA-256: e19cc1a72175bd838b151b8438861af1aece14ba2a30f94da8f6989ce7be3d59
integrity checks: 23/23
network requests: 0
route occurrences: 1
call styles: literal_reference
method candidates: []
method candidate unambiguous: false
query construction markers: []
```

Public inventory не содержит raw JavaScript context, asset URL, source guild ID или source scalar values. Raw context остаётся private/local.

## Explicit progression usage review

```text
review: evidence/real-data/argentum-guild-progression-usage-review.json
review version: guild-progression-usage-context-review-v1
review SHA-256: 063abc51579e3942c4b33766fa9d1f9ba336a921a78bc15a5849971025a77198
integrity checks: 30/30
usage context reviewed: true
actual invocation observed: false
HTTP method resolved: false
bounded route probe ready: false
```

Review зафиксировал три blockers:

```text
http_method_unresolved
literal_reference_without_call_site
invocation_shape_unresolved
```

Единственная строковая ссылка на route не доказывает HTTP method, фактический call site или request shape. Выполнять network probe с угаданным `GET`/`POST` запрещено.

Implementation:

```text
src/coa_workbench/collector/guild_progression_usage_inventory.py
scripts/inventory_guild_progression_usage.py
src/coa_workbench/collector/guild_progression_usage_review.py
scripts/review_guild_progression_usage.py
tests/unit/test_guild_progression_usage_inventory.py
tests/unit/test_guild_progression_usage_review.py
tests/unit/test_versioned_guild_progression_usage_review.py
```

## Current decision boundary

```text
guild identity verified: true
guild filtering completed: true
guild report manifest deduplicated: true
full crawl collection contract reviewed: true
guild-search route/schema verified: true
guild-search limit truncation verified: true
progression route candidate observed: true
progression usage context observed: true
progression usage context reviewed: true
progression HTTP method resolved: false
progression request shape verified: false
ready for bounded progression route probe: false
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

1. SPA asset содержит только literal route reference; фактический caller/helper не восстановлен.
2. HTTP method `/api/guilds/progression` не определён.
3. Request body/query shape не определены.
4. Response schema и relation to guild report membership не подтверждены.
5. Pagination, termination и completeness не подтверждены.
6. API-derived membership не сравнивался с private 17-report baseline.
7. Multi-report character identity graph не построен.
8. Bounded report slice содержит `0` aura events.
9. Planner scoring остаётся disabled.

## Следующий допустимый bounded этап

```text
offline helper/call-site recovery from archived SPA asset
-> scalar-free public inventory
-> explicit helper/call-site review
-> bounded progression route probe only if exact method and request shape become unambiguous
-> response schema review
-> pagination/termination/completeness evidence
-> API-versus-private-baseline set comparison
-> explicit full-crawl promotion only if every gate passes
```

Следующий этап должен быть offline-only и читать local private recovery/raw archive. До explicit review запрещено выполнять network request к `/api/guilds/progression`.

## Trust boundary

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

Parser/schema, identity, filtering и route reviews не подтверждают gameplay mechanics. Planner scoring допускает только `corroborated` и `confirmed` mechanics.

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

Never commit source guild IDs, report IDs, source rows, private queries, private receipts, raw JavaScript contexts, DuckDB, credentials, cookies, tokens, Authorization headers, browser profiles, `.env` or unsanitized HAR.
