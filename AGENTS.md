# CoA Raid Intelligence — repository instructions

These rules apply to the whole repository.

## Mission

Build a localhost-first **Raid Leader Companion for Conquest of Azeroth** that combines roster state, verified player/build observations, encounter evidence and population context into explainable raid-leading decisions.

The product owns its analytical model. External sites and APIs are evidence sources, not the product architecture.

## Read first

Before substantial work read:

```text
README.md
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
```

Dated experiments and old branch handoffs are history; they are not operating instructions.

## Truth model

Never promote automatically:

```text
field name -> gameplay meaning
UI label -> backend contract
character name -> cross-report identity
one report -> universal mechanic
population metric -> player capability
population metric -> planner recommendation
```

Planner scoring is fail-closed.

## Source priority

```text
1. official documented CoA Ascension Logs public API
2. official documented semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API observations
5. narrow browser/network observation for an exact undocumented gap
6. structural inference only after stronger sources are exhausted
```

Do not use Browser Observatory/HAR to rediscover a documented public contract.

## Official public API

Reviewed base:

```text
https://coa.ascensionlogs.gg/api/public/v1
```

Self-service `stats:read`:

```text
GET /phases
GET /bosses
GET /statistics
```

The contract also documents experimental/on-request `events:read` report/actor/event routes. Treat scope availability as a runtime capability; never assume it from documentation alone.

Credential boundary:

```text
data/private/coa-logs-api-key.txt
fallback: COA_LOGS_API_KEY
```

The API key must never enter Git, request URLs, RawArchive metadata, public receipts, logs, screenshots or hashes.

## Evidence architecture

```text
reviewed contract
-> immutable RawArchive
-> acquisition observation
-> schema/profile/scope observation
-> deterministic normalization
-> provenance + dependency tracking
-> source change detection
-> scoped reanalysis
-> reproducible analytics
-> Source & Analysis Health
```

Private/raw files are valid local analysis inputs. Privacy constrains publication, not deterministic local processing.

## Local workspace safety

Never destroy unknown operator state with `git clean`, recursive ignored-tree deletion or reset/checkout commands that discard untracked files.

Private paths remain ignored, including `data/private`, RawArchive, DuckDB, HAR/browser state, exchange outputs and artifacts.

For a local inventory:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

## Migrations

Migrations are forward-only. Never rewrite a published migration. Current tracked series is `0001` through `0013`.

## Branch model

`main` is the canonical integrated branch. Use short-lived feature branches and PRs for coherent changes. Do not maintain stacked long-lived stage branches as project state.

Always verify the exact pushed HEAD before merge or publication.

## Verification

```text
focused tests
-> coherent commit
-> uv run --no-sync python scripts/verify_repo.py
-> exact-head GitHub CI
```

Required CI jobs:

```text
public-release-audit
ubuntu
windows
```
