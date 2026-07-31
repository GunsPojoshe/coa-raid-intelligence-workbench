# Стартовый PROMPT для продолжения CoA Raid Intelligence Workbench

Ты продолжаешь разработку проекта **CoA Raid Intelligence Workbench**.

## Обязательный порядок начала

1. Проверь repository `GunsPojoshe/coa-raid-intelligence-workbench`.
2. Проверь branch, HEAD и working tree.
3. Проверь PR #7, его base и PR #3.
4. Проверь latest GitHub Actions run и exact failures.
5. Прочитай полностью:
   - `AGENTS.md`;
   - `docs/PROJECT_MASTER_CONTEXT.md`;
   - `docs/PROJECT_STATE.md`;
   - `docs/REAL_LOG_CAPTURE.md`;
   - `docs/GUILD_WIDE_COLLECTION_CONTRACT.md`;
   - `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md`;
   - `evidence/real-data/README.md`.
6. Сверь claims с кодом и versioned receipts.
7. Не доверяй старым HEAD/test counts без проверки.

## Branch chain

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Green baseline перед documentation refresh:

```text
commit: 00bae9ac4deb457eebc41cd50bdff6305bf3fe42
Verify repository run #372
Ubuntu: success
Windows: success
```

Фактический HEAD и CI перепроверить.

## Миссия и trust rules

Build a localhost-first raid planning and evidence system. Combat-log event является observation, а не автоматическим доказательством общей mechanic.

Нельзя придумывать routes, query parameters, JSON fields, pagination behavior, Spell IDs, provider mappings или semantic meaning по display name/label.

Normalization разрешена только для exact reviewed hash/fingerprint и verified mapping/extractor contract. Planner scoring допускает только `corroborated` и `confirmed`. Contradicting evidence сохраняется.

## Privacy and Git

Пользователь разрешает использовать локальный private context для анализа. Это не разрешает коммитить source scalars или secrets.

Versioned:

- code/tests;
- migrations;
- reviewed mappings;
- docs;
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

Never commit cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR or absolute user paths.

## Подтверждённый фундамент

- localhost FastAPI raid planner and DuckDB plans;
- immutable raw archive and retrieval observations;
- JSON/HAR safe tooling;
- verified mapping gates and schema fingerprints;
- canonical parser records and Aura State Engine;
- hypotheses/evidence/trust policies;
- migrations `0001`–`0008`;
- Ubuntu/Windows repository verification;
- verified Armory/public-report/report/encounter mappings;
- normalized, reconstructed and persisted report slice;
- promoted and persisted combatants parser observations;
- combatants parser and actor/build read models;
- promoted `limit=25` pagination contract;
- exhaustive public-report manifest.

## Completed combatants checkpoint

```text
migration: 0008_combatants_observation_persistence
persisted observations: 1343
actor/build observations: 1339
linked actors: 11
integrity checks: 14/14
core actor mutations: 0
```

Receipt:

```text
evidence/real-data/observed-combatants-info-persistence.json
```

Companion-addon provenance, nested semantics, gameplay meaning and planner scoring remain unverified.

## Completed public manifest checkpoint

Receipt:

```text
evidence/real-data/argentum-public-report-manifest.json
```

```text
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

Boundary:

```text
manifest complete: true
guild identity verified: false
ready for guild identity review: true
ready for guild filtering: false
ready for full guild crawl: false
planner scoring allowed: false
```

## Первая bounded задача нового агента

Не повторяй pagination probing, manifest capture или combatants persistence без hash change.

Выполни **local guild identity review**:

1. Validate `evidence/real-data/argentum-public-report-manifest.json`.
2. Load the local private manifest whose SHA-256 equals the receipt binding.
3. Select the 17 rows where normalized `guild_name` exactly equals `Argentum`.
4. Confirm all selected rows have the same non-null source guild ID.
5. Check whether that ID appears with another non-empty guild name in the same exhaustive snapshot.
6. Inspect available independent source identity evidence for the ID.
7. Do not use report title, uploader or nickname as primary identity proof.
8. Produce a scalar-free review receipt containing hashes, counts, conflict flags, reviewer and decision; do not expose the raw guild ID.
9. Keep `guild_identity_verified=false` unless the evidence is sufficient and the manual promotion is explicit.
10. Do not enable guild filtering, crawl or scoring before promotion.

## Following sequence

```text
guild identity review
-> explicit identity promotion
-> deterministic guild filtering
-> guild report manifest
-> per-report capture
-> multi-report character graph
-> aura evidence and intervals
-> supporting/contradicting observations
-> mechanic trust promotion
-> planner integration
```

## Completion gate

PR #7 remains Draft until reviewed guild identity and crawl boundaries, reviewed combatants observations, aura events and reconstructed intervals for the bounded report slice, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows CI.

## Формат отчёта

После каждой задачи сообщай verified facts, local-only observations, outdated claims corrected, files/migrations changed, exact tests/commands, CI state, remaining boundaries, and the next bounded task.

Не называй parser correctness или mapping/persistence подтверждённой gameplay mechanic.
