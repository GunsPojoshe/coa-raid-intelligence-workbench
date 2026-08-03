# Real-data evidence checkpoint

Дата актуализации: **2026-08-04**.

Каталог содержит versioned scalar-free receipts и trust boundaries. Private payloads, source rows, queries, raw JavaScript contexts, private receipts and DuckDB remain local-only.

## Major versioned artifacts

```text
observed-combatants-info-candidate-extraction.json
observed-combatants-info-candidate-promotion.json
observed-combatants-info-persistence.json
argentum-report-pagination-limit-promotion.json
argentum-public-report-manifest.json
argentum-guild-identity-decision.json
argentum-guild-report-manifest.json
argentum-guild-full-crawl-contract.json
argentum-guild-asset-profiled-recovery.json
argentum-guild-route-semantics-capture.json
argentum-guild-route-semantics-review.json
argentum-guild-limit-semantics-capture.json
argentum-guild-limit-semantics-review.json
```

Incomplete/failed receipts remain classified evidence, not successful semantic decisions.

## Public-report, identity and filtering baseline

```text
public reports: 6454
unique report IDs: 6454
public-manifest checks: 19/19
exact Argentum label reports: 17
identity-decision checks: 16/16
guild identity verified: true
filtered reports: 17
filter checks: 14/14
```

Private 17-report set is the comparison baseline. Source guild ID and report IDs are not published.

## Guild-search route and limit evidence

```text
route: /api/guilds/search
response envelope: guilds, success
guild fields: id, name, realm, report_count
route review checks: 22/22

limit capture SHA-256:
690d7d93d5e9c592877a4fa049d2638b0a5a523430f9205777ce4fa06e624e58
attempts: 3
completed: 3
result counts: 1 / 7 / 7
capture checks: 15/15
review checks: 30/30
limit truncation semantics verified: true
```

This verifies stable truncation of guild-search results. It does not verify guild-report pagination or full-crawl completeness.

## Recovered SPA asset route candidates

```text
receipt: argentum-guild-asset-profiled-recovery.json
asset download completed: true
HTTP 200: true
asset bytes: 3881146
integrity checks: 15/15
all API candidates: 79
guild candidates: 3
```

```text
/api/guilds/progression
/api/guilds/search?q=<value>
/api/guilds/search?q=<value>&limit=<value>
```

The search routes are reviewed. `/api/guilds/progression` is only a lexical candidate; its method, request shape, response schema and relation to report membership are unresolved.

## Offline progression usage inventory

Implemented files:

```text
src/coa_workbench/collector/guild_progression_usage_inventory.py
scripts/inventory_guild_progression_usage.py
tests/unit/test_guild_progression_usage_inventory.py
```

It validates the versioned public recovery, exact private recovery hash and archived asset payload hash. Raw usage snippets remain private. Public output contains only:

```text
occurrence count
context hashes
call-style candidates
HTTP method candidates
query-construction markers
boolean readiness/boundary flags
```

Expected public output after local execution:

```text
data/exchange/out/argentum-guild-progression-usage-context.json
```

A successful inventory may set only:

```text
ready_for_guild_progression_usage_review: true
```

It must keep these false:

```text
ready_for_bounded_progression_route_probe
progression route semantics verified
pagination semantics verified
termination semantics verified
completeness verified
automatic full guild crawl allowed
ready for full guild crawl
planner scoring allowed
```

## Next evidence sequence

```text
offline SPA usage-context inventory
-> explicit usage-context review
-> bounded progression route probe only after exact method/request review
-> response schema review
-> pagination/termination/completeness evidence
-> API-versus-private-baseline set comparison
-> explicit full-crawl promotion
```

## Local-only artifacts

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never commit credentials, cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR, source guild IDs, report IDs, private query values, private recovery receipts or raw JavaScript contexts.
