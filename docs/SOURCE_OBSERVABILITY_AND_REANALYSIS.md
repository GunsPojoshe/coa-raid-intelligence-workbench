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

Official `/statistics` partitioned by documented request-shaping dimensions:

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

Так один aggregate profile не сравнивается напрямую с healing/boss/week/filter profile другого request scope.

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

Для current official aggregate statistics используются:

```text
raw_object
  -> exact payload provenance

source_endpoint_profile
  -> private reviewed query-profile source-change/reanalysis dependency
```

Raw dependency отвечает на вопрос “из какого exact capture получен результат”. Profile dependency отвечает на вопрос “какой совместимый private request profile может сделать этот artifact stale при будущем schema/profile-local изменении”.

Историческая broad dependency:

```text
source_endpoint = public_api_statistics
```

была допустима как первый integration step, но теперь деактивируется для aggregate artifacts при replay через текущий persistence. Она больше не является active canonical aggregate dependency.

Dependency version хранит private profile fingerprint или другую reviewed version boundary в зависимости от dependency type. Private fingerprints не публикуются.

## 9. Profile-scoped reanalysis

`src/coa_workbench/collector/source_profile_reanalysis.py` реализует query-profile resolver.

Правила:

```text
schema/profile-local event
  -> match only source_endpoint_profile dependencies with same private observation_profile_key

request_contract_changed
  -> endpoint-global fan-out to all active profile dependencies

source event older than dependency registered_at
  -> cannot back-trigger that newer dependency
```

Resolver создаёт deduplicated `reanalysis_request` только для подходящих artifacts.

Public summary resolver-а содержит только counts/booleans. Query/profile values и profile fingerprints не публикуются.

## 10. Real aggregate profile migration proof

Локальный no-network replay уже доказал migration старого aggregate artifact:

```text
source_endpoint_profile dependency count: 1
legacy unscoped source_endpoint dependency count: 0
eligible old events: 0
profile matches: 0
global matches: 0
created reanalysis requests: 0
pending reanalysis requests: 0
actionable open source changes: 0
attention required: false
```

Это ожидаемое поведение: исторический informational baseline event был наблюдён до регистрации новой profile dependency и не должен задним числом инвалидировать artifact.

Scalar-safe receipt:

```text
evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json
```

## 11. Analysis runs

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

## 12. Source & Analysis Health

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

Real aggregate health is now proven with `attention_required=false` after profile dependency migration.

## 13. Current official `/statistics` application

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
-> source_endpoint_profile dependency
-> archived-response replay into Source Observatory
-> profile-scoped reanalysis resolver
-> Source & Analysis Health
```

Real data proves capture, normalization, persistence, second-pass idempotence, Source Observatory integration and profile-scoped dependency migration.

## 14. Bounded population coverage v1

The next use of the same architecture is a deliberately small multi-profile coverage set:

```text
required slices: 4
metric families represented: 3
role-qualified slices: 3
role-omitted slices: 1
broader dimensions: held stable
cartesian boss/location/week/realm/class/spec expansion: excluded
```

Workflow:

```text
review current-phase DuckDB coverage
-> reuse already persisted matching slices
-> network capture only missing slices
-> RawArchive
-> Source Observatory observation
-> exact normalization
-> deterministic persistence + second replay
-> profile-scoped reanalysis reconciliation
-> Source & Analysis Health
-> scalar-safe coverage receipt
```

The operator command is resumable and stops on the first incomplete capture:

```powershell
uv run --no-sync python scripts/capture_public_api_population_coverage.py
```

The goal is not “collect everything”. It is to prove a useful bounded population context while respecting API terms and the project's trust/privacy boundaries.

## 15. Automatic operating loop

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

## 16. Safety and trust

Разрешено автоматически:

```text
archive raw observations
schema/profile fingerprinting
structural diff
register change events
register dependencies
queue scoped reanalysis
replay already approved deterministic transformations
bounded missing-only aggregate capture
```

Нельзя автоматически:

```text
field name -> mechanic meaning
new API field -> planner feature
population metric -> roster score
character name -> identity
unknown changed source -> trusted semantics
bulk API crawl merely for completeness
```

## 17. Coverage model

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
