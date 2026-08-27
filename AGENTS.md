# CoA Raid Intelligence — Agent Instructions

These instructions apply to the whole repository.

## Mission

Build a localhost-first, evidence-first system **only for Conquest of Azeroth** that can eventually explain:

> Why is this specific player needed by this exact current roster?

Planner scoring is fail-closed. Only separately corroborated mechanics and reviewed analytical semantics may enter canonical recommendations.

## Documentation authority

Before substantial work read:

```text
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
```

Dated milestone/experiment documents are history unless the documentation index explicitly marks them current.

## Responsibility split

Use connected tooling for GitHub repository/branch/PR/CI inspection, source/config/migration/evidence review, documentation and safe repository changes. Ask the operator only for the exact local/private Windows boundary that remote tooling cannot see.

Private/raw files are valid analysis inputs. Privacy constrains publication/versioning, not private deterministic processing.

## Source priority

```text
1. official documented CoA Ascension Logs public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API responses
5. narrow browser/network observation for undocumented gaps
6. structural inference only after stronger sources are exhausted
```

Do not use Browser Observatory/HAR to rediscover an already documented contract.

## Official public API lane

Reviewed source:

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

Experimental/on-request `events:read` is separate and must not be assumed available.

Default credential file:

```text
data/private/coa-logs-api-key.txt
```

The API key must never enter Git, RawArchive metadata, query strings, CLI values, logs, screenshots, public receipts or public hashes.

Exact `/statistics` request dimension values may be retained only in ignored/private RawArchive observation metadata because the normalizer must prove its request scope. Never publish those values or low-entropy hashes of them.

Current real aggregate state:

```text
provenance-aware capture: proven
exact normalization: proven
DuckDB persistence: proven
second-pass idempotence: proven
population-prior read model: proven
Source Observatory/Health integration: current gate
planner scoring: blocked
```

Do not repeat the already completed capture/persistence proof merely because a session restarted.

## Source Observatory lane

The generic evidence loop is:

```text
reviewed contract
-> immutable RawArchive
-> acquisition observation
-> schema/profile/scope observation
-> source change event
-> artifact dependency
-> scoped reanalysis
-> deterministic analysis
-> Source & Analysis Health
```

For official `/statistics`, request dimensions are schema-profile keys: source-shape comparison must occur only within a compatible private request scope. The aggregate artifact depends on both the exact `raw_object` and logical `source_endpoint=public_api_statistics`, so future compatible endpoint changes can target it for reanalysis.

Generic dynamic-template ingestion is prohibited. Unknown semantics stay unknown.

## Historical report lane

The E3 report pipeline remains canonical for report-specific evidence. Historical two-report difficulty equivalence remains `insufficient_evidence`; do not manufacture a v4 heuristic or perform blocked numeric comparison.

## Upstream source lane

Pinned executable source:

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Executable code can establish client behavior and emitted structure. Comments/backend claims remain hypotheses until independently corroborated.

## Browser/HAR fallback

Use only for a specific unresolved gap after stronger sources are exhausted. Do not implement or advise stealth, fingerprint spoofing, challenge solving, proxy rotation for evasion or anti-bot bypass.

## Local workspace safety

Never:

```text
git clean unknown state
reset/checkout to destroy untracked files
recursively delete ignored/private trees
stage data/private, raw HAR, raw payloads or secrets
```

For exact local inventory:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

The historical local helper patch is already classified as valuable incomplete WIP; preserve it privately and do not apply it as-is.

## Branch topology

```text
main
└── e2/log-evidence-refactor        Draft PR #3
    └── e3/real-log-capture         Draft PR #7
        └── e4/interactive-har-discovery  Draft PR #9
```

Always inspect live mergeability. Resolve lower-chain integration debt deliberately; do not merge Draft PRs merely to clear warnings.

Never rewrite published migrations.

## Verification

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
