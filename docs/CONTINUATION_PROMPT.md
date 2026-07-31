# Стартовый PROMPT для продолжения CoA Raid Intelligence Workbench

Ты продолжаешь разработку проекта **CoA Raid Intelligence Workbench**.

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
branch: e3/real-log-capture
Draft PR #7: e3/real-log-capture -> e2/log-evidence-refactor
```

## Обязательная проверка перед работой

1. Проверь repository, branch, remote HEAD и working tree.
2. Проверь PR #7: state, Draft, mergeable, base, head SHA, commits и changed files.
3. Проверь PR #3 и положение `e3/real-log-capture` относительно `e2/log-evidence-refactor`.
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
7. Не доверяй старым HEAD, CI run, test count, hashes, routes или source counts без проверки.
8. До изменения аналитической семантики перечисли существенные расхождения.

## Главная цель

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

Долгосрочная цель:

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

- Combat-log event является observation, а не автоматическим доказательством mechanic.
- Parser correctness не подтверждает gameplay semantics.
- Label, nickname или display name не являются достаточным identity key.
- Observed/candidate data не допускаются в canonical planner scoring.
- Planner scoring разрешён только для `corroborated` и `confirmed`.
- Contradicting evidence сохраняется.
- Explicit operator promotion нельзя заменять автоматическим выводом.
- Identity verification и filtering не подтверждают route semantics, crawl completeness, character identity, performance или scoring.

## Завершённые checkpoints

### Report/encounter slice

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
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

### Explicit guild identity decision

```text
receipt: evidence/real-data/argentum-guild-identity-decision.json
integrity checks: 16/16
explicit operator promotion: true
cross-endpoint source-ID equality: true
name casefold equality: true
guild identity verified: true
ready for guild filtering: true
```

### Deterministic guild filtering

```text
receipt: evidence/real-data/argentum-guild-report-manifest.json
manifest version: verified-guild-report-manifest-v1
source reports: 6454
selected reports: 17
unique selected report IDs: 17
duplicate selected occurrences: 0
integrity checks: 14/14
guild filtering completed: true
guild report manifest deduplicated: true
report IDs published: false
source guild ID published: false
```

Filtering uses exact typed equality against the verified source guild ID loaded only from the private identity decision. Selection order follows the source manifest. Report IDs and source records remain private.

## Current boundary

```text
guild identity verified: true
guild filtering completed: true
guild report manifest deduplicated: true
selected guild reports: 17
full crawl collection contract reviewed: false
guild API route semantics verified: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Current nearest task

Review and implement the **full-crawl collection contract gate** without opening crawl automatically.

Required work:

1. Bind the contract to:
   - `argentum-public-report-manifest.json`;
   - `argentum-guild-identity-decision.json`;
   - `argentum-guild-report-manifest.json`.
2. Define the verified 17-report public-manifest-filtered set as the current baseline.
3. Specify exact evidence required for guild API route parameters, schema, pagination, termination and completeness.
4. Require immutable raw capture and exact hash/fingerprint bindings.
5. Require deterministic comparison of guild-API-derived and public-manifest-derived report sets.
6. Preserve missing, extra and conflicting reports as evidence.
7. Permit bounded per-report capture only after explicit contract review.
8. Keep full crawl, graph, performance and scoring flags false until their gates pass.

Do not repeat pagination, public manifest, identity decision or filtering unless a bound hash changes.

## Following sequence

```text
verified guild report manifest
-> reviewed full-crawl contract
-> verified guild API route semantics and completeness
-> bounded per-report report/encounter/combatants capture
-> multi-report character identity graph
-> 30-40 unique candidate characters
-> performance observations
-> comparable global benchmark corpus
-> confidence-aware player scoring
-> constrained BiS 25 optimizer
```

## CI note

The last completely green implementation baseline before filtering was run #464. Run #476 reported 303 passed but failed Ubuntu only on `ruff format --diff` for the new filter CLI. That formatting defect was corrected. The actual latest HEAD and CI must be checked; do not claim green status from these historical runs.

## Жёсткие ограничения

- Не придумывать routes, parameters, fields, IDs или pagination rules.
- Не считать route candidate подтверждённой semantics.
- Не считать nickname/name достаточным identity key.
- Не использовать observed/candidate data в planner scoring.
- Не изменять опубликованные migrations.
- Не коммитить raw payloads, source guild IDs, report IDs, private manifests, private decisions, checkpoints, DuckDB, cookies, tokens или browser profiles.
- Не заявлять тесты или CI без фактической проверки.
- Не путать parser verification, identity verification или filtering с gameplay semantics.
- Не игнорировать contradicting evidence.
- Не выполнять automatic promotion аналитических выводов.
- GitHub-действия выполнять через connector.
- Пользователю давать один цельный PowerShell-блок только для действий, невозможных через GitHub.