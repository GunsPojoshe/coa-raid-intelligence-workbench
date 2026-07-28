# Фактическое состояние проекта

Дата актуализации: 2026-07-28.

## Репозиторий

- Основная стабильная ветка: `main`.
- Родительская ветка evidence-refactor: `e2/log-evidence-refactor`.
- Активная ветка real-log capture: `e3/real-log-capture`.
- Активный Draft PR: №7, `e3/real-log-capture → e2/log-evidence-refactor`.
- Родительский Draft PR: №3, `e2/log-evidence-refactor → main`.
- PR №8 с безопасной HAR-инвентаризацией слит в PR №7.
- PR №4 с усилением Aura State Engine и PR №5 с verification runner слиты в `e2/log-evidence-refactor`.
- Проверки основного проекта выполняются на Ubuntu и Windows.
- GitHub CLI установлен на рабочем компьютере и авторизован как `GunsPojoshe`.

Не считать число commits, состояние CI и локальный HEAD из этого документа вечными. Перед изменением кода всегда проверять фактическую ветку, PR и remote.

## Реализованный фундамент

- localhost FastAPI-приложение и браузерный конструктор рейда;
- сохранение планов в DuckDB;
- неизменяемый raw archive с SHA-256;
- раздельные observation и дедуплицированные payload body;
- source registry и безопасный probe;
- импорт локального JSON и HAR;
- безопасная детерминированная HAR-инвентаризация;
- инспекция архивированного gzip JSON;
- schema inspection и fingerprint;
- verified normalization mappings;
- canonical report, encounter, actor, participant и aura events;
- normalization rejects;
- Aura State Engine с refresh, stacks, duplicate events, несколькими источниками и целями;
- различение полного encounter и ограниченного окна aura timeline;
- интервалы `active`, `closed`, `incomplete` с provenance metadata;
- причины границ `window_start`, `window_end`, `removed`, `encounter_end`;
- trust states, hypotheses, supporting/contradicting evidence и versioned weighting policy;
- миграции `0001`–`0006`;
- compatibility-исполнение опубликованной миграции `0005` без изменения checksum;
- единый `scripts/verify_repo.py`;
- CI-проверки Ubuntu и Windows;
- захват SPA HTML и связанных JavaScript assets;
- извлечение безопасных API route candidates из frontend bundle;
- первичный capture public Armory API responses;
- безопасный Armory HAR importer;
- GitHub Actions-диагностика HTTP access profile.

## Реальный evidence checkpoint: aura normalization

На локально сохранённых immutable payloads отчёта CoA Logs подтверждены два воспроизводимых single-encounter пути для spell `968746` (`Ninja's Focus`).

### Encounter 64795 — полный timeline

```text
report 2987
encounter 64795
aura_timeline -> canonical events -> Aura State Engine -> debuff_sources intervals
```

Проверенный результат:

- schema fingerprint: `2994424cb95c2a7e1997651226b7942367ebe77003e0f4614aae5da4920f8b98`;
- mapping: `coa-aura-timeline-single-encounter-v1`, status `verified`;
- `buff_applied -> APPLIED`;
- `buff_removed -> REMOVED`;
- одна пустая baseline-строка корректно исключена;
- 6 canonical aura events;
- 3 восстановленных интервала;
- 3 эталонных интервала `debuff_sources`;
- точное совпадение интервалов;
- 0 rejects;
- 0 anomalies;
- provenance сохраняет hash и archive path обоих payloads.

### Encounter 64796 — оконный timeline

```text
report 2987
encounter 64796
window 10382–38265 ms
full encounter duration 117215 ms
observed window duration 27883 ms
```

Проверенный результат:

- schema fingerprint: `d8b6dd869d6adf8f3433f9e285b8270cd1aa8d640839c915a42c80b2211cbf0b`;
- baseline в `10382` с `active_targets=1` восстановлен как начало интервала с причиной `window_start`;
- `buff_removed` в `14970` закрывает первый интервал;
- `buff_applied` в `29458` открывает второй интервал;
- отсутствие remove внутри окна закрывает второй интервал на `38265` с причиной `window_end`;
- 3 canonical aura events, включая synthetic boundary event;
- 2 восстановленных интервала;
- 2 эталонных интервала `debuff_sources`;
- точное совпадение интервалов;
- 0 rejects;
- 0 anomalies.

Оба наблюдения подтверждают reviewed mapping и реконструкцию полного и оконного single-encounter aura timeline. Это corroborating evidence технического поведения normalizer/Aura State Engine, но не игровой механики эффекта.

Не подтверждены combat-log evidence:

- числовое описание `Ninja's Focus`, включая заявленные `+8% AP`;
- обязательность эффекта;
- stacking, overwrite и coexistence;
- эквивалентность похожим эффектам;
- стратегическая критичность;
- mismatch, ранее замеченный для `Demonfire Pact`.

## Реальный HAR inventory

Локальный HAR остаётся gitignored и не должен передаваться в GitHub, issue, PR или чат.

Последний безопасный inventory:

- всего HAR entries: `1367`;
- архивировано response bodies: `525`;
- JSON objects: `124`;
- уникальных payloads: `498`;
- уникальных schema fingerprints: `59`;
- request/response header values, cookies, authorization и query values в inventory не включаются;
- non-HTTP/data URI redaction исправлен;
- подтверждены кандидаты roster, `buff_uptimes`, casts, `aura_detail`, `aura_timeline`, `debuff_sources`.

Любая семантика endpoint-а считается подтверждённой только после просмотра реального payload, а не только по route name.

## Character/Armory page discovery

Обе страницы:

```text
/characters/Gunspojoshe/Vol%27Jin?... 
/armory/Gunspojoshe/Vol%27Jin
```

возвращают один SPA shell:

- размер: `3753` bytes;
- payload SHA-256: `d70233f7776710b49cd7b2d45f7f4723c94c7abb58f0c2f3a50dbf73b30fc69c`;
- embedded JSON отсутствует.

Основной JavaScript asset:

- route: `/assets/index-DTWqLUGT.js`;
- размер: `2664204` bytes;
- payload SHA-256: `fded83a80c020a5dc5e079032c671dc8ef7706bb5a4b49417cce5c98283a9c15`.

Из frontend bundle подтверждены маршруты:

```text
GET /api/characters/search?q=<value>&limit=<value>
GET /api/armory/by-name/{character}?realm=<value>
GET /api/armory/character/{id}
GET /api/armory/character/{id}/captures?limit=100
GET /api/armory/talent-grid/{class-slug}
```

Frontend описывает Armory как просмотр captured character builds: gear, mystic enchants и talents из реальных raid captures. Это описание интерфейса, а не гарантия полноты каждого payload.

## Диагностика доступа к API

### Первоначальное наблюдение

`capture_character_build.py` с обычным `urllib`, `Accept: application/json` и собственным User-Agent получил:

```text
/api/armory/by-name/...  -> 403
/api/characters/search  -> 403
```

Оба ответа:

- размер: `56` bytes;
- payload SHA-256: `0f088f03f69d7a8e6d34d206b87db3cd50364a9dea31e21e229d0089bd4d66b7`;
- top-level keys: `error`, `message`.

Это не было доказательством обязательной авторизации или browser-only TLS. Требовалась матрица вариантов запроса.

### Проверенная GitHub Actions matrix

Контрольные endpoint-ы:

```text
/api/reports/public?page=1&limit=1&sortBy=created_at&sortOrder=desc
/api/characters/search?q=Gunspojoshe&limit=20
/api/armory/by-name/Gunspojoshe?realm=Vol%27Jin
```

Результаты:

```text
plain headers                 -> 403 для всех трёх endpoint-ов
browser headers               -> 403 для всех трёх endpoint-ов
fetch-context header profile  -> 200 для всех трёх endpoint-ов
fetch-context after HTML page -> 200 для всех трёх endpoint-ов
```

Успешный проверенный профиль `fetch-context`:

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

Проверенные `200` shapes:

- `reports_public_control`: `pagination`, `reports`, `success`;
- `character_search`: `characters`, `success`;
- `armory_by_name`: `character`, `has_armory`, `latest_capture`, `success`.

HTML bootstrap не требовался в успешной последовательности. Однако диагностика вызывала `reports_public_control` первым, после чего cookie jar содержал одну cookie. Поэтому пока не изолировано:

- проходит ли `armory_by_name` первым запросом в совершенно свежей сессии;
- какой отдельный header или их минимальное подмножество снимает `403`;
- нужна ли cookie, установленная первым успешным API response.

Не утверждать, что причиной был один конкретный header. Подтверждён только полный успешный профиль и последовательность.

GitHub Actions workflow теперь должен:

- сохранять полный JSON как `artifacts/armory-access-diagnostic.json`;
- выводить в log только компактную сводку;
- загружать artifact `armory-access-diagnostic`;
- загружать artifact даже при ненулевом exit code.

## Текущее состояние Armory collector

Реализовано:

- `src/coa_workbench/collector/armory_api_capture.py`;
- by-name capture;
- public character-search fallback;
- detail/captures/talent-grid chain после разрешения character ID;
- raw response archive до JSON interpretation;
- safe output без header values и cookies;
- `scripts/capture_character_build.py` объединяет page/asset и Armory API observations;
- `scripts/import_armory_har.py` остаётся fallback для browser-captured responses.

Текущий collector ещё использует недостаточный HTTP profile и поэтому локальный v7 capture остановился на `403`. Следующий кодовый шаг — централизовать проверенный fetch-context profile и persistent same-host cookie jar, затем повторить capture.

Не добавлены или не подтверждены:

- unit tests для нового `armory_api_capture.py`;
- отдельный regression test выбора latest verified archived JS asset при одинаковом request key;
- полный `verify_repo.py` после последних Armory/diagnostic изменений;
- реальный capture `armory/character/{id}`, `/captures` и `/talent-grid`;
- reviewed mappings для Armory payloads.

## Автоматизированное получение репортов

Целевой поток не должен требовать ручного скачивания каждого полного лога.

Предпочтительная архитектура:

```text
/api/reports/public
-> фильтрация по phase/location/difficulty/category
-> до 5 подходящих reports на категорию
-> список encounters каждого report
-> выбор нужных boss encounters
-> загрузка только необходимых analytical endpoints
-> immutable raw archive
-> schema inventory/fingerprint
-> endpoint-specific parser
-> canonical normalization
```

Приоритет специализированным payloads:

- report metadata;
- encounters;
- roster/combatants;
- aura timeline/detail/uptimes;
- casts;
- debuff sources;
- deaths/damage/healing только по конкретной аналитической задаче.

Полный event stream скачивать только когда агрегированные endpoint-ы не позволяют проверить временную или причинную гипотезу.

Много однотипных raw files ожидаемо. Нужен один versioned parser на schema/endpoint, а не parser на каждый файл. Неизвестный fingerprint отправляется в reject/review queue, а не угадывается.

## Канонические ограничения

- Статические historical mappings имеют статус `legacy_unverified`.
- Они не участвуют в canonical planner scoring.
- Непроверенный normalization mapping отклоняется.
- Только `corroborated` и `confirmed` mechanics могут использоваться для рекомендаций.
- Infrastructure evidence pipeline не является подтверждением игровых механик.
- Verified schema mapping не повышает trust state игровой механики автоматически.
- Corroborated normalizer behavior не считается corroborated mechanic behavior.
- Raw HAR, cookies, access tokens, authorization headers и private browser profiles не коммитятся.
- Cookies разрешены только в памяти процесса и не должны попадать в output metadata.

## Воспроизводимая проверка

```bash
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Verifier запускает Ruff, полный pytest, doctor, CLI smoke tests, trust gates и двукратную инициализацию временной DuckDB. Рабочая `data/warehouse/coa.duckdb` не используется. JSON-отчёт записывается в `artifacts/verification-report.json`.

Реальный aura checkpoint:

```bash
python scripts/validate_aura_capture.py \
  --timeline <timeline-payload-hash> \
  --reference <debuff-sources-payload-hash> \
  --encounter-id <encounter-id>
```

Последний полностью зафиксированный основной CI до Armory блока: GitHub Actions run №26, Ubuntu и Windows — success. Последние Armory/diagnostic изменения требуют нового полного verifier run; не заявлять их полностью проверенными до фактического прогона.

## Приоритетные следующие шаги

1. Вынести успешный HTTP profile в общий versioned модуль, например `coa-fetch-context-v1`.
2. Использовать один persistent cookie jar/opener на цепочку same-host API requests.
3. Не сохранять cookie/header values; сохранять только profile version и header names.
4. Добавить изоляционную диагностику порядка запросов:
   - fresh session -> `armory_by_name` first;
   - fresh session -> `character_search` first;
   - fresh session -> `reports_public` -> Armory;
   - минимальные подмножества `Referer`/`Sec-Fetch-*`.
5. Обновить `capture_armory_api` и повторить реальный capture Gunspojoshe/Vol'Jin.
6. Добавить unit tests full chain, `has_armory=false`, invalid JSON, exact name+realm matching, cookies/header names and limit validation.
7. Получить immutable payloads detail, captures и talent-grid; выполнить safe structural inventory без семантических догадок.
8. Создать reviewed mappings только после просмотра fingerprints и реальных shapes.
9. Реализовать report discovery по категориям и выбор до 5 reports на категорию.
10. Нормализовать полный report/encounter/roster с actors и participants.
11. Повторить aura validation на других spells/reports и искать contradicting observations.
12. Только после этого переходить к stacking/overwrite/coexistence и provider criticality.
13. Запустить `uv run python scripts/verify_repo.py` и проверить PR №7 CI на Ubuntu/Windows.
14. Удалить временную diagnostic workflow после переноса проверенного profile в тестируемый collector либо оставить её только с `workflow_dispatch`, если она нужна как воспроизводимый probe.

## Незавершённая контрольная точка

Выполнено частично:

1. реальные immutable payloads CoA Logs — выполнено локально;
2. verified mapping фактической single-encounter aura schema — выполнено;
3. нормализованные реальные encounter и aura events — выполнено для двух aura payloads;
4. восстановленные реальные aura intervals — выполнено для полного и оконного timeline;
5. независимое сравнение с `debuff_sources` intervals — выполнено для двух encounters;
6. повторяемость normalizer behavior на разных encounters и temporal shapes — выполнено;
7. безопасный source discovery и API access profile — выполнено для tested routes.

До полного evidence checkpoint остаются:

1. нормализация полного реального report/encounter/roster с actors и participants;
2. реальный immutable Armory detail/captures/talent-grid capture;
3. повторение aura-проверки на других spells/reports;
4. hypotheses stacking, overwrite и coexistence;
5. независимые supporting observations игровых механик;
6. проверенные contradicting observations;
7. criticality по описанию, распространённости и редкости providers;
8. canonical output, воспроизводимый по dataset, mapping, policy и inference versions.

До выполнения этих условий PR №3 остаётся Draft и не сливается в `main`.
