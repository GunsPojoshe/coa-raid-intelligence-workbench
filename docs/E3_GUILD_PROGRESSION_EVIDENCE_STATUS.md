# E3 guild progression evidence status

Дата актуализации: **2026-08-12**.

## Статус checkpoint

```text
scope: Conquest of Azeroth only
branch: e3/real-log-capture
last fully verified code/evidence HEAD: 13982825295737c029b425a37d210a34a7ea0762
last fully verified CI run: #603
run ID: 31533555026
event: pull_request
conclusion: success
public-release-audit: success
ubuntu: success
windows: success
```

Этот документ может быть опубликован отдельным более новым docs-only commit. Новый чат обязан получить current live HEAD.

## Evidence sequence

```text
route discovery
-> usage-context review
-> helper call-site inventory and review
-> helper-definition inventory and review
-> helper-reference inventory and review
-> helper-owner inventory and review
-> exact bounded request contract
-> bounded route probe
-> pagination / termination / completeness review
-> full guild crawl
```

Route, HTTP method candidate, helper name similarity или request-shape marker не разрешают сетевой probe сами по себе.

## Подтверждённая progression boundary

```text
route candidate: /api/guilds/progression
HTTP method candidate: POST
method candidate unambiguous: true
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
request shape verified: false
ready for bounded route probe: false
network requests performed by evidence stages: false
```

## Helper-definition inventory

```text
public receipt: evidence/real-data/argentum-guild-progression-helper-definition.json
integrity checks: 36/36
definition candidates: 1
definition kind: method_definition
binding scope: terminal_symbol
definition characters: 40
alias candidates: 0
marker classes: []
full-chain occurrences observed: 2
terminal-symbol occurrences observed: 31
all scans truncated: false
```

## Helper-definition review

```text
public receipt: evidence/real-data/argentum-guild-progression-helper-definition-review.json
integrity checks: 42/42
disposition: unresolved_terminal_method_without_transport_semantics
helper identity resolved: false
request payload mapping resolved: false
ready for helper-reference inventory: true
ready for bounded route probe: false
```

## Helper-reference inventory

```text
public receipt: evidence/real-data/argentum-guild-progression-helper-reference.json
integrity checks: 40/40
full-chain occurrences: 2
terminal-symbol occurrences: 31
terminal-symbol-only occurrences: 29
unique reference candidates: 31
definition overlaps: 1
route-context references: 0
direct transport markers: []
request-shape markers: [JSON.stringify, body, data, params, url]
all scans truncated: false
network requests performed: false
```

Private inventory remains ignored:

```text
data/extracted/report-discovery/argentum-guild-progression-helper-reference.private.json
```

## Helper-reference review — completed and versioned

```text
public receipt: evidence/real-data/argentum-guild-progression-helper-reference-review.json
integrity checks: 46/46
reference count: 31
disposition: unresolved_references_without_route_or_transport_binding
route-context references: 0
direct transport contexts: 0
route transport bindings: 0
route request-shape bindings: 0
request-shape contexts: 17
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
request shape sufficient for bounded probe: false
ready for helper-owner inventory: true
network requests performed: false
```

Blockers:

```text
route_not_observed_in_reference_contexts
direct_transport_markers_not_observed
receiver_or_owner_binding_unresolved
request_shape_markers_not_bound_to_route_invocation
```

The review is scalar-free and does not publish raw callee, raw symbols, raw contexts, source IDs or request values.

## Helper-owner inventory — local implementation checkpoint only

Prepared locally but not versioned at the last user terminal checkpoint:

```text
src/coa_workbench/collector/guild_progression_helper_owner_index.py
src/coa_workbench/collector/guild_progression_helper_owner_inventory.py
scripts/inventory_guild_progression_helper_owners.py
tests/unit/test_guild_progression_helper_owner_inventory.py
```

Design boundary:

- offline-only;
- reads exact bound helper-reference private inventory and exact archived SPA asset;
- validates public/private reference alignment and raw asset spans;
- performs bounded lexical owner-candidate extraction;
- raw owner chains stay private;
- public candidate/group evidence exposes hashes, counts and classes only;
- integrity contract: `54` checks;
- owner binding is **not inferred** by inventory;
- next gate after a successful real inventory is explicit helper-owner review;
- bounded route probe remains false.

The latest local resume output ended successfully at:

```text
Helper-owner implementation is formatted and validated.
No real helper-owner inventory was executed.
No private helper-owner artifact was created.
No progression route network request was performed.
Helper owner binding remains unresolved.
Bounded progression route probe remains disabled.
No files staged.
No commit performed.
No push performed.
```

Therefore these are **not yet project-wide versioned facts**:

```text
helper-owner implementation versioned: false
helper-owner inventory real execution complete: false
helper-owner public receipt versioned: false
helper-owner review complete: false
```

## Current decision boundary

```text
helper-definition inventory complete: true
helper-definition review complete: true
helper-reference inventory complete: true
helper-reference review complete/versioned: true
helper-owner inventory implementation prepared locally: true
helper-owner inventory implementation versioned: false
helper-owner inventory executed: false
helper-owner review complete: false
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
request shape verified: false
ready for bounded progression route probe: false
guild API route semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for encounter-aware roster completion: false
planner scoring allowed: false
```

## Next bounded sequence

```text
sync local branch to docs handoff HEAD without losing untracked helper-owner files
-> verify/configure PowerShell 7 environment
-> remove obsolete root one-off run-e3 helper scripts only after status inspection
-> inspect exact helper-owner implementation diff
-> repeat focused + full local verification on synchronized HEAD
-> stage exactly four helper-owner implementation files
-> commit/push implementation atomically
-> verify exact-head CI
-> execute offline helper-owner inventory against exact private evidence
-> validate 54/54 and privacy/hash boundaries
-> version only approved public helper-owner receipt
-> implement explicit helper-owner review
-> consider bounded route probe only after exact helper identity, owner and payload binding
```

Do not perform a guessed network request to `/api/guilds/progression`.
