# Source observability, change registry and reanalysis

Дата актуализации: **2026-08-14**.

## 1. Зачем это нужно

CoA Ascension Logs, CoA Armory, BisBeard и связанные frontend/API contracts не являются статичными источниками. Со временем могут появляться новые боссы, рейды, фазы, сложности, поля API, query parameters, классы/спеки, предметы, таланты и новые типы логов. Старые routes могут менять форму или исчезать.

Поэтому проект не должен быть набором одноразовых collectors, заточенных под сегодняшнюю версию сайта.

Целевая модель — **универсальная source observability platform**:

```text
обнаружить источники и network contracts
-> зарегистрировать contract/version
-> забрать immutable raw data
-> fingerprint schema/content
-> сравнить с предыдущим состоянием
-> зарегистрировать change event
-> определить зависимые datasets/analyses
-> пометить устаревшее
-> переобработать только затронутый scope
-> сохранить новый результат с provenance
```

## 2. Discovery-first: сначала network, потом frontend internals

Для web-источников первичный путь обнаружения — фактические сетевые запросы браузера/приложения.

Приоритет:

```text
1. browser/network capture: URL, method, params, headers shape, status, response
2. повторяемый direct request contract
3. frontend SPA/static asset analysis — только когда нужно понять формирование запроса или найти скрытые contracts
4. ручное предположение — запрещено как основание для production collection
```

Static JavaScript analysis остаётся полезным инструментом discovery/review, но не является первым выбором, если реальный network request уже наблюдаем.

## 3. Universal Source Registry

Каждый источник/endpoint регистрируется как версия контракта, а не как вечная константа.

Минимальные сущности:

### `source_endpoint`

Стабильная логическая сущность источника:

```text
source_system
logical_name
route_template
method
first_seen_at
last_seen_at
active_state
```

### `source_contract_version`

Версия наблюдаемого request contract:

```text
endpoint_id
contract_version
observed_at
request_parameter_keys
request_body_shape
required/optional parameter evidence
auth/session requirement evidence
source of discovery
contract fingerprint
confidence / review state
```

Новая версия создаётся при изменении формы запроса; старая не переписывается.

## 4. Immutable Capture Ledger

Каждый network response сохраняется как immutable observation.

Для capture фиксируются:

```text
endpoint/contract version
request fingerprint
observed_at
HTTP status
response content type
payload SHA-256
schema fingerprint
transport metadata needed for provenance
```

Raw payload хранится content-addressed. Одинаковый payload не нужно физически дублировать; retrieval observations могут ссылаться на один payload hash.

Главный принцип:

```text
новые данные добавляются
старые данные не переписываются
```

Это позволяет воспроизводить анализ «как мы знали на дату X» и переанализировать старые raw данные новым кодом.

## 5. Schema and dimension observation

Для JSON/structured responses автоматически вычисляются:

- structural/schema fingerprint;
- набор полей и типов;
- optional/nullability observations;
- container shapes;
- наблюдаемые dimension values там, где они безопасно классифицированы как domain metadata.

Отдельно отслеживаются domain dimensions, например:

```text
raid/location
boss/encounter
phase
realm
bracket
raid size
difficulty
class/spec/role
item/talent/build identifiers
```

Добавление нового босса или фазы должно регистрироваться как изменение источника, а не требовать ручной правки по всему проекту.

## 6. Change Registry

Сравнение нового observation с последним совместимым состоянием создаёт `source_change_event`.

Типичные события:

```text
endpoint_added
endpoint_removed_or_not_seen
request_contract_changed
schema_changed
field_added
field_removed
field_type_changed
new_dimension_value
boss_added
phase_added
location_added
new_report_observed
mapping_no_longer_matches
frontend_asset_changed
```

Change event содержит:

```text
what changed
where
first observed at
previous fingerprint
new fingerprint
severity
confidence
affected source/contract
```

Не каждое изменение является поломкой. Например новый report — обычное incremental событие; исчезновение обязательного поля — потенциальный breaking change.

## 7. Provenance and dependency graph

Каждый derived artifact/analysis должен объявлять зависимости:

```text
raw captures
contract versions
schema versions
mapping/extractor versions
normalization rules
analysis/model version
```

Пример:

```text
player encounter profile
  depends on report captures
  + encounter mapping v3
  + actor identity rules v2
  + performance analysis v5
```

Если изменился только новый report corpus, переанализируются новые/затронутые reports. Если изменилась mapping semantics, инвалидируется весь derived scope, который использовал эту mapping version.

## 8. Reanalysis Registry

Change events создают не немедленный глобальный rebuild, а `reanalysis_request` с вычисленным scope.

Примеры:

```text
new report
-> ingest + analyze only new report

new boss
-> register encounter
-> collect applicable corpus
-> build boss-specific models

new API field
-> archive immediately
-> review semantics
-> reprocess only mappings that opt into this field after approval

mapping changed
-> re-normalize all raw captures bound to old mapping

meta/build interpretation changed
-> recompute affected build/meta analyses while preserving historical source observations
```

Reanalysis request должен иметь причину, dependency cause, target scope, analysis version и status.

## 9. Time-aware analysis

«Последняя мета» не должна автоматически переписывать прошлое.

Необходимо различать:

```text
source observed_at
combat/report occurred_at
build observed_at
mapping effective version
analysis run time
```

Исторический рейд анализируется на основании доступных для того периода build/log evidence. Отдельно может быть запрошен современный counterfactual reanalysis: «как бы мы оценили тот состав по сегодняшней модели».

Оба результата могут сосуществовать и должны иметь явную provenance/version boundary.

## 10. Automatic operating loop

Целевой автоматический цикл:

```text
DISCOVER
  browser/network manifests + known endpoints + reviewed frontend assets

CAPTURE
  bounded collectors -> immutable raw archive

OBSERVE
  request/content/schema/dimension fingerprints

DIFF
  compare against last observed compatible state

REGISTER
  source_change_event

INVALIDATE
  dependency graph -> affected derived artifacts

REANALYZE
  incremental jobs for exact affected scope

REPORT
  change timeline + stale/fresh state + analysis deltas
```

## 11. Change dashboard / operator view

В localhost UI нужен раздел наподобие **Source & Analysis Health**:

- что изменилось на источниках;
- какие новые боссы/reports/fields появились;
- какие collectors/contracts сейчас active;
- какие mappings стали подозрительными;
- какие analyses устарели;
- какие reanalysis jobs ожидают/выполняются/завершены;
- чем новый результат отличается от предыдущего;
- какие изменения требуют ручного semantic review.

Цель — чтобы РЛ/разработчик видел не «сломался скрипт», а конкретно:

> Источник изменился вот здесь; затронуты такие данные; эти результаты уже пересчитаны; эти требуют review.

## 12. Safety and trust

Automatic discovery/capture не означает automatic semantic trust.

Разрешено автоматически:

- обнаруживать contracts;
- сохранять raw responses;
- fingerprint/diff;
- регистрировать новые dimension values;
- создавать reanalysis requests;
- переобрабатывать уже approved deterministic transformations.

Нельзя автоматически без review:

- считать новое поле доказанной mechanic semantics;
- повышать trust state;
- включать новое evidence в canonical planner scoring;
- интерпретировать неизвестный API field по имени;
- выполнять неизвестный/изменившийся write/network contract.

## 13. Implementation phases

### Phase A — Source Observatory foundation

Добавить DuckDB entities/migrations для:

```text
source_endpoint
source_contract_version
source_capture
source_schema_snapshot
source_change_event
artifact_dependency
analysis_run
reanalysis_request
```

Переиспользовать существующий immutable raw archive и retrieval observations.

### Phase B — generic JSON capture/diff

- generic reviewed GET collector;
- request fingerprint;
- JSON schema fingerprint;
- contract/schema diff;
- dimension discovery;
- change event generation.

### Phase C — incremental reanalysis

- dependency registration;
- stale/fresh state;
- scoped reanalysis queue;
- deterministic replay from raw archive.

### Phase D — source health UI

- source timeline;
- contract/schema versions;
- new bosses/reports/dimensions;
- stale analyses;
- reanalysis controls/results.

### Phase E — continuous source coverage

Apply the same framework to:

```text
CoA Ascension Logs reports/encounters/rankings/statistics/characters/guild/progression
CoA Armory/talent-grid
CoA BisBeard
future discovered CoA sources
```

## 14. Immediate consequence for current E3 work

Current progression discovery becomes the first real use case of this architecture:

```text
observed GET /api/guilds/progression/rankings
-> bounded capture
-> immutable raw archive
-> schema fingerprint
-> register contract/schema snapshot
-> detect future changes automatically
```

Do not build a one-off progression-only collector that bypasses the generic registry/change/reanalysis layer unless needed as a temporary bootstrap adapter.
