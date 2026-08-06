# Фактическое состояние проекта

Дата актуализации: **2026-08-07**.

## Репозиторий и pull requests

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
local repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench

main
└── e2/log-evidence-refactor        Draft PR #3 -> main
    └── e3/real-log-capture         Draft PR #7 -> e2/log-evidence-refactor
```

Проверенный implementation checkpoint перед handoff-документами:

```text
HEAD: 66fd5ed89520070a7d48392f41fbfb7cb352b0f7
PR #7 state: open, Draft
PR #7 mergeable at final check: true
Verify repository run: #598
run ID: 31128752182
event: workflow_dispatch
conclusion: success
public-release-audit: success
ubuntu: success
windows: success
```

После обновления handoff-документов exact HEAD снова изменится. Новый чат обязан получить branch, HEAD, PR и CI live, а не копировать SHA из документа.

PR #7 body содержит устаревший HEAD и устаревшее CI-состояние. Его актуализация входит в следующий repository audit.

## Локальная проверка checkpoint `66fd5ed`

```text
Ruff lint: passed
Ruff format: passed
focused helper-reference tests: passed
full pytest: 387 passed
repository verification: 10/10 passed
clean database initialization: passed
repeated database initialization: passed
working tree after push: clean
```

Наблюдаемое предупреждение pytest:

```text
StarletteDeprecationWarning:
Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

Это не ломает текущую проверку, но должно быть классифицировано в следующем dependency audit.

## Последние инфраструктурные commit checkpoint

```text
c24f6f1c1e6b14ed5e464a2a00fe6d462183ae5b
Repair Ruff lock distributions

7e53d5e2841808d30f127e1917a36d24cf82bcfd
Reject Ruff source builds in CI

66fd5ed89520070a7d48392f41fbfb7cb352b0f7
Document CI operations and diagnostics
```

Добавлены или изменены:

```text
uv.lock
.github/workflows/verify.yml
docs/CI_OPERATIONS.md
scripts/inspect_verify_workflow.ps1
```

Ruff 0.12.12 теперь имеет Windows/Linux wheel records в `uv.lock`. CI выполняет:

```text
uv sync --frozen --extra dev --no-build-package ruff
```

Источник Ruff больше не должен молча собираться через Rust.

## Подтверждённая проблема GitHub Actions trigger

Обычный push, который перевёл ветку с `42dfc1d` на `66fd5ed`, не зарегистрировал exact-head `push` run даже после того, как `e3/real-log-capture` уже присутствовал в `push.branches`.

При этом подтверждено:

```text
repository Actions enabled: true
allowed actions: all
workflow state: active
PR head correct: true
PR mergeable state before final push: clean
workflow_dispatch availability: true
```

Рабочий bounded fallback:

```powershell
gh workflow run verify.yml `
  --repo GunsPojoshe/coa-raid-intelligence-workbench `
  --ref e3/real-log-capture
```

Run #598 доказал работоспособность workflow и всех трёх jobs. Автоматическая доставка `push`-события остаётся отдельной инфраструктурной проблемой и не должна маскироваться пустыми commit или слепым polling.

GitHub Actions также выдал annotation о том, что pinned `actions/checkout` target Node.js 20 принудительно выполняется на Node.js 24. Это отдельный upgrade/audit item.

## Каноническая предметная граница

Проект предназначен только для **Conquest of Azeroth**.

Не использовать как CoA-факты без независимого exact CoA evidence:

- Bronzebeard-specific mechanics;
- Classless Ascension ability-selection model;
- Mystic Enchants;
- Hero Architect assumptions;
- shared Ascension FAQ/frontend statements с неясным realm scope.

Главный продуктовый вопрос:

> Почему конкретный игрок нужен именно текущему составу?

Каноническая модель истины:

```text
source response
-> immutable raw archive
-> exact hash and schema fingerprint
-> reviewed mapping/extractor
-> deterministic normalization/reconstruction
-> immutable observations
-> supporting and contradicting evidence
-> explicit trust decision
-> explainable raid-leader recommendation
```

```text
combat-log observation != mechanic proof
class/spec presence != capability coverage
shared Ascension text != CoA mechanic proof
```

Только `corroborated` и `confirmed` mechanics могут входить в planner scoring.

## Проверенные data checkpoints

```text
public reports: 6454
unique public report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
migrations: 0001–0008
```

Private source guild ID, report IDs, raw JavaScript, raw contexts and private source rows не должны попадать в Git.

## Guild progression evidence boundary

```text
route candidate: /api/guilds/progression
HTTP method candidate: POST
method candidate unambiguous: true
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
request shape verified: false
ready for bounded route probe: false
network requests performed by evidence stages: false
```

Подтверждено и versioned:

```text
helper-definition inventory: complete
helper-definition review: complete
helper-reference inventory: complete
helper-reference public receipt: versioned
helper-reference review implementation: complete
```

Текущая evidence boundary:

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

Do not perform a guessed network request to `/api/guilds/progression`.

## Первая задача следующего чата

До продолжения evidence implementation необходимо выполнить **полный repository audit, refactoring и cleanup**.

Никакие ветки, файлы, документы или старые Excel-артефакты нельзя удалять до инвентаризации и классификации.

Обязательный порядок:

```text
1. live local/GitHub state verification
2. complete local and remote branch inventory
3. repository file and dependency inventory
4. classify every cleanup candidate as KEEP / REFACTOR / ARCHIVE / DELETE
5. present evidence-backed cleanup plan
6. obtain explicit approval for destructive actions
7. perform atomic refactoring and cleanup
8. run full local verification
9. run exact-head CI through proven trigger/fallback
10. update canonical docs and PR metadata
```

Branch inventory должна содержать:

```text
branch name
local/remote
last commit
linked PR
merged/unmerged status
unique commits against intended base
protected or operational role
KEEP / DELETE candidate
exact reason
```

До подтверждения `unique commits = 0` или осознанного сохранения истории ветку не удалять.

## Старый Excel-контур

Следующий audit должен найти все упоминания и зависимости по признакам:

```text
Excel
xlsx
workbook
openpyxl
baseline workbook
/workbook/
старые названия конструктора состава
старые import/export scripts
legacy formulas and plans
```

Каждый объект сначала классифицировать:

```text
active runtime dependency
active development plan
required migration/history record
obsolete prototype
redundant generated artifact
unrelated legacy content
```

Удалять только то, что доказанно не требуется runtime, тестам, evidence chain, миграциям, актуальным ADR или планам разработки.

Цель cleanup — оставить:

- действующую логику продукта;
- проверяемые data/evidence contracts;
- актуальные архитектурные решения;
- реальный план разработки;
- необходимые operational instructions;
- минимальную достаточную историческую трассируемость.

## Обязательные ограничения cleanup

Сохранить и не публиковать private contents из:

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

Не удалять `.gitkeep`, миграции, public scalar-free receipts или доказательства целостности без отдельного анализа.

Большие PowerShell automation blocks с `if/elseif/else`, loops или here-strings запускать только как `.ps1`, а не вставлять построчно в интерактивную консоль.

## Продолжение функциональной разработки после cleanup

После завершения и проверки cleanup вернуться к bounded sequence:

```text
execute helper-reference review against exact private inventory
-> inspect all integrity checks and private result
-> validate scalar-free public review receipt
-> version only public receipt
-> implement helper-owner inventory and review
-> consider bounded route probe only after exact owner, helper and payload binding
```

No false gate may be raised by inference.
