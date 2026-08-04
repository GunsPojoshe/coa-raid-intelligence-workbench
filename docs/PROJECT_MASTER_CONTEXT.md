# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата полной сверки: **2026-08-04**.

Этот документ определяет долгосрочную цель, архитектуру, truth model и обязательную последовательность развития. Изменяемые HEAD, CI и оперативные blockers фиксируются в `docs/PROJECT_STATE.md` и всегда перепроверяются live.

## 1. Миссия

Создать localhost-first браузерное приложение для подготовки рейдов FLEX / 10 / 25 / 40 и evidence-first raid intelligence для Classless / Ascension WoW.

Система должна:

- хранить и проверять рейдовые планы;
- собирать реальные наблюдения с `coa.ascensionlogs.gg`;
- сохранять исходные ответы без изменений;
- связывать выводы с exact evidence;
- различать parser correctness, source identity, gameplay semantics и player performance;
- не использовать непроверенные наблюдения в planner scoring.

Канонический принцип:

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

Planner scoring допускает только `corroborated` и `confirmed` mechanics.

## 2. Product contours

### Raid Planner

- составы до 40 персонажей;
- class/spec/role catalog;
- структурная валидация;
- CRUD планов в DuckDB;
- explainable recommendations с provenance;
- constrained future BiS 25 optimizer.

### Raid Intelligence

- immutable raw capture;
- separate retrieval observations;
- hashes и schema fingerprints;
- reviewed mappings/extractors;
- canonical parser records;
- deterministic normalization/reconstruction;
- immutable observations;
- supporting/contradicting evidence;
- explicit trust evaluation;
- scoring только для достаточно подтверждённых mechanics.

## 3. Долгосрочная цель

```text
verified Argentum report corpus
-> stable multi-report identity for 30-40 candidate characters
-> comparable performance observations
-> global benchmark corpus
-> confidence-aware player evaluation
-> role/utility/availability constraints
-> explainable optimal BiS 25 roster
```

Каждый переход требует отдельного воспроизводимого receipt/review. Долгосрочная цель не разрешает перепрыгивать evidence gates.

## 4. Этапы и ветки

```text
E0  Excel baseline — закрыт как основной runtime
E1  localhost web and planner foundation
E2  evidence-first foundation — PR #3, Draft
E3  real log capture, review and persistence — PR #7, Draft
```

```text
main
└── e2/log-evidence-refactor        PR #3 -> main
    └── e3/real-log-capture         PR #7 -> e2
```

## 5. Evidence architecture

```text
source response
-> immutable raw payload
-> retrieval observation
-> SHA-256 + schema fingerprint
-> structural/field review
-> versioned mapping or dedicated extractor
-> exact raw validation
-> explicit promotion/publication
-> normalization/extraction
-> deterministic reconstruction
-> atomic immutable persistence
-> read models
-> hypotheses and evidence
-> trust evaluation
-> planner scoring
```

Верхний слой не может переписать нижний. Любой derived вывод обязан сохранять exact provenance.

## 6. Trust model

```text
legacy_unverified
observed
candidate
corroborated
confirmed
contradicted
rejected
```

Provenance:

```text
raw_log
upstream_derived
companion_addon
local_inference
manual_override
```

Не являются автоматическим gameplay knowledge:

- parser correctness;
- schema verification;
- guild identity verification;
- deterministic filtering;
- collection contract review;
- route/schema review;
- successful persistence;
- один combat-log event;
- display name или nickname.

## 7. Реализованный фундамент

- localhost FastAPI raid planner;
- DuckDB plans and CRUD;
- immutable content-addressed raw archive;
- separate retrieval observations;
- JSON/HAR privacy-safe tooling;
- schema fingerprints and verified mapping gates;
- canonical report/encounter/actor/participant/aura records;
- normalization rejects и Aura State Engine;
- hypotheses, evidence links and weighting policies;
- migrations `0001`–`0008`;
- repository verifier;
- Ubuntu/Windows CI;
- public-release audit.

## 8. Verified report and guild baseline

```text
public reports: 6454
unique public report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
```

Source guild ID, report IDs and private rows remain local-only.

## 9. Guild-search semantics checkpoint

Verified:

```text
route: /api/guilds/search
response keys: guilds, success
guild fields: id, name, realm, report_count
limit result counts: 1 / 7 / 7
limit truncation semantics verified: true
```

This proves bounded search-list truncation only. It does not prove guild-report pagination, termination or completeness.

## 10. Progression route discovery checkpoint

The archived SPA asset contains one `/api/guilds/progression` route candidate.

Usage-context review proved only a literal route reference and did not authorize a network probe.

A later helper/call-site inventory and review established:

```text
call class: generic_helper_call
HTTP method candidate: POST
method evidence: method_property_literal
method candidate unambiguous: true
helper identity resolved: false
request payload mapping resolved: false
request shape sufficient for bounded probe: false
ready for bounded route probe: false
```

The structural envelope around the call is overbroad and generic-helper identity remains unresolved. Therefore `POST` is not yet a complete request contract.

## 11. Helper-definition inventory stage

Implemented:

```text
src/coa_workbench/collector/guild_progression_helper_definition_command.py
src/coa_workbench/collector/guild_progression_helper_definition_index.py
src/coa_workbench/collector/guild_progression_helper_definition_inventory.py
scripts/inventory_guild_progression_helper_definition.py
tests/unit/test_guild_progression_helper_definition_command.py
tests/unit/test_guild_progression_helper_definition_index.py
tests/unit/test_guild_progression_helper_definition_inventory.py
```

Contract:

- offline-only;
- exact archived SPA asset;
- exact bound call-site/recovery artifacts;
- bounded helper-definition and alias search;
- private raw definitions, aliases, callees and JavaScript contexts;
- scalar-free public receipt;
- `36` integrity checks;
- no automatic promotion of route, pagination, completeness, crawl or scoring gates.

The implementation is CI-green at implementation HEAD `82265903a26bbf8e0032e6dc2512e623055da972`, run #578. The inventory has not yet been executed on the current local private artifacts and no helper-definition receipt/review is versioned.

## 12. Current decision boundary

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild-search route/schema verified: true
guild-search limit truncation verified: true
progression route candidate observed: true
progression usage context reviewed: true
progression helper/call-site reviewed: true
progression HTTP method candidate: POST
progression method candidate unambiguous: true
helper-definition inventory implementation complete: true
helper-definition inventory executed on private artifacts: false
helper-definition public receipt validated: false
helper-definition receipt versioned: false
helper-definition review complete: false
progression helper identity resolved: false
progression request payload mapping resolved: false
progression request shape verified: false
ready for bounded progression route probe: false
progression route semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## 13. Обязательная дальнейшая последовательность

```text
verify current documentation HEAD and CI
-> sync local branch by fast-forward
-> run offline helper-definition inventory against exact private artifacts
-> inspect private definitions/aliases/call-chain candidates
-> validate all integrity checks and privacy boundaries
-> version only the scalar-free public receipt
-> implement explicit deterministic helper-definition review
-> bounded progression route probe only if helper identity and payload mapping are verified
-> response schema review
-> pagination/termination/completeness evidence
-> deterministic API-versus-private-17-report-baseline comparison
-> explicit full-crawl promotion only if every gate passes
-> multi-report character identity graph
-> performance corpus
-> confidence-aware scoring
-> constrained BiS 25 optimizer
```

## 14. API-versus-baseline comparison contract

Future API-derived report set must be compared with the private verified 17-report baseline as:

```text
matching_reports
missing_from_guild_api
extra_in_guild_api
conflicting_report_records
```

Rules:

- exact typed report-ID comparison;
- deduplicate before comparison;
- preserve source order where applicable;
- preserve contradicting evidence;
- keep report IDs private;
- never mark partial capture complete;
- preserve failures as observations;
- bind resume/checkpoints to exact contract/hash.

## 15. Aura boundary

The current bounded report slice contains `0` aura events. Fixtures prove technical Aura State Engine behavior, not magnitude, stacking, scope, provider equivalence or gameplay criticality.

## 16. Data and Git policy

Versioned:

- code/tests;
- migrations;
- mappings and review decisions;
- documentation;
- scalar-free receipts.

Local-only:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never commit secrets, cookies, tokens, Authorization headers, browser profiles, unsanitized HAR, source guild IDs, report IDs, private queries, private receipts, raw JavaScript or raw archive content.

## 17. Local Windows operating conventions

```text
repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
```

- provide one complete PowerShell block;
- validate branch, expected HEAD and clean working tree;
- preserve evidence paths and tracked `.gitkeep` files;
- use `git --no-pager diff`;
- do not assume active `.venv` is required for standalone tools;
- do not install Visual Studio Build Tools solely for Ruff formatting;
- report any deviation from canonical `uv sync --frozen --extra dev` verification.

## 18. Workflow notification convention

After each push or connector write that launches GitHub Actions:

1. check the exact new run immediately;
2. report job states;
3. offer one opt-in completion notification for that run;
4. create it only after user acceptance;
5. disable it after completion or supersession.

The user prefers 15-minute polling. The current automation platform supports no more than hourly checking, so the limitation must be stated honestly.

## 19. Completion criteria for E3

PR #7 remains Draft until reviewed identity/filtering/crawl boundaries, reviewed combatants observations, sufficient aura observations and intervals, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows verification are present.