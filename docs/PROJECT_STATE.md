# Фактическое состояние проекта

Дата актуализации: **2026-08-04**.

Документ фиксирует operational state. Перед работой обязательно перепроверять GitHub, branch HEAD, PR, CI, code, local private artifacts и versioned receipts. HEAD не фиксируется внутри этого файла как постоянная истина, потому что само обновление документа создаёт новый commit.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #7 остаётся `open`, `Draft` и `mergeable`; это состояние всегда перепроверять live.

## Текущий этап простыми словами

Подтверждены identity гильдии Argentum, private baseline из 17 отчётов, guild-search route, response schema и ограничение multi-result выдачи параметром `limit`.

Versioned scalar-free capture показал стабильную выдачу `1 / 7 / 7` для low limit, high limit и повторного high limit. Отдельный deterministic review повысил только `limit_truncation_semantics_verified=true`.

Следующий узкий этап — bounded pagination-semantics capture и отдельный review. Full crawl, character graph, performance model, BiS 25 и planner scoring остаются запрещены.

## Trust boundary

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

Parser/schema verification, identity verification, filtering и route/limit reviews не подтверждают gameplay mechanics. Planner scoring допускает только `corroborated` и `confirmed` mechanics.

## Реализованный фундамент

- localhost FastAPI raid planner и DuckDB plans;
- immutable content-addressed raw archive;
- separate retrieval observations;
- JSON/HAR privacy-safe tooling;
- schema fingerprints и reviewed mappings;
- canonical report/encounter/actor/participant/aura records;
- normalization/reconstruction/persistence pipeline;
- migrations `0001`–`0008`;
- repository verifier;
- Ubuntu/Windows CI;
- public-release audit.

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

Contract определяет будущие gates и set-comparison contract, но не разрешает full crawl.

## Route/schema checkpoint

```text
capture: evidence/real-data/argentum-guild-route-semantics-capture.json
review: evidence/real-data/argentum-guild-route-semantics-review.json
route review integrity checks: 22/22
route template verified: true
query shapes verified: true
response envelope verified: true
guild record schema verified: true
limit parameter accepted: true
```

Verified record fields:

```text
id: integer
name: string
realm: string
report_count: string
```

## Multi-result limit capture checkpoint

```text
receipt: evidence/real-data/argentum-guild-limit-semantics-capture.json
capture version: guild-limit-semantics-capture-v1
capture SHA-256: 690d7d93d5e9c592877a4fa049d2638b0a5a523430f9205777ce4fa06e624e58
attempts: 3
completed attempts: 3
HTTP 200 responses: 3
observed result counts: 1 / 7 / 7
integrity checks: 15/15
ready for limit-semantics review: true
```

Capture evidence:

```text
response schema consistent: true
low limit saturated: true
multi-result observed: true
high limit respected: true
high-limit repeat stable: true
source-ID order stable by hash: true
low result is exact high-result prefix by ID hash: true
```

Capture сохранил `limit_truncation_semantics_verified=false` и не повысил другие gates.

## Explicit limit-semantics review checkpoint

```text
receipt: evidence/real-data/argentum-guild-limit-semantics-review.json
review version: guild-limit-semantics-review-v1
integrity checks: 30/30
source capture SHA-256 verified: true
source route-review binding verified across LF/CRLF: true
limit truncation semantics verified: true
ready for bounded pagination-semantics capture: true
```

Review implementation:

```text
src/coa_workbench/collector/guild_limit_semantics_review.py
scripts/review_guild_limit_semantics.py
tests/unit/test_guild_limit_semantics_review.py
tests/unit/test_versioned_guild_limit_semantics_review.py
```

Public capture/review не содержат private query, request URLs, source guild IDs, raw records или raw payloads.

## Current decision boundary

```text
guild identity verified: true
guild filtering completed: true
guild report manifest deduplicated: true
full crawl collection contract reviewed: true
guild route template verified: true
guild query shapes verified: true
guild response schema verified: true
limit parameter accepted: true
limit truncation semantics verified: true
ready for bounded pagination-semantics capture: true
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

1. Current HEAD должен пройти green `public-release-audit`, Ubuntu и Windows CI.
2. Pagination semantics не подтверждены.
3. Termination semantics не подтверждены.
4. Completeness boundary не подтверждён.
5. API-derived report membership не сравнивался с private 17-report baseline.
6. Multi-report character identity graph не построен.
7. Bounded report slice содержит `0` aura events.
8. Нет gameplay mechanic с independent supporting and contradicting evidence.
9. Planner scoring остаётся disabled.

## Следующий bounded этап

```text
bounded pagination-semantics capture
-> explicit pagination review
-> termination/completeness evidence and review
-> API-versus-private-baseline set comparison
-> explicit full-crawl promotion only if every gate passes
```

До green CI текущего HEAD следующий network capture не выполнять.

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

Never commit source guild IDs, report IDs, source rows, private queries, private captures, DuckDB, credentials, cookies, tokens, Authorization headers, browser profiles, `.env` or unsanitized HAR.

## Completion gate

PR #7 остаётся Draft до появления reviewed identity/filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, reproducible provenance и green Ubuntu/Windows verification.
