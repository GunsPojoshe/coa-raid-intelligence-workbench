# Continuation prompt — CoA Raid Intelligence Workbench

Скопируй весь текст ниже в новый чат и выполняй его как стартовую задачу.

---

Продолжи разработку проекта **CoA Raid Intelligence Workbench**.

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
local repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
working branch: e3/real-log-capture
Draft PR #7: e3/real-log-capture -> e2/log-evidence-refactor
parent Draft PR #3: e2/log-evidence-refactor -> main
```

## 1. Live start — не доверяй сохранённым SHA

Сначала через GitHub connector получи live состояние repository, PR #7, PR #3 и exact-head `Verify repository`.

Локально сначала только диагностика:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short --branch
git fetch origin --prune
git rev-parse origin/e3/real-log-capture
```

Не удаляй и не перезаписывай untracked файлы до их классификации.

Исторически последний полностью проверенный code/evidence checkpoint перед docs-handoff:

```text
HEAD: 13982825295737c029b425a37d210a34a7ea0762
commit: Review guild progression helper references
Verify repository run: #603
run ID: 31533555026
event: pull_request
conclusion: success
public-release-audit: success
ubuntu: success
windows: success
```

После него был создан docs-only handoff commit, поэтому current remote HEAD должен быть получен live. Локальная ветка пользователя может быть на один docs commit позади remote.

## 2. Прочитай канонический контекст

В порядке:

```text
AGENTS.md
docs/COA_DOMAIN_BOUNDARY.md
docs/COA_TARGET_PRODUCT_DEFINITION.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/E3_GUILD_PROGRESSION_EVIDENCE_STATUS.md
docs/CI_OPERATIONS.md
docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md
docs/CONTINUATION_PROMPT.md
```

Документация не заменяет live verification.

## 3. Ожидаемое локальное незакоммиченное состояние

На последнем пользовательском терминале helper-owner implementation был отформатирован и валидирован, но не staged/committed/pushed.

Ожидаемые untracked implementation files:

```text
scripts/inventory_guild_progression_helper_owners.py
src/coa_workbench/collector/guild_progression_helper_owner_index.py
src/coa_workbench/collector/guild_progression_helper_owner_inventory.py
tests/unit/test_guild_progression_helper_owner_inventory.py
```

Ожидаемые одноразовые root helper scripts, которые не являются project source:

```text
run-e3-commit-push-reference-review.ps1
run-e3-helper-reference-review-fixed-v3.ps1
run-e3-implement-helper-owner-inventory.ps1
run-e3-resume-helper-owner-inventory.ps1
run-e3-resume-helper-owner-inventory-v2.ps1
run-e3-resume-helper-owner-inventory-v3.ps1
```

Последний подтверждённый STOP BOUNDARY:

```text
Helper-owner implementation is formatted and validated.
No real helper-owner inventory was executed.
No private helper-owner artifact was created.
No progression route network request was performed.
Helper owner binding remains unresolved.
Bounded progression route probe remains disabled.
No files staged.
No commit performed.
No push performed.
```

Если actual local status отличается — остановись и классифицируй расхождение, не угадывай.

## 4. Safe synchronization после docs handoff

Перед `pull` проверь, что remote commits после local HEAD не затрагивают четыре untracked helper-owner implementation paths.

Если изменения только documentation и fast-forward безопасен:

```powershell
git pull --ff-only origin e3/real-log-capture
```

Не использовать reset/clean/checkout для обхода untracked state.

## 5. PowerShell environment

Пользователь использует VS Code extension:

```text
ms-vscode.powershell
observed version: 2025.4.0
```

Extension сохраняем. Для проектной Windows automation стандартизировать runtime на **PowerShell 7+ (`pwsh`)**, а не Windows PowerShell 5.1.

Проверь:

```powershell
$PSVersionTable.PSVersion
(Get-Process -Id $PID).Path
Get-Command pwsh -ErrorAction SilentlyContinue
```

Если `pwsh` отсутствует — помочь установить PowerShell 7 по официальной Microsoft инструкции и выбрать PowerShell 7 через VS Code PowerShell session menu. См. `docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md`.

Сложные automation scripts с loops/conditionals/here-strings выполнять как `.ps1`:

```powershell
pwsh -NoProfile -File .\script.ps1
```

Не возвращаться к Windows PowerShell 5.1 для новых project automation scripts без специальной причины.

## 6. Безопасная очистка root helper `.ps1`

После live status и successful sync можно удалить **только явно перечисленные** одноразовые root scripts, если они всё ещё untracked.

Не использовать broad wildcard/recurse cleanup. Не удалять versioned `scripts/*.ps1`, private data, receipts или `.gitkeep`.

После удаления снова показать:

```powershell
git status --short
```

Ожидаемо должны остаться только четыре helper-owner implementation files.

## 7. Текущая evidence chain

Versioned:

```text
helper-definition inventory: 36/36
helper-definition review: 42/42
helper-reference inventory: 40/40
helper-reference review: 46/46
```

Helper-reference review:

```text
public receipt: evidence/real-data/argentum-guild-progression-helper-reference-review.json
references: 31
disposition: unresolved_references_without_route_or_transport_binding
route-context references: 0
direct transport contexts: 0
route transport bindings: 0
route request-shape bindings: 0
request-shape contexts: 17
ready for helper-owner inventory: true
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
ready for bounded route probe: false
network requests performed: false
```

Blockers:

```text
route_not_observed_in_reference_contexts
direct_transport_markers_not_observed
receiver_or_owner_binding_unresolved
request_shape_markers_not_bound_to_route_invocation
```

Не выполнять guessed network request к `/api/guilds/progression`.

## 8. Helper-owner implementation — что проверять

Четыре локальных файла реализуют offline-only bounded owner-candidate inventory.

Ожидаемые свойства:

- exact binding к versioned helper-reference review;
- hash binding к private helper-reference inventory;
- exact raw archived SPA asset;
- public/private reference alignment;
- raw asset symbol/context span validation;
- bounded lexical owner candidate scan;
- raw owner chains только private;
- public receipt только hashes/counts/classes/booleans;
- `54` integrity checks;
- no network client/import;
- `helper_owner_binding_resolved = false`;
- `ready_for_bounded_progression_route_probe = false`;
- после successful inventory следующий gate — explicit helper-owner review.

До staging покажи полный exact diff четырёх файлов и проверь privacy/network boundary.

## 9. Verification перед commit

После синхронизации с docs handoff HEAD повторить:

```powershell
uv sync --frozen --extra dev --no-build-package ruff
uv run --no-sync python -m ruff check .
uv run --no-sync python -m ruff format --check .
uv run --no-sync python -m pytest tests/unit/test_guild_progression_helper_owner_inventory.py tests/unit/test_guild_progression_helper_reference_review.py -q
uv run --no-sync python scripts/verify_repo.py
```

Если проектная canonical команда отличается в актуальном `CI_OPERATIONS.md`, следовать ей после анализа причины.

Не заявлять pass без фактического выполнения на текущем HEAD + рабочем diff.

## 10. Atomic implementation commit

Если diff и verification корректны:

Stage только:

```text
scripts/inventory_guild_progression_helper_owners.py
src/coa_workbench/collector/guild_progression_helper_owner_index.py
src/coa_workbench/collector/guild_progression_helper_owner_inventory.py
tests/unit/test_guild_progression_helper_owner_inventory.py
```

Не добавлять root helper `.ps1`, private artifacts, generated outputs или docs в этот implementation commit.

Перед commit показать:

```powershell
git diff --cached --name-only
git --no-pager diff --cached
git diff --cached --check
```

Затем atomic commit/push и exact-head CI verification.

## 11. После green versioned implementation

Только после versioned implementation + green exact-head CI:

1. выполнить offline helper-owner inventory against exact private reference inventory/raw asset;
2. проверить 54/54;
3. проверить exact private/public SHA bindings;
4. убедиться, что public candidate scalar-free;
5. подтвердить `network_requests_performed=false`;
6. подтвердить все downstream gates false;
7. version only approved public helper-owner inventory receipt отдельным commit;
8. реализовать explicit helper-owner review;
9. route probe разрешать только после exact helper identity, owner binding и payload/request-shape evidence.

## 12. Privacy and integrity

Local-only:

```text
data/raw/
data/extracted/
data/normalized/
data/reconstructed/
data/warehouse/
data/exchange/in/
data/exchange/out/
```

Never commit:

- cookies/tokens/Authorization;
- browser profiles;
- unsanitized HAR;
- private source guild/report IDs;
- private queries;
- raw JavaScript;
- raw owner chains;
- raw private contexts;
- private receipts.

Do not delete `.gitkeep`. Do not rewrite published migrations. Do not raise evidence gates by inference.

## 13. Working style

Пользователь предпочитает:

- прямую пошаговую работу без лишней теории;
- complex PowerShell — готовым downloadable `.ps1`, не огромным paste block;
- полный код файлов без обрывов;
- exact diff перед commit;
- evidence-first выводы;
- при ошибке терминала — диагностировать конкретную точку и продолжать с текущего состояния, а не начинать заново.

Начни с live GitHub/local audit и безопасной синхронизации docs-only handoff commit. Не задавай вопросы, которые можно разрешить из repository state.
