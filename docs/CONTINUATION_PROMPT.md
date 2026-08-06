# Continuation prompt — CoA Raid Intelligence Workbench

Скопируй весь текст этого файла в новый чат и выполняй его как стартовую задачу.

---

Продолжи работу с проектом:

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
local repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
working branch: e3/real-log-capture
Draft PR #7: e3/real-log-capture -> e2/log-evidence-refactor
parent Draft PR #3: e2/log-evidence-refactor -> main
```

## Главная задача этой сессии

До продолжения функциональной разработки выполни **полный аудит локального проекта и GitHub, архитектурный рефакторинг и очистку от ненужного**.

Особое внимание:

- лишние local/remote branches;
- устаревшие документы и статусы;
- мёртвый и дублирующий код;
- временные diagnostics/workarounds;
- generated artifacts;
- старый Excel/workbook-контур и всё, что больше не относится к действующей логике продукта или актуальному плану разработки.

Не удаляй ничего по названию или предположению. Сначала докажи назначение, зависимости и безопасность удаления.

## Обязательный live start

Не доверяй SHA, CI, counts, readiness и branch state из prompt как текущим фактам.

Сначала:

1. Через GitHub connector получи live состояние repository, PR #7 и PR #3.
2. Локально проверь:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short --branch
git fetch origin --prune
git rev-parse origin/e3/real-log-capture
```

3. Подтверди, что local/remote HEAD синхронизированы, либо безопасно объясни расхождение.
4. Получи latest exact-head `Verify repository` run через REST/`gh`, не через предположение по странице Actions.
5. До любых изменений прочитай в порядке:

```text
AGENTS.md
docs/COA_DOMAIN_BOUNDARY.md
docs/COA_TARGET_PRODUCT_DEFINITION.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/CONTINUATION_PROMPT.md
docs/CI_OPERATIONS.md
docs/E3_GUILD_PROGRESSION_EVIDENCE_STATUS.md
docs/REAL_LOG_CAPTURE.md
docs/GUILD_WIDE_COLLECTION_CONTRACT.md
evidence/real-data/README.md
relevant ADR/capture/review documents
```

6. Сравни документацию с кодом, migrations, tests, receipts, workflow и live GitHub state.
7. Отдельно отметь stale документы и PR metadata. PR #7 body на момент handoff содержал устаревшие HEAD/CI данные.

## Проверенный checkpoint перед handoff-документами

Это исторически подтверждённый checkpoint, а не разрешение пропустить live verification:

```text
HEAD: 66fd5ed89520070a7d48392f41fbfb7cb352b0f7
Verify repository run: #598
run ID: 31128752182
event: workflow_dispatch
conclusion: success
windows: success
ubuntu: success
public-release-audit: success
```

Локально на этом checkpoint:

```text
Ruff lint: passed
Ruff format: passed
focused helper-reference tests: passed
full pytest: 387 passed
repository verification: 10/10 passed
working tree after push: clean
```

После checkpoint были добавлены handoff documentation commits, поэтому exact current HEAD должен быть получен live.

## Последние подтверждённые инфраструктурные изменения

```text
c24f6f1c1e6b14ed5e464a2a00fe6d462183ae5b
Repair Ruff lock distributions

7e53d5e2841808d30f127e1917a36d24cf82bcfd
Reject Ruff source builds in CI

66fd5ed89520070a7d48392f41fbfb7cb352b0f7
Document CI operations and diagnostics
```

Состояние:

- Ruff 0.12.12 имеет Windows/Linux wheels в `uv.lock`;
- CI использует `uv sync --frozen --extra dev --no-build-package ruff`;
- `docs/CI_OPERATIONS.md` фиксирует incident и безопасную процедуру;
- `scripts/inspect_verify_workflow.ps1` выполняет exact-head REST diagnosis;
- не устанавливать Visual Studio Build Tools только ради Ruff.

## Подтверждённая проблема CI trigger

Обычный push к checkpoint `66fd5ed` не зарегистрировал exact-head `push` run, хотя workflow был active, Actions enabled, branch filter уже существовал и PR был clean/mergeable.

Known-good fallback:

```powershell
gh workflow run verify.yml `
  --repo GunsPojoshe/coa-raid-intelligence-workbench `
  --ref e3/real-log-capture
```

Manual dispatch run #598 прошёл полностью.

Правила:

- не создавать пустые commits для слепого trigger retry;
- не начинать длинный polling до получения конкретного run ID;
- для exact-head diagnosis использовать `scripts/inspect_verify_workflow.ps1` или REST;
- большие PowerShell programs с `if/elseif/else`, loops и here-strings запускать как `.ps1`, не вставлять построчно;
- проверить annotation о deprecated Node.js 20 target у pinned `actions/checkout`;
- классифицировать `StarletteDeprecationWarning` о `httpx`/`starlette.testclient` в dependency audit.

## Канонический продукт

Проект только для **Conquest of Azeroth**.

Не использовать как CoA-факты без независимого exact CoA evidence:

- Bronzebeard-specific mechanics;
- Classless Ascension ability-selection model;
- Mystic Enchants;
- Hero Architect assumptions;
- shared Ascension FAQ/frontend statements с неясным realm scope.

Главный продуктовый вопрос:

> Почему конкретный игрок нужен именно текущему составу?

Truth model:

```text
source response
-> immutable raw archive
-> exact hash and schema fingerprint
-> reviewed mapping/extractor
-> deterministic normalization/reconstruction
-> immutable observations
-> supporting and contradicting evidence
-> trust decision
-> explainable raid-leader recommendation
```

```text
combat-log observation != mechanic proof
class/spec presence != capability coverage
shared Ascension text != CoA mechanic proof
```

Только `corroborated` и `confirmed` mechanics могут участвовать в planner scoring.

## Проверенная data baseline

```text
public reports: 6454
unique public report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
migrations: 0001–0008
```

Private guild ID, report IDs, raw JavaScript, raw contexts и private source rows не versioned.

## Текущая progression evidence boundary

```text
route candidate: /api/guilds/progression
HTTP method candidate: POST
method candidate unambiguous: true
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
request shape verified: false
ready for bounded route probe: false
```

Versioned и implemented:

```text
helper-definition inventory: complete
helper-definition review: complete
helper-reference inventory: complete
helper-reference public receipt: versioned
helper-reference review implementation: complete
```

Не завершено:

```text
helper-reference review private execution complete: false
helper-reference review public receipt versioned: false
helper-owner inventory complete: false
helper owner binding resolved: false
helper identity resolved: false
request payload mapping resolved: false
request shape verified: false
ready for bounded progression route probe: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for encounter-aware roster completion: false
planner scoring allowed: false
```

Не выполнять guessed network request к `/api/guilds/progression`.

## Этап 1 — полный local/GitHub audit

До изменения кода подготовь доказательный audit report.

Проверь:

```text
repository settings
default branch and protections
open/closed/draft PRs
issues relevant to active development
workflow files and registered workflow states
recent Actions runs and exact-head mapping
local and remote branches
remote refs and stale refs
tags
merge bases
unique commits
working tree and ignored/untracked files
tracked generated artifacts
large files and accidental binaries
dependencies and lock consistency
migrations and schema ownership
test structure and coverage intent
runtime entrypoints
CLI commands
private/public evidence boundary
documentation graph and stale status references
```

Не модифицируй проект, пока не представишь audit findings и план.

## Этап 2 — branch inventory

Составь таблицу для **каждой** local и remote branch:

```text
branch
local/remote
last commit SHA and date
intended base
linked PR
open/closed/merged/draft status
merge-base
unique commits against intended base
contains commits absent from active branches
operational/staging/temp role
KEEP / ARCHIVE / DELETE candidate
exact evidence-backed reason
```

До подтверждения отсутствия нужных unique commits ветки не удалять.

Не удалять `main`, active PR branches или branches с неразобранной историей.

Destructive branch cleanup выполнять только после явного согласования пользователя.

## Этап 3 — repository cleanup inventory

Классифицируй каждый кандидат:

```text
KEEP
REFACTOR
ARCHIVE
DELETE
```

И отдельно укажи:

```text
runtime dependency
test dependency
migration/history dependency
evidence-chain dependency
documentation dependency
active plan dependency
privacy/security significance
safe deletion proof
```

Ищи:

- dead code;
- duplicate implementations;
- obsolete scripts;
- one-off diagnostics;
- stale receipts/status docs;
- temporary compatibility paths;
- generated artifacts accidentally tracked;
- obsolete dependencies;
- unused CLI commands;
- unreachable modules;
- redundant tests;
- stale GitHub workflows;
- documentation that describes abandoned architecture.

Сохраняй минимально достаточную историческую трассируемость, но не превращай репозиторий в архив старых прототипов.

## Этап 4 — старый Excel/workbook-контур

Найди все объекты и упоминания по признакам:

```text
Excel
xlsx
workbook
openpyxl
baseline workbook
/workbook/
старые названия конструктора состава
старые import/export scripts
legacy formulas
spreadsheet-based plans
```

Для каждого объекта определи:

```text
active runtime dependency
active development-plan dependency
required migration/history record
obsolete prototype
redundant generated artifact
unrelated legacy content
```

Удаление допустимо только после доказательства, что объект не нужен:

- runtime;
- tests;
- migrations;
- evidence chain;
- актуальным ADR;
- текущему плану разработки;
- воспроизводимости подтверждённых решений.

Цель — избавиться от старого Excel как канонической архитектуры и от нерелевантного наследия, но не потерять действующую бизнес-логику, которую ещё нужно перенести или формализовать.

## Этап 5 — plan before destructive changes

До удаления веток, файлов, dependencies или крупных rewrites представь:

1. подтверждённые findings;
2. список KEEP / REFACTOR / ARCHIVE / DELETE;
3. dependency impact;
4. rollback strategy;
5. atomic commit plan;
6. verification plan;
7. что требует отдельного решения пользователя.

Жди явного подтверждения destructive actions.

## Этап 6 — implementation rules

После согласования:

- выполнять изменения атомарными commit по одному scope;
- не смешивать branch cleanup, code refactor, docs cleanup и evidence changes;
- показывать exact diff перед commit;
- сохранять private data paths и `.gitkeep`;
- не публиковать cookies, tokens, browser profiles, raw HAR, raw private JS, IDs или private rows;
- не переписывать migrations задним числом;
- не повышать evidence gates по inference;
- после каждого крупного scope запускать relevant focused tests;
- перед push выполнить полный verification.

Обязательная локальная проверка:

```powershell
uv sync --frozen --extra dev --no-build-package ruff
uv run python -m ruff check .
uv run python -m ruff format --check .
uv run python -m pytest
uv run python scripts/verify_repo.py
```

Ожидаемый результат:

```text
Summary: 10/10 checks passed
```

После push проверить exact-head CI. Если automatic push-run отсутствует, использовать документированный bounded `workflow_dispatch` fallback и явно зафиксировать trigger mode.

## Обязательная защита private data

Не удалять и не публиковать contents из:

```text
data/raw
data/extracted
data/normalized
data/reconstructed
data/warehouse
data/exchange/in
data/exchange/out
local backups
browser/HAR/cookie/token/profile artifacts
```

Не коммитить private recovery outputs. Public receipts должны оставаться scalar-free и не раскрывать private identifiers или raw contexts.

## Результат этой сессии

Минимально требуемый результат:

1. live state report;
2. branch inventory;
3. repository cleanup inventory;
4. Excel/workbook dependency inventory;
5. stale documentation/PR metadata inventory;
6. refactoring and deletion plan;
7. явное разделение безопасных и destructive changes;
8. только после согласования — реализация cleanup;
9. green local verification and exact-head CI;
10. обновлённые canonical docs и PR metadata.

## Продолжение product development после cleanup

После завершённого, проверенного и задокументированного cleanup вернуться к bounded progression sequence:

```text
execute helper-reference review against exact private inventory
-> inspect all integrity checks and private result
-> validate scalar-free public review receipt
-> version only public receipt
-> implement helper-owner inventory and review
-> consider bounded route probe only after exact owner, helper and payload binding
```

No false gate may be raised by inference.
