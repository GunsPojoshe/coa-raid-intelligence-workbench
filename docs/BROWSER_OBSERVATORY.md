# Browser Observatory — E4 accelerated discovery

Status date: **2026-08-19**.

Branch:

```text
e4/interactive-har-discovery
```

PR:

```text
#9 -> e3/real-log-capture
```

This is the current E4 operating document. `INTERACTIVE_HAR_DISCOVERY.md` now describes the legacy/fallback HAR path only.

## Purpose

E4 accelerates source discovery without weakening the E3 evidence boundary.

The acquisition model is now:

```text
headed dedicated browser
-> explicit operator actions
-> live same-origin fetch/xhr observations
-> private HAR + trace + action manifest
-> provider-neutral NetworkObservation
-> action/network windows
-> intrinsic request-burst signatures
-> negative-control comparison
-> scenario coverage
-> scalar-safe public receipt
```

HAR remains a forensic/replay/fallback input. Manual DevTools HAR export is no longer the default workflow.

## Stable inherited core

Browser Observatory feeds, rather than replaces:

```text
RawArchive
Source Registry / reviewed contracts
schema/profile/scope observation
provenance
change registry
artifact dependencies
scoped reanalysis
public/private boundary
fail-closed mechanic/planner trust
```

No Browser Observatory result automatically becomes a canonical source contract or gameplay semantic claim.

## Current implementation

Provider-neutral network layer:

```text
src/coa_workbench/collector/network_observation.py
src/coa_workbench/collector/har_observation_source.py
```

Interaction correlation:

```text
src/coa_workbench/collector/interaction_session.py
src/coa_workbench/collector/interaction_differential.py
```

Live browser acquisition:

```text
src/coa_workbench/collector/browser_observatory.py
scripts/run_browser_observatory.py
```

Scenario coverage:

```text
src/coa_workbench/collector/discovery_scenarios.py
config/browser_discovery_scenarios.yaml
scripts/build_discovery_coverage.py
```

Manual HAR fallback/replay:

```text
scripts/review_interaction_session.py
```

## Private workspace

Dedicated browser state and raw capture are local-only:

```text
data/private/browser-observatory/
  browser-profile/
  sessions/
    <session>/
      network.har
      trace.zip
      actions-private.json
```

Public-safe local handoff receipts are written under:

```text
data/exchange/out/
```

The normal operator Chrome/Firefox profile must not be used. The project profile may contain authentication state and must never be published or included in a normal handoff archive.

## Runtime dependency strategy

Playwright is intentionally not a mandatory project dependency yet. Normal CI and the application remain usable without it.

Use an ephemeral uv overlay:

```powershell
uv run --with "playwright>=1.61,<2" playwright install chromium
```

Then invoke Browser Observatory with the same overlay:

```powershell
uv run --with "playwright>=1.61,<2" python scripts/run_browser_observatory.py ...
```

This leaves `pyproject.toml` and `uv.lock` unchanged during E4 validation.

## One-time profile bootstrap

If the site requires login, initialize the dedicated profile without collecting evidence:

```powershell
uv run --with "playwright>=1.61,<2" python scripts/run_browser_observatory.py `
  --start-url "<PRIVATE_START_URL>" `
  --scenario-code report.difficulty `
  --bootstrap-profile
```

Authenticate if needed, then return to the terminal and press `Ctrl+C`.

Bootstrap records:

```text
profile_bootstrap_completed = true
evidence_capture_performed = false
```

Login traffic is therefore not mixed with the later evidence session.

## Evidence session

First real E4 scenario:

```powershell
uv run --with "playwright>=1.61,<2" python scripts/run_browser_observatory.py `
  --start-url "<PRIVATE_REPORT_URL>" `
  --scenario-code report.difficulty
```

Use the browser normally. The Python process pumps Playwright events while the session is active. End the session with `Ctrl+C` in the terminal.

Do not paste or commit the private report URL.

## Recommended first scenario: report.difficulty

Goal: establish whether repeated difficulty control transitions have a stable browser/network signature.

Operate one factor at a time. A useful sequence is:

```text
baseline report load
-> change difficulty
-> select boss / encounter
-> return to the same difficulty control
-> change difficulty again
-> exercise a neighbouring unrelated control
-> repeat difficulty change if practical
```

Exact UI labels are not trusted semantics. The important properties are:

```text
same physical control is exercised repeatedly
unrelated controls provide negative controls
private scalar values may vary
public review exposes only key names / route shapes / structural evidence
```

A network-silent action is a valid result.

## Capture boundary

For accepted same-origin API traffic:

```text
HTTPS exact host only
/api/ prefix by default
fetch/xhr only
request method and concrete URL privately
request body privately
response status/body privately
resource type
timestamps
```

The scalar-safe model publishes only safe structural information such as:

```text
method
normalized route shape
query key names
request-body key names
response structural fingerprint
network-silent state
session control codes
```

Concrete IDs, query values, body values, private labels, cookies and headers are not copied into the public review.

## Action identity

The injected browser observer assigns one session-local public-safe control code to the same private DOM identity:

```text
control_001
control_002
...
```

The actual DOM identity, page URL and UI label remain in the private action manifest.

## Corroboration model

Adjacent-state deltas remain useful diagnostics, but they are not the repetition identity.

Corroboration uses the intrinsic network burst generated by the current action:

```text
same control group
+ same intrinsic request-burst structure repeated >= 2
+ signature is not produced by neighbouring negative-control groups
+ when relevant, private scalar variation is observed across the repeated burst
```

Scalar variation is published only as safe metadata:

```text
query key name varied
request-body key name varied
dynamic path segment index varied
```

The values themselves remain private. This proves a repeatable structural relation, not domain/gameplay semantics.

## Scenario manifest

Ascension Logs E4 currently declares:

```text
reports.discovery
report.overview
report.difficulty
report.encounters
report.roster
report.throughput
report.damage_taken
report.healing
report.subpages
characters.discovery
guild.discovery
guild.progression
rankings.discovery
statistics.discovery
```

The manifest is source-specific:

```text
source_code = coa_ascension_logs
```

Armory, talent-grid and BisBeard must use their own source manifests/hosts later. They may reuse the Browser Observatory engine, but cannot satisfy Ascension Logs coverage.

## Coverage states

Build local coverage from Browser Observatory public receipts:

```powershell
uv run --no-sync python scripts/build_discovery_coverage.py
```

Possible states:

```text
unobserved
observed
repeatable_structure
scalar_variation_observed
```

These are evidence states only:

```text
coverage_is_semantic_proof = false
coverage_is_completion_percentage = false
```

Unknown, unassigned, invalid and foreign-source sessions remain visible instead of being silently treated as covered.

## Outputs

Private:

```text
data/private/browser-observatory/sessions/<session>/network.har
data/private/browser-observatory/sessions/<session>/trace.zip
data/private/browser-observatory/sessions/<session>/actions-private.json
```

Scalar-safe local handoff:

```text
data/exchange/out/coa-browser-observatory-<session>.json
```

Coverage:

```text
data/exchange/out/coa-browser-discovery-coverage.json
```

The normal chat handoff should prefer the scalar-safe receipt. Raw HAR/trace/private action data is requested only when a structural question genuinely cannot be resolved from the safe receipt or existing local corpus.

## Promotion back to E3

Potential merge candidates:

```text
provider-neutral observation/review code
confirmed reviewed source contracts
confirmed response-profile rules
focused deterministic tests
scalar-safe real receipts
documentation
```

Do not merge:

```text
browser profile
raw HAR
trace
private action manifest
private screenshots
private IDs/names/query/body values
one-session UI-label guesses
unverified gameplay mechanics
```

## Current next gate

The implementation is ready for the first real private Browser Observatory session.

```text
run report.difficulty real session
-> inspect scalar-safe interaction receipt
-> build/update discovery coverage
-> if repeatable structural candidates exist:
     inspect private local evidence only for the exact unresolved relation
     promote only reviewed deterministic contract knowledge
-> if no stable network relation:
     record network-silent or ambiguous result
     do not invent a contract
```

No additional one-off HAR helper should be created before this real run.
