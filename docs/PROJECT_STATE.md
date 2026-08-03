# Фактическое состояние проекта

Дата актуализации: **2026-08-03**.

Документ фиксирует operational state. Перед работой обязательно перепроверять GitHub, branch HEAD, PR, CI, code, local private artifacts и versioned receipts. HEAD не фиксируется внутри этого файла как постоянная истина, потому что само обновление документа создаёт новый commit.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

На момент последней сверки PR #7 был `open`, `Draft` и `mergeable`. Это состояние перепроверять live.

## Последний полностью подтверждённый green baseline

```text
commit: 93f4e801a7251382bedc60f4deda1b84ec7bbda0
Verify repository run: #513
public-release-audit: success
Ubuntu: success
Windows: success
Ruff lint/format: success
pytest: 318 passed
Doctor: success
clean/repeated DuckDB initialization: success
```

После этого baseline были добавлены versioned route/schema review receipt, documentation refresh и bounded multi-result limit probe. Их актуальный CI необходимо проверять по текущему HEAD; старый run нельзя переносить на новый commit.

## Простыми словами: текущий этап

Мы уже подтвердили:

- откуда безопасно брать данные;
- как хранить исходные ответы без изменения;
- как проверять schema и hashes;
- какая guild identity относится к Argentum;
- какие 17 public reports относятся к ней;
- какой route используется для поиска гильдий;
- как выглядит response schema;
- что сервер принимает параметр `limit`.

Сейчас мы проверяем следующий узкий вопрос: работает ли `limit` как стабильное ограничение списка из нескольких результатов.

Код проверки готов. Реальный multi-result capture ещё не versioned и не review-promoted. Full crawl всё ещё запрещён.

## Trust boundary

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

Parser/schema verification, guild identity verification, filtering, collection contract review, route/schema review и успешный capture не подтверждают игровую механику. Canonical planner scoring допускает только `corroborated` и `confirmed` mechanics.

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

## Public manifest checkpoint

```text
receipt: evidence/real-data/argentum-public-report-manifest.json
route: /api/reports/public
limit: 25
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
integrity checks: 19/19
exact Argentum label reports: 17
```

## Guild identity checkpoint

```text
receipt: evidence/real-data/argentum-guild-identity-decision.json
integrity checks: 16/16
explicit operator promotion: true
guild identity verified: true
ready for guild filtering: true
```

Source guild ID остаётся private.

## Deterministic filtering checkpoint

```text
receipt: evidence/real-data/argentum-guild-report-manifest.json
source public reports: 6454
selected guild reports: 17
unique selected report IDs: 17
filter integrity checks: 14/14
guild filtering completed: true
guild report manifest deduplicated: true
```

Report IDs и selected records остаются private.

## Full-crawl collection contract checkpoint

```text
receipt: evidence/real-data/argentum-guild-full-crawl-contract.json
integrity checks: 12/12
full crawl collection contract reviewed: true
verified private comparison baseline: 17 reports
```

Contract не разрешает full crawl. Он определяет обязательные gates и будущий set-comparison contract.

## Bounded route-semantics capture checkpoint

```text
receipt: evidence/real-data/argentum-guild-route-semantics-capture.json
attempts: 3
completed attempts: 3
HTTP 200 responses: 3
integrity checks: 13/13
observed result counts: [1]
payload hash stable: true
schema fingerprint stable: true
source ID set stable by hash: true
pagination object observed: false
```

Observed cases:

```text
/api/guilds/search?q=<target>&limit=1
/api/guilds/search?q=<target>&limit=25
/api/guilds/search?q=<target>
```

## Route shape and response schema review checkpoint

```text
receipt: evidence/real-data/argentum-guild-route-semantics-review.json
review version: guild-route-semantics-review-v1
integrity checks: 22/22
route template verified: true
query shapes verified: true
response envelope verified: true
guild record schema verified: true
limit parameter accepted: true
ready for bounded limit-semantics capture: true
```

Verified record fields:

```text
id: integer
name: string
realm: string
report_count: string
```

Все три cases вернули одинаковую single-result выдачу. Limit truncation, pagination, termination и completeness не подтверждены.

## Bounded multi-result limit probe — implementation completed

```text
src/coa_workbench/collector/guild_limit_semantics_capture.py
scripts/capture_guild_limit_semantics.py
tests/unit/test_guild_limit_semantics_capture.py
```

Implementation properties:

- exactly three requests;
- low limit, high limit and repeated high limit;
- same-origin HTTPS;
- redirects disabled;
- retries disabled;
- no cookies, Authorization or credentials;
- bounded timeout and response size;
- archive complete raw bytes before interpretation;
- private query and raw rows stay local-only;
- public receipt contains only counts, hashes, schemas and boolean decisions;
- successful capture does not promote limit semantics automatically.

Deterministic tests cover:

1. stable multi-result prefix evidence;
2. single-result capture not ready for review;
3. high-limit repeat drift blocks review;
4. changed route-review boundary blocks network execution;
5. public receipt privacy boundary.

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
ready for bounded limit-semantics capture: true
limit truncation semantics verified: false
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

1. Актуальный HEAD должен пройти green `public-release-audit`, Ubuntu и Windows CI.
2. Реальный bounded multi-result limit capture ещё не выполнен/не versioned.
3. Отдельный limit-semantics review ещё не выпущен.
4. Pagination semantics не подтверждены.
5. Termination semantics не подтверждены.
6. Completeness boundary не подтверждён.
7. API-derived report membership не сравнивался с private 17-report baseline.
8. Multi-report character identity graph не построен.
9. Bounded report slice содержит `0` aura events.
10. Нет новой gameplay mechanic с independent supporting and contradicting evidence.
11. Planner scoring остаётся disabled.

## Следующие шаги

### Шаг 1. Проверить CI

Получить green на current HEAD:

```text
public-release-audit
Ubuntu repository verifier
Windows pytest + Doctor + repeated DuckDB initialization
```

### Шаг 2. Выполнить local bounded multi-result capture

Запускать только после green CI. Требуется privacy-safe private query, ожидаемо возвращающая несколько guild records.

```powershell
uv run --no-sync python scripts/capture_guild_limit_semantics.py --query "<PRIVATE_MULTI_RESULT_QUERY>"
```

Accepted exit codes:

```text
0 = capture ready for limit-semantics review
2 = bounded capture completed, but evidence is insufficient for review
```

Local private output:

```text
data/extracted/report-discovery/argentum-guild-limit-semantics-capture.private.json
```

Public output:

```text
data/exchange/out/argentum-guild-limit-semantics-capture.json
```

Upload/version only the public output. Never upload the private query, private capture, raw archive or DuckDB.

### Шаг 3. Review capture

- validate exact receipt kind/version;
- verify source route-review binding;
- verify all integrity checks;
- inspect result counts and repeat stability;
- confirm prefix relation by hashes;
- keep query and IDs private;
- version scalar-free capture receipt only if safe;
- implement separate limit-semantics review;
- keep `limit_truncation_semantics_verified=false` until explicit review promotion.

### Шаг 4. Следующие independent gates

```text
explicit limit-semantics review
-> pagination review
-> termination/completeness review
-> API-versus-private-baseline set comparison
-> explicit full-crawl promotion
```

### Шаг 5. После full-crawl promotion

```text
per-report report/encounter/combatants capture
-> coverage and failure accounting
-> stable multi-report character identity
-> 30-40 candidate characters
-> performance observations
-> global benchmark corpus
-> confidence-aware scoring
-> constrained BiS 25 optimizer
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

Never commit source guild IDs, report IDs, report rows, private queries, private manifests, private decisions, DuckDB, credentials, cookies, tokens, Authorization headers, browser profiles, `.env` or unsanitized HAR.

## Completion gate

PR #7 remains Draft until reviewed identity/filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows verification are present.
