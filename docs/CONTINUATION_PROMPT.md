# Стартовый PROMPT для продолжения CoA Raid Intelligence Workbench

Ты продолжаешь разработку проекта **CoA Raid Intelligence Workbench**.

Repository:

```text
GunsPojoshe/coa-raid-intelligence-workbench
```

Активная ветка:

```text
e3/real-log-capture
```

Активный Draft PR:

```text
PR #7: e3/real-log-capture -> e2/log-evidence-refactor
```

## Обязательная проверка перед работой

До любых изменений:

1. Проверь repository, branch, remote HEAD и working tree.
2. Проверь PR #7: state, Draft, mergeable, base, head SHA, commits и changed files.
3. Проверь PR #3 и положение ветки PR #7 относительно его head.
4. Проверь последний GitHub Actions run и все jobs.
5. Прочитай полностью и в порядке:
   - `AGENTS.md`;
   - `docs/PROJECT_MASTER_CONTEXT.md`;
   - `docs/PROJECT_STATE.md`;
   - `docs/CONTINUATION_PROMPT.md`;
   - `docs/REAL_LOG_CAPTURE.md`;
   - `docs/GUILD_WIDE_COLLECTION_CONTRACT.md`;
   - `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md`;
   - `evidence/real-data/README.md`.
6. Сверь документацию с кодом, migrations, versioned receipts и CI.
7. Не доверяй старым HEAD, test count, CI run, hashes, routes или source counts без проверки.
8. До изменения аналитической семантики перечисли существенные расхождения.

## Последнее проверенное состояние до documentation refresh

```text
PR #7:
state: open
Draft: true
mergeable: true
base: e2/log-evidence-refactor
head: e3/real-log-capture
implementation HEAD: 297895c5ce3b26ce2911befd9addf474ef3e1138
commits: 449
changed files: 225

PR #3:
state: open
Draft: true
base: main
head: e2/log-evidence-refactor
head SHA: 4b42a7d0735ba1125e4f0ef14dd01422d4b55afc

Verify repository run #464:
public-release-audit: success
Ubuntu: success
Windows: success
reported tests: 300 passed
```

Documentation commits после этого baseline продвинули ветку. Фактический HEAD и CI перепроверь.

## Главная цель проекта

Построить evidence-first систему:

```text
source response
-> immutable raw archive
-> SHA-256 and schema fingerprint
-> reviewed verified mapping/extractor
-> canonical normalization or dedicated extraction
-> deterministic reconstruction
-> immutable observations
-> supporting and contradicting evidence
-> corroborated or confirmed mechanic
-> explainable planner scoring
```

Долгосрочная прикладная цель:

```text
verified Argentum reports
-> stable identity for 30-40 characters
-> multi-report performance corpus
-> comparable global benchmark
-> role/utility/availability constraints
-> explainable optimal BiS 25 roster
```

BiS 25 не является простым top-25 рейтингом. Оптимизатор должен учитывать роли, boss coverage, utility, defensives, устойчивость состава, confidence, sample volume, attendance и заменяемость.

## Trust boundaries

- Combat-log event является observation, не автоматическим доказательством общей mechanic.
- Parser correctness не подтверждает gameplay semantics.
- Label, nickname или display name не являются достаточным identity key.
- Observed/candidate data не допускаются в canonical planner scoring.
- Planner scoring разрешён только для `corroborated` и `confirmed` mechanics.
- Contradicting evidence сохраняется.
- Explicit operator promotion нельзя заменять автоматическим выводом.

## Завершённые checkpoints

### Armory

- реальные character и talent-grid payloads получены;
- immutable archives проверены;
- mappings имеют статус verified;
- exact raw production gate пройден.

### Report/encounter slice

Observed routes:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

Отдельный `/roster` route не наблюдался.

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants, 0 field conflicts
persisted through 0007: 77 canonical entity observations
```

### Combatants persistence

```text
migration: 0008_combatants_observation_persistence
persisted observations: 1343
actor/build observations: 1339
distinct linked actors: 11
integrity checks: 14/14
core actor mutations: 0
```

Read models:

```text
combatants_parser_observation_v1
combatants_actor_build_observation_v1
```

This verifies parser structure and persistence for the exact reviewed payload only. Companion-addon provenance, nested semantics, gameplay meaning and scoring remain unverified.

### Exhaustive public-report manifest

```text
receipt: evidence/real-data/argentum-public-report-manifest.json
route: /api/reports/public
limit: 25
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
terminal page reports: 4
integrity checks: 19/19
sentinel stability: verified
```

Guild fields:

```text
reports with both guild fields: 1171
distinct guild identity pairs: 88
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

### Snapshot identity review

```text
receipt: evidence/real-data/argentum-guild-identity-snapshot-review.json
exact label reports: 17
candidate guild-ID reports: 17
conflicting non-empty names: 0
integrity checks: 10/10
snapshot internal identity consistent: true
```

### Guild route and search evidence

Initial asset discovery/recovery failures were classified as timeout, TLS/network failure, partial-probe mismatch and access denial. They are not identity evidence.

Profiled recovery succeeded:

```text
receipt: evidence/real-data/argentum-guild-asset-profiled-recovery.json
profile: http1_1
HTTP status: 200
asset bytes: 3881146
API route candidates: 79
guild route candidates: 3
```

Observed route shapes:

```text
/api/guilds/progression
/api/guilds/search?q=<value>
/api/guilds/search?q=<value>&limit=<value>
```

Access diagnostic:

```text
minimal_http1_1: HTTP 403
spa_fetch_context: HTTP 200
```

Search schema inventory:

```text
receipt: evidence/real-data/argentum-guild-search-schema-inventory.json
guild objects: 1
field entries: 5
casefold label matches: 1
source ID matches: 1
integrity checks: 15/15
```

Reviewed object shape:

```text
guilds[]
├── id           integer
├── name         string
├── realm        string
└── report_count string
```

Mapping review:

```text
receipt: evidence/real-data/argentum-guild-search-mapping-review.json
mapped fields: 4
search results: 1
source ID matches: 1
name casefold matches: 1
integrity checks: 13/13
cross-endpoint identity candidate observed: true
ready for guild identity decision review: true
```

Reviewed mapping:

```text
$.guilds[].id           -> guild_id
$.guilds[].name         -> guild_name
$.guilds[].realm        -> realm
$.guilds[].report_count -> report_count
```

The private evidence shows the manifest candidate and the single guild-search result share the same source ID. The names match after Unicode casefold. Public receipts contain no raw guild ID or raw payload.

## Implemented but not yet executed checkpoint

Explicit identity decision:

```text
scripts/decide_guild_identity.py
src/coa_workbench/collector/guild_identity_decision.py
```

The CLI requires:

```text
--promote-identity
```

Without this flag the decision cannot be produced. Code existence does not verify identity.

A successful run revalidates the complete evidence chain and may set only:

```text
independent_source_identity_verified: true
guild_identity_verified: true
ready_for_guild_filtering: true
```

It must keep false:

```text
guild_api_route_semantics_verified
ready_for_full_guild_crawl
ready_for_multi_report_character_graph
ready_for_performance_model
ready_for_bis25_scoring
planner_scoring_allowed
```

## Текущая ближайшая задача

Выполнить **explicit local guild identity decision**.

Перед локальным запуском:

1. Проверь текущую реализацию decision CLI и tests.
2. Проверь, что CI текущего HEAD зелёный.
3. Не повторяй pagination, manifest, snapshot review, route discovery, schema inventory или mapping review без hash/fingerprint change.
4. Не публикуй raw guild ID, raw payload или private decision packet.
5. Не объявляй identity verified до получения и проверки нового scalar-free receipt.

Единственная локальная команда:

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location "C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench"

git fetch origin
git switch e3/real-log-capture
git pull --ff-only origin e3/real-log-capture
git status --short

$Head = (git rev-parse HEAD).Trim()
Write-Host "HEAD: $Head"

uv run --no-sync python scripts/decide_guild_identity.py `
    --promote-identity

$ExitCode = $LASTEXITCODE
if ($ExitCode -notin 0, 2) {
    throw "Guild identity decision failed with exit code $ExitCode"
}

Write-Host "Guild identity decision exit code: $ExitCode"
```

После выполнения загрузить только:

```text
data\exchange\out\argentum-guild-identity-decision.json
```

Не загружать и не коммитить:

```text
data\extracted\report-discovery\argentum-guild-identity-decision.private.json
```

Ожидаемый код — `0`. Он означает, что explicit promotion и все integrity checks прошли. До проверки receipt не утверждать, что identity подтверждён.

## После получения decision receipt

Проверить:

- decision kind/version;
- exact public manifest, snapshot review и mapping review SHA bindings;
- private decision SHA binding;
- all integrity checks;
- absence of source scalar values;
- absence of raw payload;
- explicit operator promotion flag;
- cross-endpoint source-ID equality;
- name casefold equality;
- `guild_identity_verified=true`;
- `ready_for_guild_filtering=true`;
- all crawl/graph/performance/scoring flags remain false.

После успешной проверки:

1. добавить scalar-free receipt в `evidence/real-data/`;
2. не добавлять private decision, private manifests, raw payloads или DuckDB;
3. обновить canonical docs и PR #7;
4. реализовать deterministic filtering by verified source guild ID;
5. сформировать deduplicated guild report manifest;
6. открыть full guild crawl только после отдельной проверки route semantics и collection contract.

## Следующая последовательность

```text
explicit guild identity decision
-> verified source-ID filtering
-> guild report manifest
-> reviewed full-crawl contract
-> per-report report/encounter/combatants capture
-> multi-report character identity graph
-> 30-40 unique candidate characters
-> performance observations
-> comparable global benchmark corpus
-> confidence-aware player scoring
-> constrained BiS 25 optimizer
```

## Жёсткие ограничения

- Не придумывать routes, parameters, fields, IDs или pagination rules.
- Не считать route candidate подтверждённой semantics.
- Не считать nickname/name достаточным identity key.
- Не использовать observed/candidate data в planner scoring.
- Не изменять опубликованные migrations.
- Не коммитить raw payloads, private manifests, private decisions, checkpoints, DuckDB, cookies, tokens или browser profiles.
- Не заявлять тесты/CI без фактической проверки.
- Не путать parser verification с gameplay semantics.
- Не игнорировать contradicting evidence.
- Не выполнять automatic promotion аналитических выводов.
- Пользователю давать один цельный короткий PowerShell-блок только для действий, невозможных через GitHub.
- GitHub-действия выполнять через connector, а не перекладывать на пользователя.

## Первый ответ нового агента

В первом ответе:

1. покажи фактические repository, branch, HEAD, working tree (если доступен), PR #7, PR #3 и latest CI;
2. перечисли расхождения документации, кода и receipts;
3. подтверди completed manifest, snapshot review, search schema/mapping review;
4. чётко раздели cross-endpoint candidate и explicit identity verification;
5. назови один bounded task: выполнить и проверить identity decision receipt;
6. сразу приступи к GitHub-части;
7. для локального decision выдай только один PowerShell-блок;
8. не заявляй identity verified до получения нового scalar-free receipt.