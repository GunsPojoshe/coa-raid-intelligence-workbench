# Source Observatory v1 — implementation checkpoint

Дата: **2026-08-14**.

## Реализованный вертикальный срез

Source Observatory v1 теперь строится поверх уже существующих `source_endpoint`, `raw_object` и `raw_fetch_observation`, а не создаёт второй параллельный raw-контур.

Добавлено:

```text
migration 0009
source_contract_version
source_capture
source_schema_snapshot
source_change_event
artifact_dependency
analysis_run
reanalysis_request
```

`source_endpoint` расширен source/logical/first-seen/last-seen metadata.

## Generic reviewed GET contract

`collector/source_observatory.py` вводит generic reviewed GET contract:

```text
reviewed/verified contract
-> validated HTTPS base + route template
-> only reviewed path/query keys
-> deterministic contract/request fingerprint
-> immutable RawArchive capture
-> JSON schema/path-type snapshot
-> configured dimension observation
-> diff against previous endpoint snapshot
-> source_change_event
-> dependency lookup
-> scoped reanalysis_request
```

Неизвестные query keys не разрешаются автоматически. Network capture entrypoint работает только с reviewed/verified GET contract; write methods в v1 не поддерживаются.

## Change semantics v1

Автоматически регистрируются наблюдаемые изменения:

```text
endpoint_added
request_contract_changed
schema_changed
field_added
field_removed
field_type_changed
new_dimension_value
```

`field_removed` не создаётся, если previous/current snapshot был bounded/truncated, чтобы частичный scan не выдавался за доказанное удаление поля.

Dimension values наблюдаются только для явно настроенных ключей; имя поля само по себе не превращается в domain semantics.

## Reanalysis

`artifact_dependency` связывает derived artifact/analysis с source endpoint. Для зарегистрированного source change создаётся deduplicated pending `reanalysis_request` точного зависимого artifact scope.

Это первая рабочая основа для цепочки:

```text
new source observation
-> change registry
-> affected dependency
-> pending reanalysis request
```

Сам reanalysis worker и stale/fresh UI ещё не реализованы.

## Testing boundary

Добавлены deterministic unit/integration tests для:

- reviewed URL construction and unknown parameter rejection;
- structural JSON diff;
- new dimension detection;
- truncated-scan safety;
- DuckDB migration 0009;
- immutable raw capture integration;
- first endpoint registration;
- no-change observation;
- schema/dimension change events;
- dependency-driven reanalysis queue.

Тесты не выполняют реальный network request. Exact-head CI является acceptance gate этого checkpoint.

## Next slice after green CI

```text
register progression/rankings as first Source Observatory contract
-> one bounded GET using observed empty params branch
-> immutable capture through generic observatory
-> inspect real response schema/dimensions
-> register exact change baseline
-> then determine pagination/termination semantics
```

После этого тот же adapter model расширяется на reports, encounters, statistics, characters, guild data, Armory/talent-grid и BisBeard без отдельной инфраструктуры для каждого источника.
