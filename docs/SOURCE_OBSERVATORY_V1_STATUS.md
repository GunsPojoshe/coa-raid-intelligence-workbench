# Source Observatory v1 — implementation checkpoint

Дата актуализации: **2026-08-14**.

## 1. Базовый вертикальный срез

Source Observatory строится поверх существующего immutable `RawArchive` и DuckDB persistence.

```text
reviewed source contract
-> acquisition observation
-> immutable raw capture
-> schema snapshot when the response is JSON
-> source change event
-> dependency lookup
-> scoped reanalysis request
```

Persistence:

```text
source_contract_version
source_capture
source_schema_snapshot
source_change_event
artifact_dependency
analysis_run
reanalysis_request
source_acquisition_observation
```

Blocked/non-JSON responses остаются acquisition evidence и не превращаются в ложную schema evidence.

## 2. Network-first discovery

Основной discovery path теперь начинается с реального browser Network/HAR, а не с внутреннего устройства SPA.

Добавлен generic scalar-free HAR inventory:

```text
browser HAR
-> same-origin API Fetch/XHR selection
-> route shape normalization
-> query key inventory without values
-> status/content-family inventory
-> JSON structure fingerprint
-> sanitized network candidate inventory
```

Команда:

```powershell
uv run --no-sync python scripts/inventory_network_har.py <capture.har>
```

Inventory не сохраняет query values, headers, cookies, response bodies или response scalar values. Он предназначен для обнаружения новых/изменившихся источников, после чего конкретный контракт проходит review и только затем становится capture-ready.

## 3. Фактический progression network path

Очищенный browser HAR страницы `/guilds/progression` от 2026-08-14 показал текущий runtime path:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=<value>&difficulty=<value>
```

Оба ответа были `200 application/json`.

Для текущего phase-progression response наблюдались структурные области:

```text
phase
board
enabled
totalBosses
bossesCollapsed
bossList
perBossRankings
guilds
```

Наблюдалось 12 boss rows, 12 per-boss ranking groups и 16 guild progression rows. Эти значения являются timestamped observation, а не вечной конфигурацией.

Current SPA дополнительно показывает, что helper `phase-progression` всегда передаёт `phase` и условно добавляет `board` и `difficulty`. В registry разрешены эти три query keys, но автоматический capture не должен придумывать значения.

Canonical public receipt:

```text
evidence/real-data/coa-guild-phase-progression-browser-network.json
```

Raw HAR, user/session data, guild IDs/names, report IDs and raw response bodies не versioned.

## 4. Отношение к `/guilds/progression/rankings`

Rankings contracts остаются в текущем SPA и поэтому не удаляются как несуществующие. Но конкретный browser capture текущей страницы `/guilds/progression` их не вызвал.

Следовательно:

```text
rankings route = alternate reviewed contract
phase-progression route = actually exercised current-page contract
```

Первый direct rankings GET ранее получил managed-edge `403`; это acquisition-mode observation, а не доказательство отсутствия route.

## 5. Source registry

Добавлены reviewed Observatory routes:

```text
phases_api
guild_phase_progression_api
```

`guild_phase_progression_api` отслеживает только полезные низкокардинальные dimensions:

```text
phase
board
bossId
difficulty
location
```

Guild/report/encounter identifiers не используются как automatic change dimensions.

## 6. Следующий вертикальный срез

```text
import observed /api/phases and /api/guilds/phase-progression from browser HAR
-> establish local schema/dimension baseline
-> repeat browser/network acquisition on a later run
-> automatically detect new phase/boss/location/schema values
-> connect resulting events to reanalysis dependencies
-> then generalize the same process to reports, encounters, statistics, characters, Armory/talent-grid and BisBeard
```

Pagination/termination/completeness для progression пока не объявляются verified: текущий phase-progression response выглядит агрегированным, но одного capture недостаточно для доказательства полной семантики.
