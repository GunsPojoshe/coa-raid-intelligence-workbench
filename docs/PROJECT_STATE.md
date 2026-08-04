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
- explicit usage-context review без semantic overclaim;
- offline helper/call-site inventory;
- explicit helper/call-site review с сохранением закрытого route probe.

## Guild-search limit evidence

```text
capture: evidence/real-data/argentum-guild-limit-semantics-capture.json
capture SHA-256: 690d7d93d5e9c592877a4fa049d2638b0a5a523430f9205777ce4fa06e624e58
capture checks: 15/15
review checks: 30/30
limit truncation semantics verified: true
```

Это доказывает только стабильное ограничение списка результатов guild search. Guild-report pagination этим не подтверждена.

## Progression usage-context checkpoint

```text
inventory: evidence/real-data/argentum-guild-progression-usage-context.json
inventory SHA-256: e19cc1a72175bd838b151b8438861af1aece14ba2a30f94da8f6989ce7be3d59
inventory checks: 23/23
review: evidence/real-data/argentum-guild-progression-usage-review.json
review SHA-256: 063abc51579e3942c4b33766fa9d1f9ba336a921a78bc15a5849971025a77198
review checks: 30/30
route occurrences: 1
usage classification: literal_reference
usage-context HTTP method candidates: []
usage context reviewed: true
bounded route probe ready: false
```

Этот этап не подтвердил call site или HTTP method. Он разрешил только отдельный offline helper/call-site inventory.

## Progression helper/call-site checkpoint

Versioned inventory:

```text
inventory: evidence/real-data/argentum-guild-progression-callsite.json
inventory version: guild-progression-helper-callsite-inventory-v1
inventory SHA-256: ad8a5addf9ac9dd566284e0bc395ac40100986d0f14f0a49e9519a6aef28d351
integrity checks: 32/32
network requests: 0
route occurrences: 1
call candidates: 1
direct invocation candidates: 1
call class: generic_helper_call
method candidate: POST
method candidate unambiguous: true
method evidence: method_property_literal
```

Observed structural spans:

```text
call/envelope characters: 2479207
function characters: 2411715
reviewable threshold: 65536
```

Versioned review:

```text
review: evidence/real-data/argentum-guild-progression-callsite-review.json
review version: guild-progression-helper-callsite-review-v1
review SHA-256: d79302d755eab918ce3f85a9ad39e78231720391c8f0692925fe2e79b6adc60f
integrity checks: 36/36
helper/call-site reviewed: true
HTTP method candidate: POST
helper identity resolved: false
request payload mapping resolved: false
request shape sufficient for bounded probe: false
ready for helper-definition inventory: true
ready for bounded route probe: false
```

Review зафиксировал blockers:

```text
generic_helper_identity_unresolved
structural_envelope_overbroad
request_payload_mapping_unresolved
```

`POST` является однозначным method candidate внутри найденного generic-helper call. Это не подтверждает identity helper, фактическое отображение `body/data/params`, response schema или route semantics.

Implementation:

```text
src/coa_workbench/collector/guild_progression_callsite_contract.py
src/coa_workbench/collector/guild_progression_js_index.py
src/coa_workbench/collector/guild_progression_callsite_inventory.py
scripts/inventory_guild_progression_callsite.py
src/coa_workbench/collector/guild_progression_callsite_review.py
scripts/review_guild_progression_callsite.py
tests/unit/test_guild_progression_callsite_inventory.py
tests/unit/test_guild_progression_callsite_review.py
tests/unit/test_versioned_guild_progression_callsite_review.py
```

Source receipt hashes in the deterministic review use canonical LF bytes so Linux and Windows checkouts produce the same review document.

## Last confirmed implementation checkpoint

```text
HEAD: 2bfd1e15abe715d37454db95d6b46fd17619ed99
Verify repository run: #570
public-release-audit: success
Ubuntu: success
Windows: success
pytest: 356 passed, 1 warning
Doctor: success
DuckDB clean/repeated initialization: success
migrations: 0001–0008
```

Recheck live. Do not transfer this result to a later HEAD.

## Current decision boundary

```text
guild identity verified: true
guild filtering completed: true
guild report manifest deduplicated: true
full crawl collection contract reviewed: true
guild-search route/schema verified: true
guild-search limit truncation verified: true
progression route candidate observed: true
progression usage context reviewed: true
progression helper/call-site inventory observed: true
progression helper/call-site reviewed: true
progression HTTP method candidate: POST
progression method candidate unambiguous: true
progression helper identity resolved: false
progression request payload mapping resolved: false
progression request shape verified: false
ready for helper-definition inventory: true
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

1. Generic helper identity не восстановлен из exact archived SPA asset.
2. Structural envelope около `2.48M` символов слишком широк для semantic promotion.
3. Отображение `body`, `data` и `params` в фактический POST payload не подтверждено.
4. Response schema и relation to guild report membership не подтверждены.
5. Pagination, termination и completeness не подтверждены.
6. API-derived membership не сравнивался с private 17-report baseline.
7. Multi-report character identity graph не построен.
8. Bounded report slice содержит `0` aura events.
9. Planner scoring остаётся disabled.

## Следующий допустимый bounded этап

```text
offline helper-definition inventory from the exact archived SPA asset
-> bind helper-definition candidates to the published callee hash
-> publish scalar-free definition/call-chain hashes and classifications
-> explicit helper-definition review
-> bounded progression route probe only if helper identity and exact request contract are verified
-> response schema review
-> pagination/termination/completeness evidence
-> API-versus-private-baseline set comparison
-> explicit full-crawl promotion only if every gate passes
```

Следующий этап должен быть offline-only и читать local private recovery/raw archive. До explicit helper-definition review запрещено выполнять network request к `/api/guilds/progression`.

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

Never commit source guild IDs, report IDs, source rows, private queries, private receipts, raw JavaScript contexts, raw callees, DuckDB, credentials, cookies, tokens, Authorization headers, browser profiles, `.env` or unsanitized HAR.
