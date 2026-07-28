# Фактическое состояние проекта

Дата актуализации: 2026-07-29.

Главный контекст:

```text
docs/PROJECT_MASTER_CONTEXT.md
```

Этот документ фиксирует изменяемое operational state. Перед работой проверять GitHub и код заново.

## Репозиторий

- repository: `GunsPojoshe/coa-raid-intelligence-workbench`;
- default branch: `main`;
- evidence branch: `e2/log-evidence-refactor`;
- active capture branch: `e3/real-log-capture`;
- PR #3: `e2/log-evidence-refactor -> main`, Draft;
- PR #7: `e3/real-log-capture -> e2/log-evidence-refactor`, Draft;
- PR #8 safe HAR inventory merged into PR #7;
- current verified PR #7 head before this documentation series: `ad605cc`;
- documentation commits after that head update the same active branch.

Не доверять commit count, HEAD или CI status из документа без проверки.

## Current product/evidence foundation

Реализовано:

- localhost FastAPI application;
- browser raid constructor FLEX / 10 / 25 / 40;
- DuckDB raid-plan persistence;
- immutable raw archive;
- separate observations and deduplicated payload bodies;
- source registry;
- JSON/HAR import;
- safe HAR inventory;
- schema fingerprints;
- verified normalization mapping gate;
- canonical report/encounter/actor/participant/aura records;
- Aura State Engine;
- hypotheses and supporting/contradicting evidence;
- trust and weighting policies;
- migrations `0001`–`0006`;
- repository verifier and Ubuntu/Windows CI;
- SPA/asset capture;
- frontend route discovery;
- Armory API collector;
- versioned HTTP profile `coa-fetch-context-v1`;
- persistent same-origin session with in-memory cookie jar;
- resilient HTTP read with timeout, retry, `IncompleteRead` and disconnect handling.

## Real aura checkpoint

### Encounter 64795

```text
report: 2987
spell: 968746
fingerprint: 2994424cb95c2a7e1997651226b7942367ebe77003e0f4614aae5da4920f8b98
mapping: coa-aura-timeline-single-encounter-v1
mapping status: verified
canonical events: 6
reconstructed intervals: 3
reference intervals: 3
rejects: 0
anomalies: 0
```

### Encounter 64796

```text
report: 2987
spell: 968746
window: 10382–38265 ms
full duration: 117215 ms
fingerprint: d8b6dd869d6adf8f3433f9e285b8270cd1aa8d640839c915a42c80b2211cbf0b
canonical events: 3
reconstructed intervals: 2
reference intervals: 2
rejects: 0
anomalies: 0
```

Это подтверждает technical behavior normalizer/Aura State Engine, но не numeric/runtime mechanic `Ninja's Focus`.

## Safe HAR inventory snapshot

Последний документированный локальный inventory:

```text
1367 entries
525 archived bodies
124 JSON objects
498 unique payloads
59 unique schema fingerprints
```

Structural candidates включают roster, buff uptimes, casts, aura detail, aura timeline и debuff sources.

HAR остаётся локальным и gitignored.

## HTTP access finding

Полный same-origin profile возвращал HTTP 200 для:

- `/api/reports/public`;
- `/api/characters/search`;
- `/api/armory/by-name/...`.

Profile:

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

Не доказано:

- минимальное подмножество headers;
- обязательность cookie;
- порядок request dependency;
- Armory-first behavior в completely fresh session.

## Real Armory capture state

Тестовый subject:

```text
Gunspojoshe
Vol'Jin
Tyrant
phase 0
World Bosses
normal
```

Identity подтверждена:

```text
character_id: 156120
character_class: Felsworn
has_armory: true
identity_source: by_name
profile: coa-fetch-context-v1
```

Успешно сохранено:

### armory_api_by_name

```text
HTTP: 200
keys: character, has_armory, latest_capture, success
payload hash: a81bb54342ee1573017b314af418e54da3ec56c51131f62bd2dd5efe826d5cff
fingerprint: 108ea5ed6a659d7161904ab087b4631df0f5c2ec69f94e1f2d90cbbaeaea0c37
```

### armory_api_captures

```text
HTTP: 200
bytes: 3151
keys: captures, success
payload hash: 34192051026d918ec0dcb311efc236c5873fda2f7748bc2acad128e5f5ec7851
fingerprint: e03d3b0d7c308ab4740280720cbaaaf60740a19e50826d23eb2194124397b814
```

Не завершено:

- `armory_api_character` body;
- `armory_api_talent_grid` body.

Наблюдаемое поведение:

- status успевал стать 200;
- body read зависал;
- были `TimeoutError` и один incomplete chunked transfer;
- `IncompleteRead` handling добавлен;
- последний повторный capture пользователь остановил во время второй попытки после 180-second timeout;
- aggregate result file не был создан;
- локальная DuckDB и уже сохранённые payloads не повреждены.

## Local DuckDB snapshot

Зафиксированный snapshot одного запуска:

```text
migrations: 6
unique raw objects: 786
fetch observations: 1603
HTTP 200: 1552
HTTP 201: 46
HTTP 401: 2
HTTP 403: 3
```

Armory snapshot позднее:

```text
armory_api_by_name: 2 unique payloads, 4 observations
armory_api_captures: 1 unique payload, 1 observation
```

Это локальное изменяемое состояние, не repository fixture.

## Tests and CI

Последний проверенный CI для commit `ad605cc`:

```text
workflow: Verify repository
run number: 65
Windows: success
Ubuntu: failure
Ubuntu full pytest: 78 passed, 1 warning
```

Ubuntu failure вызван Ruff gates, не tests/runtime:

- unused `ssl` in `scripts/diagnose_armory_access.py`;
- unused `FETCH_CONTEXT_PROFILE_VERSION` in `armory_api_capture.py`;
- formatting required for `scripts/diagnose_armory_access.py`;
- formatting required for `scripts/import_armory_har.py`.

Последний локальный targeted collector suite:

```text
12 passed
```

## Local Windows environment issue

`uv sync --frozen --extra dev` локально попытался build Ruff source distribution и завершился из-за отсутствующего MSVC `link.exe`.

При этом:

- runtime and targeted tests через `uv run --no-sync` работают;
- GitHub Actions Windows locked sync прошёл;
- не устанавливать Visual Studio Build Tools автоматически без отдельной диагностики wheel selection/cache/index behavior.

## Current blockers

1. Ruff CI blockers.
2. No complete `character` payload.
3. No complete `talent_grid` payload.
4. Full chain capture waits too long per endpoint.
5. Aggregate result is written only after the full chain.
6. No resumable/progressive endpoint manifest.
7. Armory mappings are not reviewed.
8. Full report/encounter/roster slice is not normalized.
9. Evidence coverage is still narrow.
10. No corroborated gameplay mechanic ready for canonical planner scoring.

## Next bounded tasks

1. Fix Ruff only; obtain green CI.
2. Implement endpoint-isolated Armory capture.
3. Add short bounded timeout and progressive result writing.
4. Capture only missing `character` and `talent_grid` endpoints.
5. Inspect and fingerprint their real structures.
6. Create reviewed mappings.
7. Implement bounded report discovery, default up to 5 reports/category.
8. Normalize complete report/encounter/roster slice.
9. Expand supporting and contradicting evidence.
10. Integrate only corroborated/confirmed mechanics into planner.

## Completion gate

PR #3 remains Draft until:

- real immutable payloads;
- stable fingerprints;
- verified mappings;
- normalized report/encounter/actors/participants/aura events;
- reconstructed intervals;
- independent supporting observations;
- contradicting evidence review;
- reproducible versioned output;
- green Ubuntu and Windows verification.
