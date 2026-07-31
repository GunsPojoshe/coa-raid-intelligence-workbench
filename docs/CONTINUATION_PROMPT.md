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

## Trust boundaries

- Combat-log event является observation, а не доказательством общей mechanic.
- Parser correctness не подтверждает gameplay semantics.
- Label, nickname или display name не являются достаточным identity key.
- Planner scoring разрешён только для `corroborated` и `confirmed`.
- Contradicting evidence сохраняется.
- Explicit operator promotion нельзя заменять автоматическим выводом.
- Identity verification, filtering и contract review не подтверждают route semantics, crawl completeness, character identity, performance или scoring.

## Завершённые checkpoints

```text
report/encounter:
  normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
  reconstructed: 1 report, 14 encounters, 31 actors, 31 participants
  persisted through 0007: 77 observations

combatants:
  persisted through 0008: 1343 observations
  actor/build observations: 1339
  linked actors: 11
  integrity checks: 14/14

public manifest:
  reports: 6454
  unique report IDs: 6454
  integrity checks: 19/19

identity decision:
  integrity checks: 16/16
  guild identity verified: true

verified guild report manifest:
  selected reports: 17
  unique selected IDs: 17
  integrity checks: 14/14

full-crawl contract:
  integrity checks: 12/12
  contract reviewed: true
  bounded route-semantics capture allowed: true
  full crawl allowed: false
```

Versioned receipts:

```text
evidence/real-data/argentum-public-report-manifest.json
evidence/real-data/argentum-guild-identity-decision.json
evidence/real-data/argentum-guild-report-manifest.json
evidence/real-data/argentum-guild-full-crawl-contract.json
```

## Current boundary

```text
guild identity verified: true
guild filtering completed: true
guild report manifest deduplicated: true
full crawl collection contract reviewed: true
ready for bounded route-semantics capture: true
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Current nearest task

Perform **bounded guild API route-semantics capture** under the reviewed contract.

Required work:

1. Use only observed route candidates.
2. Record exact route template and query parameters.
3. Archive complete raw responses before interpretation.
4. Compute payload SHA-256 and schema fingerprint.
5. Inventory response collection shape, fields, types and nullability.
6. Inventory pagination fields without assigning unobserved meaning.
7. Verify deterministic termination and completeness before full-crawl promotion.
8. Compare any future API report set with the private verified 17-report baseline.
9. Partition differences into matching, missing, extra and conflicting reports.
10. Preserve failed requests and contradicting evidence.
11. Keep full crawl, graph, performance and scoring false.

Observed route shapes remain candidates:

```text
/api/guilds/progression
/api/guilds/search?q=<value>
/api/guilds/search?q=<value>&limit=<value>
```

Do not repeat pagination, public manifest, identity decision, filtering or contract review unless a bound hash changes.

## Following sequence

```text
bounded route-semantics capture
-> explicit route-semantics decision
-> deterministic API-versus-baseline report-set comparison
-> full-crawl promotion only if evidence passes
-> per-report report/encounter/combatants capture
-> multi-report character identity graph
-> 30-40 unique candidate characters
-> performance observations
-> global benchmark corpus
-> confidence-aware player scoring
-> constrained BiS 25 optimizer
```

## CI note

Run #476 reported 303 passed but failed Ubuntu only on a formatting defect that was corrected. All later HEADs require fresh verification. Never claim green status from old runs.

## Жёсткие ограничения

- Не придумывать routes, parameters, fields, IDs или pagination rules.
- Не считать route candidate подтверждённой semantics.
- Не считать nickname/name достаточным identity key.
- Не использовать observed/candidate data в planner scoring.
- Не изменять опубликованные migrations.
- Не коммитить raw payloads, source guild IDs, report IDs, private manifests, private decisions, checkpoints, DuckDB, cookies, tokens или browser profiles.
- Не заявлять тесты или CI без фактической проверки.
- Не путать parser verification, identity verification, filtering или contract review с gameplay semantics.
- Не игнорировать contradicting evidence.
- GitHub-действия выполнять через connector.
- Пользователю давать один PowerShell-блок только для действий, невозможных через GitHub.