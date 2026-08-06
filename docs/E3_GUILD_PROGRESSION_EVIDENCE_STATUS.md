# E3 guild progression evidence status

## Статус

```text
scope: Conquest of Azeroth only
branch: e3/real-log-capture
last_reviewed: 2026-08-07
last_fully_verified_head: 50e6f50cf478eed4c6abf5bc032c2c1661c8ef8e
last_fully_verified_ci_run: 596
last_fully_verified_ci_result: success
reference_receipt_head: e664d258bd6e93cc8fce8ff4781d577ca8f17fa6
reference_review_implementation: staged
```

## Цель evidence chain

Guild progression разрешается использовать только после последовательного доказательства request contract, collection semantics и полноты. Обнаружение route, HTTP method candidate, маркеров payload или сходного имени helper само по себе не разрешает сетевой probe.

```text
route discovery
-> usage-context review
-> helper call-site inventory and review
-> helper-definition inventory and review
-> helper-reference inventory and review
-> helper-owner inventory and review
-> exact bounded request contract
-> bounded route probe
-> pagination, termination and completeness review
-> full guild crawl
```

## Подтверждённое состояние

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

### Helper-definition inventory

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

### Helper-definition review

```text
public receipt: evidence/real-data/argentum-guild-progression-helper-definition-review.json
receipt SHA-256: 923f80b0d9b9b1e68d86933d601d65d2d6f0d8eda3a9c0d2d15be4595a449753
integrity checks: 42/42
disposition: unresolved_terminal_method_without_transport_semantics
helper identity resolved: false
request payload mapping resolved: false
ready for helper-reference inventory: true
ready for bounded route probe: false
```

The single 40-character terminal-symbol method is not sufficient to bind the observed call site to a transport implementation. It does not prove receiver ownership, alias ownership, payload mapping, headers, serialization or response handling.

## Helper-reference inventory

### Versioned public receipt

```text
public receipt: evidence/real-data/argentum-guild-progression-helper-reference.json
receipt SHA-256: f21a0b74a70e76f4728e3322e6c79571289895453f3fae6e44e851f3818da982
private output SHA-256: 5542e7979fe01cd85239b09c81aaa8ca667fedd8c8ef1b4db541333c008d5bbd
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

Reference kinds observed:

```text
definition_candidate
invocation
member_reference
object_key
```

The request-shape marker classes were observed only inside broad bounded reference contexts. No reference context contains the progression route, and no direct transport marker was observed. Therefore those marker classes do not establish route binding, helper ownership or payload mapping.

### Privacy boundary

The private output remains ignored by Git:

```text
data/extracted/report-discovery/argentum-guild-progression-helper-reference.private.json
```

The public receipt publishes only:

- occurrence counts and truncation flags;
- reference and symbol-scope classifications;
- context SHA-256 values and character counts;
- marker classes;
- definition-overlap and route-context booleans;
- explicit false downstream gates.

It does not publish raw callee, raw symbol, source offsets, raw context, guild identifiers or request payload values.

## Current bounded stage: explicit helper-reference review

Implementation files:

```text
src/coa_workbench/collector/guild_progression_helper_reference_review.py
scripts/review_guild_progression_helper_references.py
tests/unit/test_guild_progression_helper_reference_review.py
```

The review stage:

1. Binds the versioned public inventory to the exact private inventory and helper-definition review.
2. Revalidates all 31 public/private reference rows in order.
3. Recomputes private context hashes and validates bounded context spans.
4. Reviews each reference without publishing raw symbols or contexts.
5. Separates request-shape marker proximity from actual route/transport binding.
6. Keeps helper identity, owner binding, payload mapping and route-probe gates false.
7. Selects helper-owner inventory as the next bounded gate.

Expected review disposition:

```text
unresolved_references_without_route_or_transport_binding
```

Expected blockers:

```text
route_not_observed_in_reference_contexts
direct_transport_markers_not_observed
receiver_or_owner_binding_unresolved
request_shape_markers_not_bound_to_route_invocation
```

Integrity contract:

```text
integrity checks: 46
public/private reference alignment: required
network requests performed: false
raw contexts published: false
ready for helper-owner inventory: true
ready for bounded route probe: false
```

Local implementation validation:

```text
Python compilation: passed
focused unit tests: 5 passed
```

## Decision boundary

Until helper-reference review is executed on the exact private inventory and its scalar-free public receipt is versioned:

```text
helper-reference inventory complete: true
helper-reference public receipt versioned: true
helper-reference review implementation complete: true
helper-reference review private execution complete: false
helper-reference review public receipt versioned: false
helper owner binding resolved: false
helper identity resolved: false
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
ready for BiS25 scoring: false
planner scoring allowed: false
```

## Next bounded action

```text
verify CI for the versioned helper-reference inventory receipt
-> publish explicit helper-reference review implementation
-> execute review against the exact private reference inventory
-> validate scalar-free public review receipt
-> version only the public review receipt
-> implement helper-owner inventory
```
