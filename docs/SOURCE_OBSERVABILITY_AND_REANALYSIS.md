# Source observability, change registry and reanalysis

Дата актуализации: **2026-08-27**.

## 1. Назначение

Источники CoA меняются: появляются новые фазы, боссы, поля, response shapes и routes. Поэтому проект рассматривает source state как временно наблюдаемое состояние, а не вечную схему.

Целевая модель:

```text
strongest available source
-> reviewed contract
-> immutable raw capture
-> acquisition observation
-> schema/profile/dimension observation
-> diff
-> source_change_event
-> dependency lookup
-> scoped reanalysis_request
-> deterministic replay
-> Source & Analysis Health
```

## 2. Source priority before discovery tooling

Старая формулировка “browser/network first” больше не является текущей парадигмой.

Для Ascension Logs используем:

```text
1. official documented public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API evidence
5. narrow browser/network observation for exact undocumented gaps
6. structural inference last
```

Source Observatory не диктует источник. Он принимает наблюдение после того, как выбран наиболее сильный доступный evidence provider.

Browser/HAR остаётся generic fallback, а не обязательным первым этапом.

## 3. Source registry and reviewed contracts

`source_endpoint` — стабильная логическая сущность endpoint-а.

`source_contract_version` — immutable/versioned representation reviewed request contract:

```text
source_code
endpoint_code
method
route_template
parameter key names
auth state
discovery source
review state
contract fingerprint
first/last seen
```

Contract values and credentials are not public evidence.

## 4. Immutable RawArchive

Каждый успешный raw response сохраняется content-addressed. Content object и fetch observation разделены.

Capture provenance включает:

```text
source/endpoint
request key
observed_at
HTTP status
content type
payload hash
schema fingerprint
sanitized request URL
private observation metadata where required
```

Raw payloads остаются локальными. Новый observation добавляется, старый не переписывается.

## 5. Request scope and schema profiles

Schema diff имеет смысл только внутри совместимого request scope.

Для endpoint-ов, где response shape зависит от query values, registry может объявить:

```text
schema_profile_keys
```

`observation_profile_key()` вычисляет локальный private hash только по значениям этих reviewed keys. Этот hash не публикуется, потому что low-entropy query values могут быть угадываемыми.

Пример: official `/statistics` partitioned by documented request-shaping dimensions:

```text
phase
difficulty
metric
bracket
location
bossId
damageMode
role
class
spec
weekNumber
realm
```

Так schema current-phase DPS request не сравнивается напрямую с healing/boss/week/filter request.

## 6. Schema and dimension observation

Для JSON автоматически наблюдаются:

```text
root type
normalized JSON paths
observed types
schema fingerprint
reviewed dimension value sets
scan truncation
```

Наблюдаемое значение dimension не является автоматически gameplay semantics.

## 7. Change registry

`source_change_event` создаётся для structural/contract changes, например:

```text
endpoint_added
request_contract_changed
observation_profile_added
field_added
field_removed
field_type_changed
root_type_changed
new_dimension_value
```

Change event хранит cause/severity/confidence/provenance. Не каждое open event является проблемой.

Например, первая регистрация endpoint-а создаёт informational `endpoint_added`. Dedicated health review может считать его baseline information, а warning/error changes — actionable.

## 8. Artifact dependency graph

Derived artifact должен объявлять зависимости на source evidence.

Для official aggregate statistics используются две complementary dependencies:

```text
raw_object
  -> exact payload provenance

source_endpoint = public_api_statistics
  -> logical source-change/reanalysis dependency
```

Raw dependency отвечает на вопрос “из какого exact capture получен результат”. Endpoint dependency отвечает на вопрос “какой логический source contract может сделать этот artifact stale при будущем изменении”.

Dependency version хранит normalizer/analysis boundary.

## 9. Reanalysis registry

Change events не должны запускать глобальный rebuild.

Схема:

```text
source_change_event
-> active source_endpoint dependencies
-> exact affected artifact(s)
-> deduplicated reanalysis_request
-> target scope
-> requested analysis version
```

`reanalysis_request` имеет reason event, dependency, artifact, requested analysis version, target scope и status.

Automatic reanalysis разрешён только для уже reviewed deterministic transformation. Новое неизвестное поле не становится автоматически trusted mechanic input.

## 10. Analysis runs

`analysis_run` фиксирует:

```text
analysis_type
analysis_version
artifact_type/artifact_key
target_scope
input fingerprint
output fingerprint
status
started/finished time
metadata
```

Official public statistics используют:

```text
analysis_type = official_public_api_population_statistics
artifact_type = public_api_population_statistics
```

## 11. Source & Analysis Health

Generic `build_source_health()` показывает:

```text
registered endpoints
capture counts
latest acquisition outcome
latest schema observation
open change counts
pending reanalysis count
active dependency count
completed analysis runs
recent changes
recent analyses
```

Domain-specific reviews may apply stricter or more useful gates while preserving generic provenance. Official aggregate statistics health separately distinguishes informational baseline events from actionable source changes and emits only scalar-safe counts/booleans.

## 12. Current official `/statistics` application

The aggregate pipeline is now:

```text
official OpenAPI contract
-> bounded provenance-aware /statistics capture
-> immutable RawArchive
-> exact StatisticsResponse normalization
-> DuckDB batch/class/spec persistence
-> population-prior read model
-> analysis_run
-> raw_object dependency
-> source_endpoint dependency
-> archived-response replay into Source Observatory
-> Source & Analysis Health
```

Real data already proves capture, normalization, persistence and second-pass idempotence. The current real gate is Source Observatory/Health replay of that **existing** archived response; no additional network request is required.

## 13. Automatic operating loop

```text
SELECT SOURCE
  strongest source by canonical priority

CAPTURE/IMPORT
  reviewed bounded acquisition -> immutable RawArchive

OBSERVE
  acquisition + compatible schema profile + dimensions

DIFF
  compare only against compatible source/profile history

REGISTER
  source_change_event

INVALIDATE
  dependency graph -> exact affected artifacts

REANALYZE
  approved deterministic transformations only

REPORT
  Source & Analysis Health + reviewed public-safe receipt
```

## 14. Safety and trust

Разрешено автоматически:

```text
archive raw observations
schema/profile fingerprinting
structural diff
register change events
register dependencies
queue scoped reanalysis
replay already approved deterministic transformations
```

Нельзя автоматически:

```text
field name -> mechanic meaning
new API field -> planner feature
population metric -> roster score
character name -> identity
unknown changed source -> trusted semantics
```

## 15. Coverage model

The same platform is reusable for:

```text
official aggregate API
first-party report endpoints
future documented CoA APIs
CoA Armory/talent sources when reviewed
pinned source-derived structures
browser/HAR fallback observations
```

Current priority is not “cover everything continuously”. It is to integrate each useful source family with explicit contract/profile/dependency boundaries before it becomes planner input.
