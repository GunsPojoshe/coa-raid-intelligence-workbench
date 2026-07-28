# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата последней полной сверки: 2026-07-29.

Этот документ — главная точка входа в проектный контекст. Он объединяет цель продукта, архитектуру, правила доверия, фактическое состояние реализации, локальное окружение, подтверждённые данные, ограничения, идеи и дорожную карту.

Он не заменяет проверку репозитория. Ветки, HEAD, PR, CI, количество тестов и локальные данные изменяются. Перед работой их нужно проверить заново.

## 1. Полная цель проекта

Создать localhost-first браузерное приложение для подготовки рейдовых составов и evidence-first анализа рейдовой эффективности в Classless / Ascension WoW.

Продукт должен решать две связанные задачи.

### 1.1. Конструктор рейда

Пользователь должен иметь возможность:

- собирать рейды FLEX / 10 / 25 / 40;
- размещать до 40 персонажей;
- выбирать класс, специализацию и роль;
- видеть структурные ошибки состава;
- сохранять, открывать, изменять и удалять планы;
- получать объяснимые рекомендации только из данных, достигших необходимого trust state.

### 1.2. Raid Intelligence

Система должна:

- автоматически получать доступные наблюдения с `coa.ascensionlogs.gg`;
- сохранять исходные ответы неизменяемо;
- отделять факты источника от локальных выводов;
- нормализовать только проверенные схемы;
- восстанавливать временное состояние аур и других механик;
- формировать hypotheses;
- накапливать supporting и contradicting evidence;
- различать глобальную игровую механику и качество исполнения конкретной гильдии;
- считать criticality по нескольким независимым измерениям;
- использовать в planner scoring только `corroborated` и `confirmed` mechanics;
- объяснять каждую рекомендацию через provenance, dataset version, mapping version, policy version и inference version.

Главный принцип:

```text
combat-log event = наблюдение
combat-log event != автоматическое доказательство общей игровой механики
```

## 2. История направления проекта

### E0 — Excel baseline

Первоначальная версия строилась вокруг Excel-конструктора. Были исправлены технические формулы OOXML, но утверждённый golden fixture на 25 игроков не был завершён. PR #1 закрыт без merge.

### E1 — переход на localhost web

PR #2 перевёл рабочий продукт с Excel на:

```text
Browser -> FastAPI -> Python domain logic -> DuckDB
```

Excel, Power Query и VBA исключены из runtime. Исторические Excel-данные сохранены только как legacy/reference material.

### E2 — evidence-first foundation

PR #3 вводит модель доказательности, immutable raw archive, normalization gates, Aura State Engine, hypotheses/evidence и trust-aware scoring.

### E3 — real log capture

PR #7 получает реальные payloads, исследует маршруты, фиксирует схемы и должен довести один полный report/encounter/roster/evidence slice до воспроизводимого результата.

## 3. Репозиторий и ветки

Репозиторий:

```text
GunsPojoshe/coa-raid-intelligence-workbench
```

Структура активных веток на момент сверки:

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Связанные PR:

- PR #2 — localhost web pivot, merged;
- PR #3 — evidence-first foundation, Draft;
- PR #4 — Aura State Engine hardening, merged into E2;
- PR #5 — verification runner and CI, merged into E2;
- PR #6 — canonical documentation refresh, merged into E2;
- PR #7 — real CoA Logs capture, active Draft;
- PR #8 — safe HAR inventory, merged into PR #7.

Правило: PR #3 остаётся Draft до полного evidence checkpoint. PR #7 остаётся Draft до завершения реального capture/normalization slice и зелёного CI.

## 4. Рабочее окружение пользователя

Подтверждённый рабочий профиль:

- Windows 11;
- сильная локальная машина;
- PowerShell;
- Python 3.12.x, в последней локальной диагностике — 3.12.13;
- `uv` для окружения и locked dependencies;
- Git;
- GitHub-репозиторий доступен пользователю `GunsPojoshe`;
- Docker ранее использовался;
- опыт традиционной разработки ограниченный;
- уровень vibe-coding высокий;
- уровень написания PROMPT — средний, непрофессиональный.

Локальный путь должен указываться в документации только в обезличенном виде:

```text
C:\Users\<USER>\source\repos\coa-raid-intelligence-workbench
```

Предпочтения пользователя:

- максимально автономная работа через GitHub;
- не просить действия, которые агент может выполнить сам;
- для локального запуска присылать один полный PowerShell-блок;
- не присылать оборванные процедуры, функции или код;
- прямые ответы без лишних вступлений;
- явно говорить, что реально проверено, а что нет;
- не передавать raw logs, HAR, cookies, credentials и приватные payloads в GitHub или чат.

## 5. Технологический стек

Runtime:

- Python >= 3.12;
- FastAPI;
- Uvicorn;
- Typer CLI;
- Pydantic;
- DuckDB;
- PyYAML;
- browser frontend, поставляемый локальным приложением.

Dev/test:

- pytest;
- Ruff;
- httpx;
- openpyxl только для legacy/regression задач, не для runtime.

Основные локальные директории:

```text
data/exchange/in
data/exchange/out
data/raw
data/warehouse
artifacts
```

Они содержат локальные или производные данные и должны оставаться gitignored.

## 6. Архитектура

### 6.1. Product runtime

```text
Browser
-> localhost FastAPI
-> planner / catalog / persistence API
-> DuckDB
```

### 6.2. Evidence pipeline

```text
source response
-> immutable raw observation
-> SHA-256 content addressing
-> schema inspection and fingerprint
-> explicitly reviewed mapping
-> canonical normalized records
-> deterministic state reconstruction
-> mechanic hypothesis
-> supporting and contradicting evidence
-> trust evaluation
-> planner scoring and recommendation
```

### 6.3. Разделение слоёв

Система обязана различать:

1. immutable raw payload;
2. upstream-derived fields;
3. canonical normalized observations;
4. local deterministic reconstruction;
5. local hypothesis;
6. supporting/contradicting evidence;
7. corroborated/confirmed mechanic;
8. planner output.

Нельзя переписывать нижний слой выводом верхнего слоя.

## 7. Модель доверия

Trust states:

```text
legacy_unverified
observed
candidate
corroborated
confirmed
contradicted
rejected
```

В canonical planner scoring допускаются только:

```text
corroborated
confirmed
```

Исторический статический каталог и provider links имеют статус `legacy_unverified`. Они разрешены только для контролируемого regression research и выключены из canonical scoring по умолчанию.

Provenance types должны оставаться раздельными:

```text
raw_log
upstream_derived
companion_addon
local_inference
manual_override
```

Нельзя:

- объявлять эффект покрытым только потому, что в составе есть класс или специализация;
- считать одинаковые display names эквивалентными механиками;
- выводить raid-wide scope из одного применения;
- считать отсутствие события в одном логе опровержением общей механики;
- смешивать данные разных game versions без явной версии;
- считать upstream-detected specialization доказательством provider mechanic;
- автоматически повышать trust mechanic после верификации parser/mapping.

## 8. Модель веса evidence

Вес evidence versioned и включает:

- exponential recency decay;
- отдельные global и guild cohorts;
- независимые минимумы reports и encounters;
- configurable thresholds подтверждения и отклонения;
- начальный default half-life 90 дней.

90 дней — параметр алгоритма, а не игровая истина.

## 9. Реализованный product foundation

Подтверждено кодом и историей PR:

- localhost FastAPI service;
- браузерный конструктор до 40 слотов;
- FLEX / 10 / 25 / 40;
- Python-валидация активных слотов и состава;
- class/spec/role catalog;
- автоматическое определение роли;
- DuckDB persistence для raid plans;
- create/read/update/delete планов;
- запрет сохранения некорректного плана;
- request ID и diagnostic logs;
- localhost-only bind по умолчанию;
- legacy catalog сохранён как forensic/regression layer;
- role limits для raid profiles пока не утверждены владельцем.

Текущие raid profile facts:

- `legacy_v9_25`: размер 25, class limit 3, spec limit 5, role limits не утверждены;
- `draft_10`: структурный draft, role/effect limits не утверждены;
- `draft_40`: структурный draft, role/effect limits не утверждены.

## 10. Реализованный evidence foundation

- source registry;
- safe source probe;
- immutable raw archive;
- payload SHA-256;
- observation отдельно от deduplicated payload body;
- JSON import;
- HAR import;
- deterministic privacy-safe HAR inventory;
- archived gzip JSON inspection;
- structure inspection and schema fingerprint;
- versioned normalization mappings;
- обязательный status `verified`;
- fingerprint gate;
- canonical report, encounter, actor, participant and aura events;
- rejects для unknown/incomplete records;
- Aura State Engine;
- anomalies with reason codes;
- hypotheses;
- supporting and contradicting evidence links;
- trust policy;
- weighting policy and inference-run persistence;
- migrations `0001`–`0006`;
- compatibility execution опубликованной migration `0005` без изменения файла/checksum;
- repository verifier;
- GitHub Actions Ubuntu + Windows.

## 11. Raw archive contract

Raw payload:

- сохраняется до semantic interpretation;
- неизменяем;
- content-addressed по SHA-256;
- повторный одинаковый payload не создаёт ещё один body;
- повторное получение создаёт отдельное observation;
- получает schema fingerprint, если это валидный JSON;
- связывается с sanitized request shape и безопасной metadata.

Нельзя коммитить:

- raw payloads;
- HAR;
- DuckDB;
- cookies;
- Authorization headers;
- access tokens;
- browser profiles;
- приватные query values;
- абсолютные локальные пути с username.

Cookies допускаются только в памяти процесса.

## 12. Normalization contract

Mapping разрешён только после просмотра реального payload.

Mapping должен содержать:

- точный schema fingerprint;
- mapping ID и version;
- status `verified`;
- explicit collection paths;
- explicit field mappings;
- provenance type;
- ссылку на reviewed payload hash или другой воспроизводимый source pointer.

Unknown fingerprint:

```text
reject -> review queue
```

Нельзя угадывать новую схему или автоматически применять похожий mapping.

## 13. Aura State Engine

Engine восстанавливает per-target intervals по событиям apply/refresh/remove/stack.

Он должен корректно обрабатывать:

- normal apply/remove;
- refresh;
- stack changes;
- missing remove;
- semantic duplicates;
- out-of-order events;
- multiple sources;
- multiple targets;
- encounter-end closure;
- observed-window start/end boundaries.

Interval содержит:

- encounter;
- source actor;
- target actor;
- spell;
- start/end timestamps;
- stack count;
- ordinals;
- state status;
- terminal/boundary reason;
- reconstruction version;
- provenance metadata;
- ambiguity/anomaly state.

## 14. Подтверждённый real aura checkpoint

Источник: локально сохранённые immutable CoA Logs payloads report `2987`, spell `968746` (`Ninja's Focus`).

### Encounter 64795 — полный timeline

- fingerprint: `2994424cb95c2a7e1997651226b7942367ebe77003e0f4614aae5da4920f8b98`;
- mapping: `coa-aura-timeline-single-encounter-v1`, `verified`;
- 6 canonical events;
- 3 reconstructed intervals;
- точное совпадение с 3 `debuff_sources` intervals;
- 0 rejects;
- 0 anomalies.

### Encounter 64796 — ограниченное окно

- observed window: `10382–38265 ms`;
- full encounter duration: `117215 ms`;
- fingerprint: `d8b6dd869d6adf8f3433f9e285b8270cd1aa8d640839c915a42c80b2211cbf0b`;
- baseline active target восстановлен через synthetic `window_start`;
- missing remove закрыт через `window_end`;
- 3 canonical events;
- 2 reconstructed intervals;
- точное совпадение с 2 `debuff_sources` intervals;
- 0 rejects;
- 0 anomalies.

Эти результаты corroborate поведение normalizer и Aura State Engine. Они не подтверждают игровую механику `Ninja's Focus`.

Не подтверждены:

- заявленное `+8% AP`;
- обязательность;
- raid-wide scope;
- stacking;
- overwrite;
- coexistence;
- эквивалентность похожим эффектам;
- provider criticality;
- ранее замеченный mismatch для `Demonfire Pact`.

## 15. Safe HAR inventory snapshot

Последний документированный локальный inventory:

```text
1367 HAR entries
525 archived response bodies
124 JSON objects
498 unique payloads
59 unique schema fingerprints
```

Подтверждены structural candidates для:

- roster;
- buff uptimes;
- casts;
- aura detail;
- aura timeline;
- debuff sources.

Route name не является достаточным доказательством семантики payload.

## 16. CoA Logs source discovery

Primary observation source:

```text
https://coa.ascensionlogs.gg
```

Frontend route discovery исторически подтвердил:

```text
GET /api/characters/search?q=<value>&limit=<value>
GET /api/armory/by-name/{character}?realm=<value>
GET /api/armory/character/{id}
GET /api/armory/character/{id}/captures?limit=<value>
GET /api/armory/talent-grid/{class-slug}
```

Также подтверждён публичный reports endpoint shape через access diagnostic:

```text
GET /api/reports/public?page=<value>&limit=<value>&sortBy=<value>&sortOrder=<value>
```

Фильтры, pagination policy и остальные endpoint parameters должны подтверждаться реальными frontend/payload observations, а не предполагаться.

## 17. Проверенный HTTP access profile

Простой `urllib` profile и только browser-like headers возвращали `403` для public reports, character search и Armory by-name.

Полный same-origin profile вернул `200`:

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

Он реализован как versioned profile:

```text
coa-fetch-context-v1
```

Реализация использует persistent same-origin session/opener и in-memory cookie jar. Metadata хранит profile version и header names, но не header/cookie values.

Ограничения интерпретации:

- проверен полный профиль, не минимальный subset;
- не установлен единственный обязательный header;
- access matrix первоначально вызывала reports endpoint до Armory;
- после первого успешного API response наблюдалась одна cookie;
- не доказано, требуется ли cookie для Armory-first fresh session;
- нельзя утверждать auth-only, browser-only, Cloudflare-only или TLS-fingerprint-only причину старых `403`.

## 18. Реальный Armory capture — подтверждённые локальные результаты

Тестовый субъект:

```text
character: Gunspojoshe
realm: Vol'Jin
spec: Tyrant
phase: 0
location: World Bosses
difficulty: normal
```

Первый реальный запуск нового profile подтвердил:

```text
character_id: 156120
character_class: Felsworn
has_armory: true
identity_source: by_name
http_profile_version: coa-fetch-context-v1
```

### Успешно сохранено

`armory_api_by_name`:

- HTTP 200;
- top-level keys: `character`, `has_armory`, `latest_capture`, `success`;
- один из подтверждённых payload hashes: `a81bb54342ee1573017b314af418e54da3ec56c51131f62bd2dd5efe826d5cff`;
- fingerprint: `108ea5ed6a659d7161904ab087b4631df0f5c2ec69f94e1f2d90cbbaeaea0c37`.

`armory_api_captures`:

- HTTP 200;
- 3151 uncompressed bytes в зафиксированном observation;
- top-level keys: `captures`, `success`;
- payload hash: `34192051026d918ec0dcb311efc236c5873fda2f7748bc2acad128e5f5ec7851`;
- fingerprint: `e03d3b0d7c308ab4740280720cbaaaf60740a19e50826d23eb2194124397b814`.

### Пока не завершено

`armory_api_character` и `armory_api_talent_grid`:

- HTTP status успевал определиться как 200;
- чтение response body зависало и завершалось timeout;
- в одном запуске сервер оборвал chunked transfer и вызвал `IncompleteRead`;
- обработка `IncompleteRead` добавлена в `http_read.py`;
- последующий запуск снова достиг read timeout;
- пользователь остановил повторную попытку через `Ctrl+C`;
- итоговый aggregate JSON этого запуска не создан;
- payloads detail и talent-grid пока не считаются полученными.

Следствие: access profile подтверждён, но transport/capture strategy для крупных или нестабильных ответов требует отдельного endpoint-isolated режима.

## 19. SPA observations

Ранее документированный frontend snapshot:

- SPA shell: 3753 bytes;
- asset: `/assets/index-DTWqLUGT.js`;
- asset size: 2664204 bytes.

Более новый локальный capture наблюдал:

- тот же размер SPA shell: 3753 bytes;
- другой shell payload hash: `a0a939ddd3a00e2e3af381c1e7fb5d3ffc691c5ccd811db0a374e6e5ab386412`;
- asset route: `/assets/index-DFAxcOOO.js`;
- asset body не был дочитан из-за timeout.

Эти snapshots должны храниться как time-versioned observations. Нельзя молча считать один asset name вечным.

## 20. Локальная DuckDB — наблюдавшийся snapshot

В одном локальном checkpoint зафиксировано:

```text
applied migrations: 6
unique raw objects: 786
fetch observations: 1603
HTTP 200 observations: 1552
HTTP 201 observations: 46
HTTP 401 observations: 2
HTTP 403 observations: 3
```

Позднее для Armory наблюдалось:

```text
armory_api_by_name: 2 unique payloads, 4 observations
armory_api_captures: 1 unique payload, 1 observation
```

Это изменяемый локальный snapshot, а не repository fixture. Raw database не коммитится.

## 21. HTTP transport implementation state

Реализовано:

- chunked reading через `read1`;
- retry loop;
- timeout handling;
- `IncompleteRead` handling с сохранением последних полученных bytes;
- `RemoteDisconnected` handling;
- max response bytes gate;
- deterministic fake-response tests.

Последний локальный targeted suite:

```text
12 passed
```

Он включал:

- `test_http_read.py`;
- `test_http_profile.py`;
- `test_armory_api_capture.py`.

Текущий design limitation:

- full Armory chain выполняется последовательно;
- default retry count равен 1, то есть две попытки;
- timeout применяется к каждому чтению;
- большой timeout может привести к длительному ожиданию одного endpoint;
- aggregate output записывается только после завершения всей функции;
- при `Ctrl+C` текущий progress не попадает в итоговый JSON.

## 22. CI и verification state

Repository verifier выполняет 10 checks:

- Ruff lint;
- Ruff format check;
- full pytest;
- doctor;
- CLI help;
- config smoke;
- legacy scoring disabled gate;
- unverified mapping rejected gate;
- clean temporary DuckDB initialization;
- repeated temporary DuckDB initialization.

Последний проверенный run для commit `ad605cc`:

- workflow run #65;
- Windows job — success;
- Windows locked sync — success;
- Windows pytest — success;
- Windows doctor — success;
- Windows DuckDB initialization twice — success;
- Ubuntu dependency sync — success;
- Ubuntu full pytest — `78 passed, 1 warning`;
- Ubuntu verifier — failure только из-за Ruff gates.

Известные Ruff blockers на этом snapshot:

- unused `ssl` в `scripts/diagnose_armory_access.py`;
- unused `FETCH_CONTEXT_PROFILE_VERSION` import в `armory_api_capture.py`;
- Ruff format требует reformat `scripts/diagnose_armory_access.py`;
- Ruff format требует reformat `scripts/import_armory_har.py`.

Не называть текущий PR полностью зелёным до нового успешного run.

## 23. Локальная проблема dev dependency sync

На пользовательской Windows-машине `uv sync --frozen --extra dev` попытался собрать `ruff==0.12.12` из source distribution и завершился ошибкой, потому что отсутствовал MSVC linker `link.exe`.

При этом:

- runtime environment уже позволял выполнять приложение и pytest через `uv run --no-sync`;
- GitHub Actions Windows установил locked dev dependencies успешно;
- проблема не доказана как общая проблема проекта;
- нельзя требовать установки полного Visual Studio Build Tools до проверки, почему uv не использовал совместимый wheel в этом локальном окружении.

## 24. Основные CLI commands

```powershell
uv run coa-workbench doctor --project-root .
uv run coa-workbench validate-config --path config/raid_profiles.yaml
uv run coa-workbench init-db --database data/warehouse/coa.duckdb --migrations migrations
uv run coa-workbench probe-source public_home
uv run coa-workbench import-json <payload.json>
uv run coa-workbench import-har <browser-export.har>
uv run coa-workbench inventory-har <browser-export.har> --output <inventory.json>
uv run coa-workbench inspect-json <payload.json>
uv run coa-workbench inspect-archived <payload-path-or-hash>
uv run coa-workbench normalize-json <payload.json> --mapping <verified-mapping.json>
uv run coa-workbench serve
uv run pytest
```

Full verifier:

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

При уже подготовленном окружении и локальной проблеме sync допускается для targeted diagnostics:

```powershell
uv run --no-sync pytest <tests>
```

Это не заменяет locked full verifier.

## 25. Целевой автоматизированный сбор reports

Ручное скачивание каждого полного лога не является целевой архитектурой.

```text
/api/reports/public
-> verified filters and pagination
-> deterministic selection, default up to 5 reports per category
-> encounter discovery
-> boss encounter selection
-> required analytical endpoints only
-> immutable archive
-> structural inventory/fingerprint
-> endpoint/schema parser
-> canonical normalization
```

Приоритет payloads:

- report metadata;
- encounter list/details;
- roster/combatants;
- aura timeline;
- aura detail;
- aura/buff uptimes;
- casts;
- debuff sources;
- deaths/damage/healing только для конкретной hypothesis.

Full event stream загружается только если специализированных endpoints недостаточно для temporal/causal analysis.

## 26. Parser strategy

Правило:

```text
one reviewed versioned parser per endpoint/schema
not one parser per file
```

Требования:

- known fingerprint allowlist;
- explicit schema version;
- deterministic output;
- reject unknown shape;
- source pointers;
- provenance;
- counts and reconciliation checks;
- no silent field coercion;
- no speculative semantic mapping.

## 27. Criticality model — целевая идея

Criticality не должна быть одним вручную заданным числом.

Отдельные dimensions:

- source-provided description and magnitude;
- runtime behavior evidence;
- uptime and target coverage;
- usage prevalence среди сильных групп;
- number and scarcity of providers;
- exact and similar alternatives;
- stacking/overwrite/refresh/coexistence;
- execution reliability;
- encounter dependence;
- global vs guild reproducibility.

Описание эффекта является semantic observation, но не доказательством runtime magnitude.

## 28. Product ideas and backlog

### Capture reliability

- endpoint-isolated capture command;
- short bounded timeout per endpoint;
- configurable retries/backoff только для retryable failures;
- progressive result file после каждого endpoint;
- resumable capture manifest;
- archive reuse для уже подтверждённых payloads;
- explicit transport warning metadata;
- response byte progress diagnostics без сохранения секретов;
- per-endpoint maximum size policy;
- rate-limit awareness;
- deterministic request ordering.

### Dataset management

- named dataset snapshots;
- manifest of payload hashes and fingerprints;
- dataset version in every inference run;
- review queue for unknown fingerprints;
- schema drift report;
- reproducible local export без raw secrets.

### Evidence analysis

- independent supporting observations across reports;
- contradicting observation search;
- order-sensitive stacking experiments;
- provider equivalence matrix;
- scope inference;
- guild vs global cohort comparisons;
- temporal drift by game version;
- execution reliability metrics;
- anomaly dashboard.

### Planner and UI

- recommendation explanation tree;
- unavailable/insufficient-evidence state instead of fabricated scores;
- source and trust badges;
- criticality decomposition;
- missing-mechanic view;
- provider scarcity view;
- encounter-specific composition advice;
- audit trail from recommendation to raw evidence.

## 29. Отброшенные или запрещённые выводы

Не повторять как факт:

- «Armory API требует авторизацию»;
- «обязательно нужен Playwright/browser/HAR»;
- «проблема только в Cloudflare или TLS fingerprint»;
- «browser-like User-Agent достаточно»;
- «HTML bootstrap обязателен»;
- «cookie точно не нужна»;
- «verified mapping подтверждает игровую механику»;
- «Ninja's Focus даёт +8% AP по combat logs»;
- «один parser нужен для каждого файла»;
- «полный event stream нужно скачивать всегда»;
- «один успешный endpoint подтверждает стабильность всей цепочки»;
- «HTTP status 200 означает, что body успешно и полностью сохранён».

## 30. Текущие риски и технический долг

1. PR #7 CI красный из-за Ruff gates.
2. `character` и `talent_grid` bodies не получены.
3. Aggregate Armory capture плохо переживает долгие endpoint timeouts и manual interruption.
4. Source registry ещё не отражает все проверенные API route templates как production-ready routes.
5. Minimal HTTP header subset и cookie/order dependency не изолированы.
6. Armory payload mappings не созданы.
7. Полный report/encounter/roster slice не нормализован.
8. Aura evidence ограничено одним spell и двумя encounters одного report.
9. Игровые stacking/overwrite/coexistence hypotheses не подтверждены.
10. Canonical planner пока не имеет достаточного подтверждённого mechanic dataset.
11. Локальный Windows dev sync Ruff требует отдельной диагностики.
12. FastAPI/httpx test stack выдаёт deprecation warning.

## 31. Следующий bounded plan

### Phase 0 — привести baseline в чистое состояние

1. Исправить четыре Ruff blockers.
2. Запустить новый CI.
3. Подтвердить green Ubuntu + Windows.
4. Не менять migrations.

### Phase 1 — endpoint-isolated Armory capture

1. Добавить capture одного явно заданного endpoint.
2. Записывать progress/result сразу после endpoint.
3. Использовать короткий bounded timeout.
4. Не повторять уже собранные `by_name` и `captures` без причины.
5. Получить `character` body.
6. Получить `talent_grid` body.
7. Сохранить hashes, fingerprints, sizes и safe transport metadata.

### Phase 2 — Armory structural review

1. Inspect real payloads.
2. Зафиксировать top-level structures, collection paths, counts and field types.
3. Отделить source fields от предполагаемой игровой семантики.
4. Создать candidate mappings.
5. После review перевести допустимые mappings в `verified`.

### Phase 3 — automated report discovery

1. Проверить pagination и filters на реальных responses/frontend behavior.
2. Реализовать deterministic selection policy.
3. Default: до 5 reports на категорию.
4. Реализовать encounter discovery и endpoint capture plan.
5. Добавить rate/retry/archive reuse policy.

### Phase 4 — full canonical slice

Нормализовать один полный набор:

```text
report
encounter
actors
participants/roster
aura events
```

Связать source pointers и provenance.

### Phase 5 — evidence expansion

1. Другие spells.
2. Другие reports.
3. Supporting observations.
4. Contradicting observations.
5. Stacking/overwrite/coexistence.
6. Provider equivalence.
7. Criticality dimensions.

### Phase 6 — planner integration

1. Допуск только corroborated/confirmed mechanics.
2. Reproducible scoring.
3. Explainable recommendations.
4. UI states для insufficient evidence.

## 32. Полный evidence checkpoint

PR #3 не сливается в `main`, пока не выполнено всё:

1. real immutable payloads;
2. recorded schema fingerprints;
3. reviewed verified mappings;
4. complete normalized report/encounter;
5. linked actors, participants and aura events;
6. reconstructed intervals;
7. repeatable mechanic with independent supporting observations;
8. reviewed contradicting evidence;
9. reproducible result with dataset/mapping/policy/inference versions;
10. provenance visible from recommendation to raw observation;
11. green verification on Ubuntu and Windows.

## 33. Порядок чтения для нового агента

Перед любыми изменениями:

1. проверить branch, HEAD и working tree;
2. проверить PR #7 и base branch;
3. проверить последний CI;
4. прочитать `AGENTS.md`;
5. прочитать этот документ;
6. прочитать `docs/PROJECT_STATE.md`;
7. прочитать `docs/CONTINUATION_PROMPT.md`;
8. прочитать relevant ADR/capture docs;
9. сверить документацию с кодом;
10. сообщить найденные расхождения до расширения модели.

## 34. Формат отчёта после задачи

Всегда указать:

- что проверено фактически;
- что было только локальным observation;
- какое старое утверждение оказалось неверным или устаревшим;
- files changed;
- migrations added;
- commands actually run;
- exact test results;
- CI state;
- remaining limitations;
- next bounded task.

Нельзя называть scaffolding, parser correctness или schema mapping подтверждённым игровым знанием.
