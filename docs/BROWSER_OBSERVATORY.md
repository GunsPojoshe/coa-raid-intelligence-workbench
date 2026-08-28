# Browser Observatory — fallback discovery tool

Status date: **2026-08-26**.

Historical branch:

```text
e4/interactive-har-discovery
```

The branch name reflects how E4 started. Browser Observatory is **not** the current default acquisition model for Ascension Logs.

## Current role

Use Browser Observatory only after stronger sources fail to answer the exact unresolved question:

```text
official public API
-> official site semantics
-> pinned executable Companion source
-> existing persisted first-party evidence
-> Browser Observatory / manual HAR for the remaining gap
```

It remains valuable as reusable provider-neutral infrastructure.

## Implemented components

```text
src/coa_workbench/collector/network_observation.py
src/coa_workbench/collector/har_observation_source.py
src/coa_workbench/collector/interaction_session.py
src/coa_workbench/collector/interaction_differential.py
src/coa_workbench/collector/browser_observatory.py
src/coa_workbench/collector/discovery_scenarios.py
scripts/run_browser_observatory.py
scripts/review_interaction_session.py
scripts/build_discovery_coverage.py
config/browser_discovery_scenarios.yaml
```

The provider-neutral model records private request details locally and exposes scalar-safe route/key/shape structure for review.

## Evidence meaning

A repeated action/request burst can prove a stable structural relation. It does **not** automatically prove gameplay semantics or promote a source contract.

```text
UI label != request semantic proof
repeated burst != mechanic proof
network-silent action = valid observation
```

## Privacy boundary

Private state may include:

```text
data/private/browser-observatory/browser-profile/
data/private/browser-observatory/sessions/
HAR
trace
private action manifest
private screenshots
```

Never publish report/player/guild IDs, query/body values, cookies, Authorization values, browser profiles or raw HAR/trace material.

## Access/compliance boundary

Do not add or recommend automation intended to bypass source controls:

```text
stealth Chromium patches
fingerprint/UA spoofing for evasion
challenge solving
proxy rotation to evade rate/automation controls
anti-bot bypass
```

If live browser automation is unreliable or not appropriate for a source, prefer documented API/source evidence or an operator-authorized manual browser observation rather than making the browser less detectable.

## Current Ascension Logs decision

The official public API now covers the active population-statistics gate. Therefore no Playwright/HAR session is required for current `/statistics` normalization/persistence.

The historical Browser Observatory difficulty experiment is retained as project history. The two-report difficulty gate remains unresolved, but there is no requirement to restart browser discovery until a concrete product decision depends on that exact missing relation.

## Promotion rule

Only merge/promote:

```text
provider-neutral observation/review code
reviewed source contracts
focused deterministic tests
scalar-safe receipts
documentation
```

Never promote raw browser state, one-session UI guesses or unverified mechanics.
