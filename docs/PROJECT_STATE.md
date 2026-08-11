# Фактическое состояние проекта

Дата актуализации: **2026-08-12**.

Этот документ фиксирует оперативное состояние. Любой новый чат обязан перепроверять live HEAD, PR и CI; SHA ниже являются подтверждёнными checkpoint, а не заменой live verification.

## Репозиторий и ветки

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
local repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench

main
└── e2/log-evidence-refactor        Draft PR #3 -> main
    └── e3/real-log-capture         Draft PR #7 -> e2/log-evidence-refactor
```

Последняя live-проверка перед этим documentation handoff:

```text
PR #7: open, Draft, mergeable=true
PR #7 head: 13982825295737c029b425a37d210a34a7ea0762
PR #3: open, Draft, mergeable=false
PR #3 head: 4b42a7d0735ba1125e4f0ef14dd01422d4b55afc
```

PR #7 body содержит устаревшие operational HEAD/CI/evidence сведения и должен быть актуализирован отдельно после следующего versioned implementation checkpoint.

## Последний полностью проверенный code/evidence checkpoint

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

Этот checkpoint versioned public helper-reference review. Documentation handoff commit, содержащий этот файл, будет иметь более новый SHA и должен быть получен live в следующем чате.

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

Private source guild ID, report IDs, raw JavaScript, raw contexts, private queries и private source rows не versioned.

## Guild progression evidence — завершённые versioned этапы

```text
helper-definition inventory: 36/36, versioned
helper-definition review: 42/42, versioned
helper-reference inventory: 40/40, versioned
helper-reference review: 46/46, versioned
```

Helper-reference review:

```text
public receipt: evidence/real-data/argentum-guild-progression-helper-reference-review.json
reference count: 31
disposition: unresolved_references_without_route_or_transport_binding
route-context references: 0
direct transport contexts: 0
route transport bindings: 0
route request-shape bindings: 0
request-shape contexts: 17
request-shape marker classes: [JSON.stringify, body, data, params, url]
ready for helper-owner inventory: true
network requests performed: false
```

Blockers:

```text
route_not_observed_in_reference_contexts
direct_transport_markers_not_observed
receiver_or_owner_binding_unresolved
request_shape_markers_not_bound_to_route_invocation
```

## Текущий локальный незакоммиченный этап

На пользовательской Windows-машине подготовлена и валидирована реализация helper-owner inventory. Она **не versioned** и отсутствует в remote HEAD на момент handoff.

Ожидаемые untracked implementation files:

```text
scripts/inventory_guild_progression_helper_owners.py
src/coa_workbench/collector/guild_progression_helper_owner_index.py
src/coa_workbench/collector/guild_progression_helper_owner_inventory.py
tests/unit/test_guild_progression_helper_owner_inventory.py
```

Последний локальный resume-run дошёл до `STOP BOUNDARY` без исключения после formatting, focused validation и полного repository verification. Зафиксированный boundary:

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

Реализация содержит offline-only owner-candidate inventory и контракт из `54` integrity checks. До versioning нельзя считать helper-owner inventory implementation remote/project checkpoint.

## Временные локальные PowerShell helper scripts

На момент handoff в корне локального repository оставались untracked:

```text
run-e3-commit-push-reference-review.ps1
run-e3-helper-reference-review-fixed-v3.ps1
run-e3-implement-helper-owner-inventory.ps1
run-e3-resume-helper-owner-inventory.ps1
run-e3-resume-helper-owner-inventory-v2.ps1
run-e3-resume-helper-owner-inventory-v3.ps1
```

Это одноразовые orchestration helpers, не project source. Их можно удалить точечно после live `git status` и до staging helper-owner implementation. Не использовать широкие wildcard/recurse удаления и не затрагивать versioned scripts, private evidence или `.gitkeep`.

## Текущая decision boundary

```text
helper-definition inventory complete: true
helper-definition review complete: true
helper-reference inventory complete: true
helper-reference review complete and versioned: true
helper-owner inventory implementation prepared locally: true
helper-owner inventory implementation versioned: false
helper-owner inventory executed on real private evidence: false
helper-owner public receipt versioned: false
helper-owner review complete: false
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
request shape verified: false
ready for bounded progression route probe: false
guild API route semantics verified: false
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

## PowerShell / VS Code development environment

Пользователь работает в VS Code с extension:

```text
Identifier: ms-vscode.powershell
Observed version at handoff: 2025.4.0
```

Extension оставляем. Основная проблема последних helper scripts была не в extension, а в фактическом runtime Windows PowerShell 5.1 / .NET Framework. Были воспроизведены несовместимости/quirks вокруг `System.IO.Path.GetRelativePath`, multiline external-command quoting, `gh --jq` quoting и root-array `ConvertFrom-Json` semantics.

Для дальнейшей проектной automation стандарт на Windows: **PowerShell 7+ (`pwsh`)**. Он устанавливается side-by-side с Windows PowerShell 5.1. Подробности: `docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md`.

## Следующие действия — обязательный порядок

1. Новый чат получает live GitHub state и локально выполняет `git fetch`/status.
2. Documentation handoff commit после `139828...` безопасно fast-forward pull-ится только после проверки, что он не затрагивает четыре untracked helper-owner implementation paths.
3. Проверить/настроить PowerShell 7 для VS Code и integrated terminal.
4. Удалить только перечисленные obsolete root `run-e3-*.ps1`, если они всё ещё существуют.
5. Повторно показать exact diff четырёх helper-owner implementation files и проверить privacy/network boundary.
6. На синхронизированном HEAD повторить relevant focused tests и полный `scripts/verify_repo.py`.
7. Stage **ровно четыре** helper-owner implementation files; не смешивать docs/evidence/temp scripts.
8. Commit и push atomic implementation change.
9. Проверить exact new HEAD CI: `public-release-audit`, `ubuntu`, `windows`.
10. Только после versioned green implementation выполнить **offline** helper-owner inventory против exact private reference inventory/raw asset.
11. Проверить 54/54, private/public hash binding, scalar-free public candidate и все false downstream gates.
12. Version only approved public helper-owner inventory receipt отдельным commit.
13. Реализовать explicit helper-owner review отдельным этапом.
14. Bounded route probe разрешать только после exact helper identity + owner binding + payload/request-shape evidence.

## Privacy / integrity rules

Сохранять local-only contents:

```text
data/raw/
data/extracted/
data/normalized/
data/reconstructed/
data/warehouse/
data/exchange/in/
data/exchange/out/
```

Never commit cookies, tokens, browser profiles, unsanitized HAR, source IDs, report IDs, private query, raw JS, raw owner chains, private receipts или raw private contexts.

Не удалять `.gitkeep`. Не переписывать опубликованные migrations. Не повышать evidence gate по inference.
