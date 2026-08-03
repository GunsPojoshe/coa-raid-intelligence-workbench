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
5. Прочитай полностью `AGENTS.md`, canonical docs и `evidence/real-data/README.md`.
6. Сверь документацию с кодом, migrations, versioned receipts и CI.
7. Не доверяй старым HEAD, CI run, test count, hashes, routes или source counts без проверки.

## Главная цель и trust boundary

```text
source response
-> immutable raw archive
-> SHA-256 and schema fingerprint
-> reviewed mapping/extractor
-> deterministic normalization/extraction
-> immutable observations
-> supporting and contradicting evidence
-> corroborated or confirmed mechanic
-> explainable planner scoring
```

Combat-log event является observation, а не доказательством общей mechanic. Parser correctness, identity verification, filtering, collection contract review and route/schema review do not confirm gameplay semantics. Planner scoring разрешён только для `corroborated` и `confirmed`.

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

identity/filtering:
  identity checks: 16/16
  guild identity verified: true
  selected reports: 17
  unique selected IDs: 17
  filter checks: 14/14

full-crawl contract:
  integrity checks: 12/12
  contract reviewed: true

route capture:
  attempts: 3
  HTTP 200: 3
  capture checks: 13/13
  observed result counts: [1]

route/schema review:
  integrity checks: 22/22
  route template verified: true
  query shapes verified: true
  response schema verified: true
  limit parameter accepted: true
  ready for bounded limit-semantics capture: true
```

Versioned receipts:

```text
evidence/real-data/argentum-public-report-manifest.json
evidence/real-data/argentum-guild-identity-decision.json
evidence/real-data/argentum-guild-report-manifest.json
evidence/real-data/argentum-guild-full-crawl-contract.json
evidence/real-data/argentum-guild-route-semantics-capture.json
evidence/real-data/argentum-guild-route-semantics-review.json
```

## Current boundary

```text
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

## Current nearest task

Design and execute a **bounded multi-result guild-search limit-semantics capture**.

Required work:

1. Use only the verified `/api/guilds/search` route template.
2. Choose a privacy-safe query expected to return multiple records.
3. Compare at least two accepted `limit` values.
4. Archive complete raw responses before interpretation.
5. Compute payload SHA-256 and schema fingerprint.
6. Preserve ordered-record-set and source-ID-set hashes.
7. Publish only scalar-free counts, hashes and field inventories.
8. Verify truncation behavior without assigning pagination, termination or completeness semantics.
9. Preserve failed requests and contradicting evidence.
10. Keep full crawl, graph, performance and scoring false.

A one-result response cannot verify limit truncation semantics.

## Following sequence

```text
bounded multi-result limit probe
-> explicit limit-semantics review
-> pagination semantics review
-> termination/completeness review
-> deterministic API-versus-private-17-report-baseline comparison
-> explicit full-crawl promotion only if all gates pass
-> per-report capture
-> multi-report character graph
-> performance corpus
-> constrained BiS 25 optimizer
```

Do not repeat pagination, public manifest, identity decision, filtering, contract review or route/schema review unless a bound hash changes.

## Жёсткие ограничения

- Не придумывать routes, parameters, fields, IDs или pagination rules.
- Не считать accepted parameter доказательством его truncation semantics.
- Не считать nickname/name достаточным identity key.
- Не использовать observed/candidate data в planner scoring.
- Не изменять опубликованные migrations.
- Не коммитить raw payloads, source guild IDs, report IDs, private manifests, private decisions, checkpoints, DuckDB, cookies, tokens или browser profiles.
- Не заявлять тесты или CI без фактической проверки.
- Не игнорировать contradicting evidence.
- GitHub-действия выполнять через connector.
- Пользователю давать один PowerShell-блок только для действий, невозможных через GitHub.
