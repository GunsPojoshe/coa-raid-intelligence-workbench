# CoA Raid Intelligence Workbench

Localhost-first, evidence-first raid intelligence for **Ascension WoW / Conquest of Azeroth**.

Primary product question:

> **Почему конкретный человек нужен именно текущему составу?**

The project is not a DPS-ranking scraper. Every important conclusion must preserve provenance from source observation through reviewed transformation to the analytical claim.

## Current workstream

```text
e3/real-log-capture
  stable report-evidence baseline

e4/interactive-har-discovery
  active official-API / upstream-evidence workstream
  Draft PR #9 -> e3/real-log-capture
```

The E4 branch name is historical. Browser Observatory/HAR is now a fallback tool.

## Source priority

```text
1. official documented CoA Ascension Logs public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API responses
5. narrow browser/network observation for undocumented gaps
6. structural inference only after stronger sources are exhausted
```

See `docs/CURRENT_PARADIGM.md` and `docs/DOCUMENTATION_INDEX.md`.

## Official aggregate API — real proven state

Reviewed self-service `stats:read` routes:

```text
GET /phases
GET /bosses
GET /statistics
```

Real scalar-safe evidence proves:

```text
phase records:                         3
active/current phase candidates:       1
boss records:                         285
unique stable boss_id values:         285
provenance-aware /statistics:    HTTP 200, archived
response bytes:                     21306
normalized classes:                   21
normalized specs:                     62
percentile scalar values normalized: 806
second-pass replay:            idempotent
population-prior records:              62
records with local_parse_share:        62
Source Observatory integration:    proven
profile-scoped dependency:         proven
legacy broad endpoint dependency: inactive
pending reanalysis after migration:    0
```

The real two-pass persistence proof inserted 21 class rows and 62 spec rows on the first pass, then matched all 21/62 with zero new rows on the second pass.

The later no-network replay also proved that the aggregate artifact can migrate from the old broad endpoint dependency to a private query-profile dependency without back-triggering the historical informational baseline event.

Canonical real receipts:

```text
evidence/real-data/coa-public-api-catalog-real.json
evidence/real-data/coa-public-api-statistics-capture-real.json
evidence/real-data/coa-public-api-statistics-shape-real.json
evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
evidence/real-data/coa-public-api-statistics-persistence-real.json
evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json
```

They do not publish query values, class/spec names, difficulty/phase scalars, metric values, raw IDs, profile fingerprints or API credentials.

## Aggregate implementation

```text
exact fail-closed StatisticsResponse parser
private request-scope provenance for new captures
migration 0013_public_api_statistics
DuckDB batch/class/spec persistence
analysis_run provenance
raw-object artifact dependency
private source-endpoint-profile artifact dependency
profile-scoped reanalysis resolver
population-prior read model over documented dimensions
Source Observatory replay from the existing RawArchive
scalar-safe Source & Analysis Health review
```

Request dimensions partition schema baselines through private schema-profile keys so different `/statistics` scopes are not compared as if they were the same contract instance. Profile-local source changes target only matching artifacts. A `request_contract_changed` event remains endpoint-global by design.

## Population-prior boundary

`public_api_population_prior_v1` preserves the documented aggregates and derives:

```text
local_parse_share = spec total_parses / sum(spec total_parses in the same batch)
```

This is descriptive participation within one explicit API scope. It is **not** the site's Tier List score, a gameplay capability score or a planner score.

Planner scoring remains blocked.

## Bounded population coverage v1

The next operator gate expands the proven single aggregate profile into a deliberately small multi-profile population context.

Implementation:

```text
src/coa_workbench/analytics/public_api_population_coverage.py
scripts/capture_public_api_population_coverage.py
```

Properties:

```text
4 required bounded slices
3 documented metric families represented
3 role-qualified slices + 1 role-omitted slice
current phase selected privately from archived /phases
existing matching persisted slices are reused
network requests are made only for missing slices
first incomplete capture stops the run
successful slices are archived, observed, normalized and persisted twice
profile-scoped reanalysis is reconciled after the run
boss/location/week/realm/class/spec expansion is excluded from v1
bulk dataset mode = false
```

The public coverage receipt contains only counts/booleans and never the selected phase, difficulty, metric, role, class/spec names, profile fingerprints or source metric values.

## Local API key and private request provenance

Default private key file:

```text
data/private/coa-logs-api-key.txt
```

The key must never enter Git, request URLs, RawArchive metadata, CLI values, logs, screenshots or public receipts.

Exact prepared `/statistics` query values are different from credentials. They are retained only in ignored/private RawArchive observation metadata because exact request scope is required for reproducible normalization. They are excluded from public receipts and Git evidence.

## Current operator workflow

The completed single-profile replay remains available and requires no network:

```powershell
uv run --no-sync python scripts/persist_public_api_statistics.py
```

For the current bounded multi-profile gate use:

```powershell
uv run --no-sync python scripts/capture_public_api_population_coverage.py
```

This command is resumable: already persisted matching slices are skipped, so rerunning it after a transport failure does not intentionally recapture completed coverage profiles.

It writes a scalar-safe receipt to:

```text
data/exchange/out/coa-public-api-population-coverage-review.json
```

## Verification

Python requirement: **3.12+**.

```powershell
uv sync --frozen --extra dev --no-build-package ruff
uv run --no-sync python scripts/verify_repo.py
```

Required exact-head CI jobs:

```text
public-release-audit
ubuntu
windows
```

## Historical report lane

The E3 report pipeline remains the report-specific evidence path. Two reports passed the generic persistence/analytics pipeline. Historical two-report difficulty equivalence remains `insufficient_evidence`, therefore numeric comparison of that historical pair remains blocked.

No difficulty-v4 heuristic is planned simply to force an answer.

## Client-source lane

Pinned executable evidence:

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Executable upstream code is strong evidence of client behavior. Comments/backend notes remain hypotheses until corroborated.

## Repository layout

```text
src/coa_workbench/analytics/    deterministic analytics/reviews
src/coa_workbench/collector/    source contracts/acquisition/observability
src/coa_workbench/normalizer/   normalization
src/coa_workbench/planner/      planner layer, trust-gated
src/coa_workbench/storage/      DuckDB persistence/read models
src/coa_workbench/web/          localhost application/API
scripts/                        durable operator/review commands
config/                         reviewed source/mapping configuration
migrations/                     forward-only migrations 0001-0013
tests/                          deterministic coverage
evidence/real-data/             scalar-safe real receipts only
docs/                           current + historical documentation
```

## Local workspace safety

Ignored/untracked RawArchive, DuckDB, API captures and helper artifacts may be authoritative local state. Do not clean or reset them merely to make Git look clean.

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

The historical local helper patch has already been reviewed: preserve it privately and do not apply it as-is.

## Trust boundary

Do not infer mechanics from field names, UI labels, talent/item names or one combat result. Do not equate character name with cross-report identity. Do not expose private source scalars through public receipts or low-entropy hashes.

Population aggregates are now real-proven through capture, normalization, persistence, source health and profile-scoped invalidation. That still does **not** unlock planner scoring; identity, mechanic, encounter-requirement and composition reasoning remain separate evidence gates.

## Documentation

Start with:

```text
AGENTS.md
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
docs/CONTINUATION_PROMPT.md
```

Dated experiments are historical evidence and do not override the canonical documents above.
