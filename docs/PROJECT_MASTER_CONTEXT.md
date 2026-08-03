# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата полной сверки: **2026-08-03**.

Этот документ определяет долгосрочную цель, архитектуру, truth model, завершённые major checkpoints и обязательную последовательность развития. Изменяемые HEAD, CI, counts и оперативные blockers фиксируются в `docs/PROJECT_STATE.md` и всегда перепроверяются.

## 1. Миссия

Создать localhost-first браузерное приложение для подготовки рейдов FLEX / 10 / 25 / 40 и evidence-first raid intelligence для Classless / Ascension WoW.

Система должна:

- хранить и проверять рейдовые планы;
- собирать реальные наблюдения с `coa.ascensionlogs.gg`;
- сохранять исходные ответы без изменений;
- объяснимо связывать выводы с exact evidence;
- различать parser correctness, source identity, gameplay semantics и player performance;
- не использовать непроверенные наблюдения в planner scoring.

Канонический принцип:

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

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
- trust evaluation;
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

Эта цель не разрешает перепрыгивать evidence gates. Каждый переход требует отдельного воспроизводимого receipt/review.

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

Planner scoring разрешён только для `corroborated` и `confirmed`.

Provenance:

```text
raw_log
upstream_derived
companion_addon
local_inference
manual_override
```

Запрещено автоматически считать gameplay knowledge:

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

## 8. Report/encounter и combatants baseline

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants
persisted through 0007: 77 canonical entity observations
combatants through 0008: 1343 parser observations
actor/build observations: 1339
linked actors: 11
combatants checks: 14/14
```

Это подтверждает reproducibility parser/persistence pipeline. Это не подтверждает companion-addon provenance, nested identifier semantics, gameplay mechanics или planner suitability.

## 9. Public-report baseline

```text
receipt: evidence/real-data/argentum-public-report-manifest.json
route: /api/reports/public
limit: 25
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
integrity checks: 19/19
exact Argentum label reports: 17
```

Receipt подтверждает completeness конкретного captured public snapshot, но не общую completeness provider и не identity гильдии сам по себе.

## 10. Guild identity и filtering

```text
identity receipt: evidence/real-data/argentum-guild-identity-decision.json
identity checks: 16/16
guild identity verified: true

filtered receipt: evidence/real-data/argentum-guild-report-manifest.json
selected reports: 17
unique selected report IDs: 17
filter checks: 14/14
guild filtering completed: true
```

Source guild ID и report IDs остаются private. Private 17-report set является verified comparison baseline для будущего API-derived report set.

## 11. Full-crawl collection contract

```text
receipt: evidence/real-data/argentum-guild-full-crawl-contract.json
integrity checks: 12/12
full crawl collection contract reviewed: true
verified private comparison baseline: 17 reports
```

Contract требует до разрешения full crawl независимо доказать:

1. exact route/query contract;
2. immutable raw capture;
3. payload SHA-256 и schema fingerprint;
4. reviewed collection shape and types;
5. limit behavior;
6. pagination semantics;
7. termination semantics;
8. completeness boundary;
9. deterministic API-versus-baseline comparison;
10. preservation of missing, extra and conflicting records;
11. explicit scalar-free promotion decision.

## 12. Guild route capture и route/schema review

Capture:

```text
receipt: evidence/real-data/argentum-guild-route-semantics-capture.json
attempts: 3
completed attempts: 3
HTTP 200 responses: 3
integrity checks: 13/13
observed result counts: [1]
payload hash stable: true
schema fingerprint stable: true
source ID set stable by hash: true
pagination object observed: false
```

Observed request shapes:

```text
/api/guilds/search?q=<target>&limit=1
/api/guilds/search?q=<target>&limit=25
/api/guilds/search?q=<target>
```

Review:

```text
receipt: evidence/real-data/argentum-guild-route-semantics-review.json
review version: guild-route-semantics-review-v1
integrity checks: 22/22
route template verified: true
query shapes verified: true
response envelope verified: true
guild record schema verified: true
limit parameter accepted: true
ready for bounded limit-semantics capture: true
```

Verified response schema:

```text
top-level kind: object
top-level keys: guilds, success

guild record:
  id: integer
  name: string
  realm: string
  report_count: string
```

Все три bounded cases вернули одну и ту же запись. Поэтому limit truncation, pagination, termination и completeness не подтверждены.

## 13. Реализованный bounded multi-result limit probe

Implementation:

```text
src/coa_workbench/collector/guild_limit_semantics_capture.py
scripts/capture_guild_limit_semantics.py
tests/unit/test_guild_limit_semantics_capture.py
```

Probe выполняет ровно три запроса:

```text
private query + low limit
private query + high limit
private query + identical high-limit repeat
```

Capture-ready conditions:

- all three responses complete and valid;
- stable response schema;
- low result count equals low limit;
- high result count is greater than low and does not exceed high;
- high-limit repeat has identical ordered-record hash;
- high-limit repeat has identical source-ID-order hash;
- low-limit source-ID hash sequence is an exact prefix of high-limit sequence.

Public receipt не должен содержать query, request URL, source IDs, raw records или error text. Даже успешный capture устанавливает только `ready_for_limit_semantics_review=true`. Promotion `limit_truncation_semantics_verified=true` требует отдельного review receipt.

## 14. Текущий этап простыми словами

Мы завершили проверку адреса API и структуры ответа. Следующий вопрос — действительно ли `limit=1` возвращает первый элемент той же выдачи, а больший limit возвращает стабильное расширение этой выдачи.

Код такой проверки готов и покрыт deterministic tests. Осталось:

1. получить green CI на актуальном HEAD;
2. локально выбрать приватную query, возвращающую несколько гильдий;
3. выполнить bounded capture;
4. проверить и version scalar-free receipt;
5. выпустить отдельное limit-semantics review.

Full crawl пока не разрешён.

## 15. Current decision boundary

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild route template verified: true
guild query shapes verified: true
guild response schema verified: true
limit parameter accepted: true
ready for bounded limit-semantics capture: true
limit truncation semantics verified: false
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

## 16. Обязательная дальнейшая последовательность

```text
green CI on current HEAD
-> bounded multi-result limit capture
-> explicit limit-semantics review
-> separate pagination review
-> separate termination/completeness review
-> deterministic API-versus-private-17-report-baseline comparison
-> explicit full-crawl promotion only if every gate passes
-> per-report report/encounter/combatants capture
-> multi-report character identity graph
-> 30-40 unique candidate characters
-> performance observations
-> global benchmark corpus
-> confidence-aware scoring
-> constrained BiS 25 optimizer
```

## 17. API-versus-baseline comparison contract

Будущий API-derived report set сравнивается с private verified 17-report baseline и делится на:

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

## 18. Aura boundary

Текущий bounded report slice содержит `0` aura events. Separate fixtures подтверждают technical Aura State Engine behavior, но не magnitude, stacking, scope, provider equivalence или criticality.

## 19. Data and Git policy

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

Never commit secrets, cookies, tokens, Authorization headers, browser profiles, unsanitized HAR, source guild IDs, report IDs, private queries, private decisions or private manifests.

## 20. Verification contract

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Storage changes require clean and repeated DuckDB initialization. Collector changes require deterministic fake-response tests before bounded real capture. Never claim green CI from an older HEAD.

## 21. Completion criteria for E3

PR #7 remains Draft until reviewed identity/filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows verification are present.
