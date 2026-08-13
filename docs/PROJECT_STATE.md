# Фактическое состояние проекта

Дата актуализации: **2026-08-13**.

Этот документ фиксирует оперативное состояние. Любой новый чат обязан перепроверять live HEAD, PR и CI; SHA ниже являются checkpoint, а не заменой live verification.

## 1. GitHub — live состояние на момент cleanup

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
local repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench

main
└── e2/log-evidence-refactor        Draft PR #3 -> main
    └── e3/real-log-capture         Draft PR #7 -> e2/log-evidence-refactor
```

Live PR state перед этим docs commit:

```text
PR #7: open, Draft, mergeable=true
PR #7 head: be899cc5f66c7bd82a1006116dbe57d91ecaed84
PR #3: open, Draft
```

Последний проверенный remote code/evidence checkpoint:

```text
HEAD: be899cc5f66c7bd82a1006116dbe57d91ecaed84
commit: Review guild progression helper owner binding
Verify repository: #613
run ID: 31651028612
conclusion: success
public-release-audit: success
ubuntu: success
windows: success
```

## 2. Branch audit и cleanup

На GitHub было 11 веток. Для продолжения разработки нужны только:

```text
main
e2/log-evidence-refactor
e3/real-log-capture
```

Подтверждённо устаревшие ветки:

```text
cleanup/remove-obsolete-baseline
codex/audit-repository-and-current-branch
codex/implement-cli-commands-for-har-inventory
codex/implement-project-verification-infrastructure
e0/approved-25-fixture
e1/localhost-web-pivot
e3/helper-reference-inventory-stage
e3/helper-reference-review-stage
```

Основания:

- cleanup/codex/e1 branches относятся к уже merged/closed PR;
- `e0/approved-25-fixture` относится к закрытому без merge legacy Excel PR #1 и больше не является active product path;
- обе `e3/helper-reference-*-stage` ветки являются строгими предками `e3/real-log-capture` (`behind_by=0` относительно active branch) и не содержат уникального continuation state.

Политика после cleanup: temporary branch удаляется после merge/closure либо после доказанного включения всех её commits в active branch.

## 3. Важная коррекция evidence chain

Исторические versioned helper receipts на remote HEAD были построены на lexical scanner, который позднее оказался недостаточно строгим.

Узкая offline диагностика доказала:

```text
2 relevant owner/reference anchors = template_text
0 = template-expression executable code
```

То есть helper-like terminal text внутри JavaScript template literal был принят за исполняемый reference.

Из-за общего упрощённого lexical подхода это затронуло не только owner interpretation, но и counts на definition/reference stages.

Следствие: старые versioned значения остаются историческими артефактами, но **не являются текущим доказательством helper identity/owner binding**:

```text
1 definition
31 references
17 owner candidates
8 owner groups
full-chain owner group 5
definition owner group 7
```

Старый вывод `5 != 7` не переносить в дальнейшую разработку.

## 4. Текущее локальное исправление — provisional, не versioned

Пользователь передал `e3-current-local.patch`. Он содержит 10 tracked modified files:

```text
src/coa_workbench/collector/guild_progression_helper_definition_index.py
src/coa_workbench/collector/guild_progression_helper_definition_review.py
src/coa_workbench/collector/guild_progression_helper_owner_index.py
src/coa_workbench/collector/guild_progression_helper_owner_inventory.py
src/coa_workbench/collector/guild_progression_helper_reference_index.py
src/coa_workbench/collector/guild_progression_helper_reference_inventory.py
src/coa_workbench/collector/guild_progression_helper_reference_review.py
tests/unit/test_guild_progression_helper_definition_review.py
tests/unit/test_guild_progression_helper_reference_inventory.py
tests/unit/test_guild_progression_helper_reference_review.py
```

`git diff HEAD` не показывает untracked files. По фактической истории текущей сессии дополнительно созданы как минимум:

```text
src/coa_workbench/collector/guild_progression_js_lexical.py
tests/unit/test_guild_progression_js_lexical.py
```

Последний owner-hardening updater завершился сообщением `owner inventory test asset block not found`, но до этой ошибки успел изменить tracked owner code. Поэтому current local state является **частично применённым repair**, а не завершённым атомарным change.

Последний предложенный `finish-e3-owner-hardening.py` пользователь **не запускал**.

## 5. Provisional результаты после lexical hardening

Они полезны для направления разработки, но не должны называться remote/versioned checkpoint до завершения repair.

### Definition

```text
full-chain occurrences: 2
terminal-symbol occurrences: 45
definition candidates: 3
definition kinds: method_definition
binding scopes: terminal_symbol
marker classes: []
```

Definition review:

```text
disposition: unresolved_multiple_terminal_method_definitions_without_transport_semantics
helper identity resolved: false
request payload mapping resolved: false
ready for bounded route probe: false
```

### References

```text
references: 45
full-chain: 2
terminal: 45
definition overlaps: 3
reference kinds: definition_candidate, invocation, member_reference, object_key
route-context references: 0
direct transport contexts: 0
request-shape contexts: 29
request-shape marker classes: JSON.stringify, body, data, method, params, url
```

Reference-review blockers remain:

```text
route_not_observed_in_reference_contexts
direct_transport_markers_not_observed
receiver_or_owner_binding_unresolved
request_shape_markers_not_bound_to_route_invocation
```

### Owners

Latest provisional public owner inventory:

```text
references: 45
owner candidates: 21
owner groups: 12
definition owner candidates: 1
references without owner candidates: 24
owner depths observed: 1, 2
full-chain owner group: 6, refs 6 and 20
cross-definition owner group: 8
helper owner binding resolved: false
ready for bounded route probe: false
network requests performed: false
```

Group `8` binds one definition candidate to eight non-definition references. It does **not** bind the two full-chain invocations in group `6`, so helper ownership is still unresolved.

The old `5 vs 7` owner model is superseded.

## 6. Verification status of local repair

Focused Ruff/tests shown in the terminal passed at multiple intermediate points, including a 25-test focused suite after the partial owner updater.

However:

```text
full scripts/verify_repo.py after the final current local diff: NOT RUN
current local repair committed: false
current local repair pushed: false
exact-head CI for the repair: does not exist
```

Do not call the local repair complete until the working tree is normalized, regression tests cover the lexical defect, one aggregate verifier passes, then the coherent change is committed/pushed and exact-head CI is green.

## 7. Development process agreed on 2026-08-13

- Agent performs all GitHub work it can perform itself.
- User is not a manual GitHub operator.
- Private/raw files may be inspected during analysis; privacy is a publication/versioning boundary.
- If local Windows execution is unavoidable, give the user one bundled action with one compact result/handoff.
- Prefer focused tests during iteration + one `verify_repo.py` before push + exact-head CI after push.
- One coherent commit per meaningful change; avoid process-driven micro-commits.
- Use diagnostics only to choose between concrete fixes.
- Do not create an endless chain of owner/alias evidence stages.

## 8. Next development action

Do **not** continue the old owner-relationship diagnostic loop.

At the next development session:

```text
normalize the partially applied lexical/analyzer repair
-> add/verify regression coverage for template text vs ${...} code
-> remove old hardcoded evidence counts from affected validators
-> run focused tests
-> run one full scripts/verify_repo.py
-> commit/push one coherent repair
-> verify exact-head CI
-> trace provenance of the two actual full-chain invocations (refs 6 and 20)
-> identify the concrete helper implementation
-> map exact helper arguments to request payload
-> only then review/allow one bounded /api/guilds/progression request
```

No guessed network request.

## 9. Local visibility boundary

The agent can read the full GitHub repository itself. It cannot directly enumerate the user's Windows filesystem unless the user shares an artifact/result.

For future local handoff:

- do not assume `git diff` is a complete working-tree snapshot;
- include untracked-file awareness;
- request one compact handoff artifact rather than many terminal commands;
- never ask the user to reproduce information already available from GitHub or already shared private files.

## 10. Privacy / integrity

Local-only data directories remain local/private. They may be inspected for analysis when shared, but are not published by default.

Do not delete `.gitkeep`. Do not rewrite published migrations. Do not raise evidence gates by inference.
