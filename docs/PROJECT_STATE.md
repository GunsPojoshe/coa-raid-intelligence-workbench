# Фактическое состояние проекта

Дата актуализации: **2026-08-13**.

## GitHub

Active branches:

```text
main
e2/log-evidence-refactor
e3/real-log-capture
```

Obsolete cleanup/Codex/E0/E1/E3-stage branches removed 2026-08-13.

PR #7 remains Draft: `e3/real-log-capture -> e2/log-evidence-refactor`.

Last fully verified checkpoint before the current progression-contract commits:

```text
HEAD: 005c6cbf017f7bea7c3b0b0554e05381dc4679f5
Verify repository #615: success
public-release-audit: success
ubuntu: success
windows: success
```

Newer HEAD/CI must always be checked live.

## Major progression finding

The local handoff included the exact private recovery metadata and exact archived SPA payload:

```text
SHA-256: da381a27e44be6cad3f60c4326251c7cbdd1ea8b31c5ccd5d8be03331855dacc
```

Direct analysis established that the exact literal:

```text
/api/guilds/progression
```

occurs as a `noCacheEndpoints` configuration value and has **zero direct request occurrences**.

Actual direct progression contracts:

```text
GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

Four direct frontend calls were observed, all GET. No direct POST progression request was observed.

Therefore the old helper-definition/reference/owner chain is retained as audit history but is superseded for choosing the progression HTTP contract.

## New versioned contract stage

Added to the active branch:

```text
src/coa_workbench/collector/guild_progression_frontend_contract.py
tests/unit/test_guild_progression_frontend_contract.py
evidence/real-data/argentum-guild-progression-frontend-request-contract.json
```

The review is offline-only and binds its public result to the exact archived SPA/private recovery evidence. The receipt publishes route templates and parameter-key names, not raw JavaScript/private source values.

Decision:

```text
legacy exact-prefix probe allowed: false
bounded rankings GET contract observed: true
bounded rankings GET probe ready: true
network requests performed by review: false
```

## User's current Windows working tree

The user's checkout still contains the older uncommitted lexical/helper repair from the mistaken route path. It is no longer on the critical product path.

Do not commit that repair automatically. After the current remote contract checkpoint is green, remove only those obsolete local code changes with one bounded local operation, preserve private/raw evidence, and fast-forward to the remote branch.

## Next action

After exact-head CI for the current contract stage is green:

```text
clean obsolete local helper-repair diff
-> sync local checkout
-> perform one bounded GET /api/guilds/progression/rankings using no invented query values
-> archive exact response
-> review schema/fingerprint
-> establish pagination/termination evidence before expanding collection
```

No request to the exact legacy `/api/guilds/progression` prefix. No guessed POST. No further broad helper/owner/alias diagnostics are required before the bounded rankings GET.

## Development process

- Agent performs all GitHub work available to it.
- User participates only at inaccessible local Windows/private runtime boundaries.
- Private/raw artifacts may be inspected for analysis; publication/versioning is a separate boundary.
- Focused tests during iteration; one aggregate verifier before a meaningful push; exact-head CI afterward.
- Prefer one coherent product change over process-driven micro-stages.
