# Continuation prompt — CoA Raid Intelligence Workbench

Продолжи разработку проекта **CoA Raid Intelligence Workbench**.

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
local repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
working branch: e3/real-log-capture
Draft PR #7: e3/real-log-capture -> e2/log-evidence-refactor
parent Draft PR #3: e2/log-evidence-refactor -> main
```

## 1. Сначала сделай сам всё доступное

Через GitHub connector сам проверь:

- repository/branches;
- PR #7 и PR #3;
- current remote HEAD;
- exact-head CI и required jobs;
- relevant repository files/history.

Не проси пользователя выполнять GitHub-команды или вручную собирать сведения, которые доступны через connector.

Если нужен точный Windows local state, пользователь подключается только на этой границе. Дай одну bundled action/команду и попроси один компактный результат или один handoff artifact.

Private/raw files можно читать для анализа. Не путай private analysis с public/versioned publication.

## 2. Прочитай canonical context

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

Live verification имеет приоритет над сохранёнными SHA.

## 3. Важный E3 контекст

Remote checkpoint до docs cleanup:

```text
HEAD: be899cc5f66c7bd82a1006116dbe57d91ecaed84
Verify repository: #613
run ID: 31651028612
result: success
```

Старые versioned helper receipts воспроизводимы, но их текущая helper/owner интерпретация superseded из-за обнаруженного lexical bug: helper-like terminal text внутри template-literal text считался executable reference.

Не использовать как текущую модель:

```text
1 definition
31 references
owner groups 5 vs 7
```

## 4. Текущий local repair

Пользователь ранее передал `e3-current-local.patch` с 10 tracked modified files. Дополнительно в ходе repair создавались untracked shared lexical scanner/test.

Последний owner updater применился частично и затем остановился на:

```text
owner inventory test asset block not found
```

Последний предложенный `finish-e3-owner-hardening.py` пользователь не запускал.

Provisional corrected observations:

```text
definitions: 3
references: 45
definition overlaps: 3
route contexts: 0
direct transport contexts: 0
request-shape contexts: 29
owner candidates: 21
owner groups: 12
full-chain invocations: refs 6, 20 -> owner group 6
cross-definition owner group: 8
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
bounded route probe ready: false
network requests performed: false
```

These are local provisional results, not a completed/versioned checkpoint.

## 5. Working style

Use the streamlined development mode:

```text
focused tests while iterating
-> one coherent repair/change
-> one full scripts/verify_repo.py
-> one commit/push
-> exact-head CI
```

Add privacy/deterministic validation when evidence-sensitive. Avoid micro-commits and repeated full suites.

Diagnostics must decide a concrete next implementation. Do not build another long owner/alias relationship pipeline.

## 6. Next task when development resumes

First normalize the partially applied lexical/analyzer repair into one coherent diff:

- template text must not count as executable code;
- `${...}` template expressions remain executable code;
- affected validators must derive counts from evidence rather than old hardcoded `31/1` assumptions;
- add/retain regression tests;
- run focused tests and one full `verify_repo.py`;
- commit/push once and verify exact-head CI.

Then return to the actual product question:

```text
trace refs 6 and 20
-> determine concrete full-chain helper provenance/implementation
-> determine exact argument -> request payload mapping
-> review one bounded /api/guilds/progression request contract
-> only then perform the request
```

No guessed network request. No broad global alias search unless concrete provenance tracing proves it necessary.

## 7. Branch policy

Keep only active branches:

```text
main
e2/log-evidence-refactor
e3/real-log-capture
```

Delete temporary merged/closed/stage branches promptly. The audited cleanup list is in `docs/PROJECT_STATE.md`.

## 8. Safety

- Do not rewrite published migrations.
- Do not delete `.gitkeep`.
- Do not publish secrets/private evidence accidentally.
- Do not raise an evidence gate by inference.
- Do not treat local focused-test success as an exact-head remote checkpoint.

Начинай с самостоятельного GitHub/live audit. Пользователя подключай только если действительно нужен его локальный Windows/private boundary.
