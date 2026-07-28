# PROMPT продолжения работы над CoA Raid Intelligence

Используй этот документ как стартовый контекст для нового ChatGPT/Codex-чата. Не доверяй ему вместо проверки репозитория: сначала сверяй branch, HEAD, PR, CI, код и документацию.

---

Ты продолжаешь разработку проекта **CoA Raid Intelligence Workbench**.

## 1. Репозиторий и рабочий контур

Репозиторий:

```text
GunsPojoshe/coa-raid-intelligence-workbench
```

Актуальная структура веток на момент handoff:

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #8 с safe HAR inventory уже слит в PR #7.

Локальная машина пользователя:

```text
Windows 11
PowerShell
C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
Python 3.12.13
uv
GitHub CLI установлен и авторизован как GunsPojoshe
```

Пользователь предпочитает:

- максимально автономную работу через GitHub;
- один PowerShell-блок за раз;
- полный код без обрывов;
- прямые ответы без лишних вступлений;
- не просить ручные действия, которые можно выполнить через GitHub/код;
- не загружать и не коммитить sensitive raw data.

Перед любыми изменениями:

1. проверить текущую ветку, HEAD и рабочее дерево;
2. проверить PR #7 и его base;
3. прочитать `README.md`, `AGENTS.md`, `docs/PROJECT_STATE.md`, релевантные ADR и capture docs;
4. сверить документированные утверждения с реальным кодом;
5. проверить последние CI runs;
6. не считать старые commit/test counts достоверными без проверки.

## 2. Миссия проекта

Создать localhost-first браузерное приложение для подготовки и интеллектуального анализа рейдовых составов Classless / Ascension WoW.

Главный источник наблюдений:

```text
https://coa.ascensionlogs.gg
```

Канонический evidence pipeline:

```text
immutable raw observation
→ SHA-256 + schema fingerprint
→ explicitly verified mapping
→ canonical normalized events
→ Aura State Engine / other deterministic reconstruction
→ mechanic hypothesis
→ supporting and contradicting evidence
→ corroborated / confirmed mechanic
→ planner scoring and recommendations
```

Событие combat log — наблюдение, а не автоматическое доказательство общей механики.

## 3. Жёсткие правила доверия

Нельзя придумывать:

- API routes;
- query parameters;
- JSON fields;
- pagination behavior;
- event types;
- Spell IDs;
- class/spec/provider mappings;
- игровую семантику по одному имени маршрута.

Нормализация разрешена только если:

- payload сохранён неизменяемо;
- вычислен schema fingerprint;
- mapping просмотрен человеком;
- mapping имеет status `verified`;
- fingerprint mapping совпадает с payload.

Только mechanics со статусом:

```text
corroborated
confirmed
```

могут участвовать в canonical planner scoring.

Не смешивать provenance:

```text
raw_log
upstream_derived
companion_addon
local_inference
manual_override
```

Всегда сохранять contradicting evidence. Не удалять его ради предпочтительной гипотезы.

Отделять глобальную механику игры от качества исполнения конкретного игрока/гильдии.

## 4. Privacy и raw data

Никогда не коммитить и не отправлять в GitHub/чат:

- HAR;
- raw payloads;
- DuckDB;
- cookies;
- Authorization headers;
- access tokens;
- browser profiles;
- query values с приватными данными;
- локальные абсолютные пути с username.

Допустимые локальные пути:

```text
data/exchange/in
data/exchange/out
data/raw
data/warehouse
```

Они должны оставаться gitignored.

Cookies допустимы только в памяти процесса. В outputs сохранять максимум profile version и header names, но не значения cookies/secret headers.

## 5. Уже реализованный фундамент

- FastAPI localhost app;
- browser raid constructor FLEX / 10 / 25 / 40;
- планирование до 40 слотов;
- Python domain logic;
- DuckDB persistence;
- immutable raw archive;
- observation отдельно от deduplicated payload body;
- source registry;
- safe route probe;
- JSON/HAR import;
- deterministic safe HAR inventory;
- archived gzip JSON inspection;
- schema fingerprinting;
- versioned verified normalization mappings;
- canonical report/encounter/actor/participant/aura events;
- rejects;
- Aura State Engine;
- hypotheses and evidence links;
- recency/cohort weighting;
- migrations `0001`–`0006`;
- `scripts/verify_repo.py`;
- Ubuntu + Windows CI;
- SPA HTML/JS asset capture;
- route extraction from frontend bundle;
- Armory API collector;
- Armory HAR importer;
- HTTP access diagnostic workflow.

## 6. Реальный aura checkpoint

Подтверждены два технических пути для spell `968746` (`Ninja's Focus`) в report `2987`.

### Encounter 64795

- full timeline;
- schema fingerprint:
  `2994424cb95c2a7e1997651226b7942367ebe77003e0f4614aae5da4920f8b98`;
- mapping `coa-aura-timeline-single-encounter-v1`, verified;
- 6 canonical events;
- 3 reconstructed intervals;
- exact match с 3 `debuff_sources` intervals;
- 0 rejects;
- 0 anomalies.

### Encounter 64796

- window `10382–38265 ms`;
- full duration `117215 ms`;
- schema fingerprint:
  `d8b6dd869d6adf8f3433f9e285b8270cd1aa8d640839c915a42c80b2211cbf0b`;
- baseline active target восстановлен через synthetic `window_start` event;
- missing remove внутри окна закрыт через `window_end`;
- 3 canonical events;
- 2 reconstructed intervals;
- exact match с 2 `debuff_sources` intervals;
- 0 rejects;
- 0 anomalies.

Это corroborates **normalizer/Aura State Engine behavior**, но не игровую механику эффекта.

Не подтверждено:

- заявленное `+8% AP`;
- обязательность эффекта;
- stacking;
- overwrite;
- coexistence;
- provider equivalence;
- criticality;
- ранее замеченный mismatch для `Demonfire Pact`.

## 7. Реальный HAR inventory

Последний зафиксированный inventory:

```text
1367 total entries
525 archived bodies
124 JSON objects
498 unique payloads
59 schema fingerprints
```

Подтверждены route/payload candidates для:

- roster;
- buff_uptimes;
- casts;
- aura_detail;
- aura_timeline;
- debuff_sources.

Inventory не содержит header values, cookies, Authorization, body requests или query values.

## 8. Character/Armory discovery

Обе страницы:

```text
/characters/Gunspojoshe/Vol%27Jin?...
/armory/Gunspojoshe/Vol%27Jin
```

возвращают одинаковый SPA shell:

```text
3753 bytes
SHA-256 d70233f7776710b49cd7b2d45f7f4723c94c7abb58f0c2f3a50dbf73b30fc69c
embedded JSON: none
```

Frontend asset:

```text
/assets/index-DTWqLUGT.js
2664204 bytes
SHA-256 fded83a80c020a5dc5e079032c671dc8ef7706bb5a4b49417cce5c98283a9c15
```

Подтверждённые маршруты из bundle:

```text
GET /api/characters/search?q=<value>&limit=<value>
GET /api/armory/by-name/{character}?realm=<value>
GET /api/armory/character/{id}
GET /api/armory/character/{id}/captures?limit=100
GET /api/armory/talent-grid/{class-slug}
```

Armory в клиенте описан как captured character builds: gear, mystic enchants и talents из raid captures.

## 9. Важное открытие по 403

Первоначальный collector использовал обычный `urllib` profile и получал:

```text
/api/armory/by-name/... -> 403
/api/characters/search -> 403
```

Оба 56-byte response имели hash:

```text
0f088f03f69d7a8e6d34d206b87db3cd50364a9dea31e21e229d0089bd4d66b7
```

Это сначала ошибочно выглядело как auth/browser-only restriction.

GitHub Actions access matrix проверила три маршрута:

```text
/api/reports/public
/api/characters/search
/api/armory/by-name/...
```

Результат:

```text
plain headers                -> 403
browser-like headers         -> 403
full fetch-context profile   -> 200
fetch-context after HTML     -> 200
```

Успешный профиль:

```text
Accept: application/json, text/plain, */*
Accept-Language: en-US,en;q=0.9
Cache-Control: no-cache
Pragma: no-cache
User-Agent: Chromium-like
Referer: https://coa.ascensionlogs.gg/
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
```

Успешные response shapes:

```text
reports_public: pagination, reports, success
character_search: characters, success
armory_by_name: character, has_armory, latest_capture, success
```

Критическое ограничение интерпретации:

- full profile проверен;
- не доказано, какой отдельный header минимально необходим;
- diagnostics вызывала `reports_public` первым;
- после первого успешного response cookie jar содержал одну cookie;
- не изолировано, проходит ли Armory первым запросом в fresh session;
- не утверждать, что cookie не нужна;
- не утверждать, что виноват Cloudflare/TLS fingerprint после успешного urllib fetch-context run.

## 10. Текущее состояние Armory collector

Файлы:

```text
src/coa_workbench/collector/armory_api_capture.py
scripts/capture_character_build.py
scripts/import_armory_har.py
scripts/diagnose_armory_access.py
.github/workflows/diagnose-armory-access.yml
```

Collector умеет:

- by-name request;
- character-search fallback;
- exact name+realm resolution;
- detail request;
- captures request;
- talent-grid request;
- raw archive before interpretation;
- safe sanitized output.

Но основной collector ещё не переведён на проверенный fetch-context profile, поэтому локальный v7 остановился на `403`.

Недостающие tests:

- full Armory chain;
- `has_armory=false`;
- invalid JSON with preserved raw capture;
- exact name+realm matching;
- captures limit validation;
- cookie/header-name safety;
- latest verified archived asset selection under same request key.

Последний diagnostic workflow теперь должен сохранять full JSON artifact:

```text
artifacts/armory-access-diagnostic.json
artifact name: armory-access-diagnostic
```

и печатать только compact summary.

## 11. Автоматическое получение репортов

Проект должен автоматизировать discovery и download, а не требовать ручного скачивания каждого полного лога.

Целевой процесс:

```text
/api/reports/public
→ phase/location/difficulty/category filters
→ до 5 suitable reports per category
→ encounters for each report
→ select boss encounters
→ download only required analytical endpoints
→ immutable raw archive
→ fingerprint
→ endpoint-specific parser
→ canonical normalization
```

Много однотипных файлов — нормально.

Правило parser-а:

```text
one reviewed parser per endpoint/schema version
not one parser per file
```

Unknown fingerprint:

```text
reject + review queue
never guess
```

Предпочтительные payloads:

- report metadata;
- encounters;
- roster/combatants;
- aura timeline/detail/uptimes;
- casts;
- debuff sources;
- deaths/damage/healing только по конкретной гипотезе.

Full event stream скачивать только если специализированные endpoints не позволяют проверить temporal/causal hypothesis.

## 12. Следующий bounded slice

Выполняй в таком порядке.

### Шаг 1. HTTP profile

Создай общий versioned модуль, например:

```text
coa-fetch-context-v1
```

Требования:

- один persistent cookie jar/opener на same-host chain;
- exact verified header profile;
- никаких cookie/header values в metadata;
- metadata сохраняет profile version и header names;
- redirects и HTTP errors архивируются так же, как сейчас;
- не делать browser impersonation beyond observed same-origin request headers.

### Шаг 2. Изоляционная диагностика

Проверить отдельно:

```text
fresh session -> armory_by_name first
fresh session -> character_search first
fresh session -> reports_public first -> armory
fresh session -> individual/minimal header subsets
```

Цель — понять необходимость порядка/cookie и минимальный профиль. Не блокировать основной collector, если полный профиль уже стабильно воспроизводим.

### Шаг 3. Tests

Добавить unit tests для HTTP profile и Armory chain. Использовать fake opener/responses, не сеть.

### Шаг 4. Real Armory capture

Повторить:

```text
Gunspojoshe
realm Vol'Jin
spec Tyrant
phase 0
location World Bosses
difficulty normal
```

Проверить:

- `character_id`;
- `character_class`;
- `has_armory`;
- by_name/search/detail/captures/talent_grid statuses;
- payload hashes;
- schema fingerprints;
- no secrets in output.

### Шаг 5. Safe inspection

Для real detail/captures/talent-grid payloads:

- inventory top-level structures;
- collection paths;
- counts;
- types;
- fingerprints;
- no semantic mappings until review.

### Шаг 6. Report discovery

Реализовать versioned discovery:

- pagination;
- filters verified from real frontend/payload;
- configurable `reports_per_category`, default 5;
- deterministic selection policy;
- immutable provenance;
- rate-limit awareness;
- retries/backoff only for retryable failures;
- no duplicate payload storage.

### Шаг 7. Full canonical slice

Нормализовать:

```text
report
encounter
actors
participants/roster
aura events
```

Связать source pointers и provenance.

### Шаг 8. Evidence expansion

- другие spells;
- другие reports;
- supporting observations;
- contradicting observations;
- stacking/overwrite/coexistence только после достаточных данных;
- provider criticality только после description + prevalence + scarcity evidence.

### Шаг 9. Verification

Запустить:

```text
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Проверить PR #7 CI Ubuntu/Windows. Не заявлять test success без фактического запуска.

## 13. Критерии полного evidence checkpoint

PR #3 остаётся Draft до выполнения всего:

1. real immutable payload;
2. schema fingerprint;
3. verified mapping;
4. normalized real report/encounter;
5. linked actors/participants/aura events;
6. reconstructed aura intervals;
7. repeatable mechanic with independent supporting observations;
8. contradicting evidence review;
9. reproducible output with dataset/mapping/policy/inference versions and provenance.

## 14. Отброшенные или устаревшие выводы

Не повторять как факт:

- «Armory API требует авторизацию» — не подтверждено;
- «нужен обязательный browser/Playwright/HAR» — опровергнуто успешным urllib fetch-context profile;
- «проблема только в Cloudflare/TLS fingerprint» — не подтверждено;
- «browser-like User-Agent достаточно» — опровергнуто, он всё ещё дал 403;
- «HTML bootstrap обязателен» — не подтверждено, fetch-context без HTML дал 200;
- «cookie точно не нужна» — не доказано из-за порядка endpoints в matrix;
- «Ninja's Focus даёт +8% AP по combat logs» — не подтверждено;
- «verified normalizer mapping подтверждает mechanic» — неверно;
- «полный event stream надо скачивать всегда» — неверно;
- «нужен отдельный parser для каждого файла» — неверно.

## 15. Формат отчёта после каждой задачи

Всегда сообщай:

- что проверено фактически;
- какое прежнее утверждение оказалось ложным/неполным;
- какие файлы изменены;
- какие migrations добавлены;
- какие команды реально выполнены;
- точные test results;
- что осталось непроверенным;
- следующий bounded task.

Не называй scaffolding подтверждённым игровым знанием.

---

## Стартовая команда новому агенту

Начни с проверки фактического состояния ветки `e3/real-log-capture`, PR #7 и последних CI runs. Затем прочитай `README.md`, `AGENTS.md`, `docs/PROJECT_STATE.md` и этот документ. Первой кодовой задачей сделай централизованный versioned fetch-context HTTP profile с persistent cookie jar, безопасной metadata и unit tests. После этого повтори real Armory capture и зафиксируй immutable detail/captures/talent-grid payloads без создания speculative mappings.
