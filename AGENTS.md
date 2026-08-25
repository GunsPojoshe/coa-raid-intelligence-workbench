# CoA Raid Intelligence — Agent Instructions

These instructions apply to the whole repository.

## Mission

Build a localhost-first, evidence-first raid intelligence system **only for Conquest of Azeroth** that can eventually explain:

> Why is this specific player needed by this exact current roster?

Planner scoring is fail-closed. Only separately corroborated/confirmed mechanics and reviewed analytical semantics may enter canonical recommendations.

## Documentation authority

Before continuing substantial work, read:

```text
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
```

Dated milestone/experiment documents are history unless the documentation index explicitly marks them current. Do not restart an old “next gate” from a historical handoff.

## Responsibility split

The agent performs everything available through connected tooling: GitHub repository/branch/PR/CI inspection, source/config/migration/evidence inspection, documentation, and safe repository mutations.

The operator is required only for the exact local Windows/private boundary that remote tooling cannot see. When local work is required, prefer one bounded command/script producing one compact handoff.

Private/raw files are valid analysis inputs. Privacy constrains **publication/versioning**, not private inspection.

## Current source priority

For Ascension Logs questions, prefer the strongest available source:

```text
1. official documented CoA Ascension Logs public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API responses
5. narrow browser/network observation for undocumented gaps
6. structural inference only after stronger sources are exhausted
```

Do not use Browser Observatory/HAR to rediscover a contract already documented by the official API or executable upstream source.

A timestamped source response is an observation, not permanent source semantics.

## Official public API lane

Reviewed contract:

```text
https://coa.ascensionlogs.gg/api/public/v1/openapi.json
source_code = coa_ascension_logs_public_api
```

Self-service `stats:read`:

```text
GET /phases
GET /bosses
GET /statistics
```

Experimental/on-request `events:read` is a separate scope and must not be assumed available.

Default local credential file:

```text
data/private/coa-logs-api-key.txt
```

The API key must never enter Git, RawArchive metadata, query strings, CLI values, logs, screenshots, receipts or hashes intended for publication.

Exact request dimensions are different from credentials. For provenance-aware aggregate captures, exact prepared `/statistics` query values may be stored only in **private ignored RawArchive observation metadata**. They must never be copied to public receipts, Git evidence, screenshots or low-entropy public hashes.

The exact StatisticsResponse parser, migration 0013 persistence and population-prior read model are implemented. The current official-API gate is **one new bounded provenance-aware `/statistics` capture + real two-pass persistence/idempotence proof**. Do not infer a missing historical request dimension from CLI defaults.

## Report / Source Observatory lane

The E3 report pipeline remains canonical for report-specific evidence:

```text
reviewed request contract
-> immutable RawArchive
-> acquisition observation
-> schema/profile/scope observation
-> source change event
-> artifact dependency
-> scoped reanalysis
-> deterministic analytics
-> Source & Analysis Health
```

Generic dynamic-template ingestion is prohibited. Dynamic concrete requests require reviewed/correlated resolution and safe publication boundaries.

The historical two-report difficulty equivalence result remains `insufficient_evidence`. Do not manufacture a v4 heuristic merely to make numeric comparison pass.

## Upstream source lane

Pinned executable source evidence currently includes:

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Executable code can establish client behavior and emitted structure. Comments/backend claims are hypotheses until independently corroborated. Lua identifiers are not gameplay-mechanic proof.

## Browser/HAR fallback

Browser Observatory and manual HAR remain provider-neutral forensic/discovery tools for unresolved gaps.

Do not implement or advise:

```text
stealth/fingerprint spoofing
challenge solving
proxy rotation to evade controls
anti-bot bypass
```

Do not treat a UI label as a backend contract. Repeated UI/network correlation is structural evidence only.

## Local workspace safety

Git is not the whole operational corpus. Ignored/untracked files may be authoritative project state.

Never:

```text
git clean unknown state
reset/checkout to destroy untracked files
recursively delete ignored/private trees
stage data/private, raw HAR, raw payloads or secrets
```

For exact local inventory use:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

The private manifest is `data/private/local-workspace-inventory.json`.

## Branch topology

Active staged integration chain:

```text
main
└── e2/log-evidence-refactor        Draft PR #3
    └── e3/real-log-capture         Draft PR #7
        └── e4/interactive-har-discovery  Draft PR #9
```

Always inspect live mergeability before assuming the chain is clean. Resolve lower-chain debt deliberately; do not merge Draft PRs merely because CI is green.

Never rewrite published migrations.

## Verification

Development cadence:

```text
focused tests
-> coherent change
-> uv run --no-sync python scripts/verify_repo.py
-> push
-> exact-head GitHub CI
```

Required CI jobs:

```text
public-release-audit
ubuntu
windows
```

Never claim a pass without checking the exact pushed HEAD.
