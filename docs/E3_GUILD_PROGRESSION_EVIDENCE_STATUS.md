# E3 guild progression evidence status

## Статус

```text
scope: Conquest of Azeroth only
branch: e3/real-log-capture
last_reviewed: 2026-08-06
verified_baseline_head: 8b24f5225b79172cb998c9ca53188fb76a6109ca
verified_ci_run: 595
verified_ci_result: success
```

## Цель evidence chain

Guild progression разрешается использовать только после последовательного доказательства request contract, collection semantics и полноты. Обнаружение route или HTTP method candidate само по себе не разрешает сетевой probe.

```text
route discovery
-> usage-context review
-> helper call-site inventory and review
-> helper-definition inventory and review
-> helper-reference inventory and review
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

## Current bounded stage: helper-reference inventory

The implementation inventories every bounded code reference to the exact private callee chain and its terminal symbol in the already archived SPA asset.

It does not perform network requests.

### Inputs

```text
evidence/real-data/argentum-guild-progression-helper-definition-review.json
evidence/real-data/argentum-guild-progression-helper-definition.json
data/extracted/report-discovery/argentum-guild-progression-helper-definition.private.json
data/raw/<exact recovered asset>
```

### Private output

```text
data/extracted/report-discovery/argentum-guild-progression-helper-reference.private.json
```

The private output may contain:

- exact callee and terminal symbol;
- source offsets;
- bounded raw contexts;
- definition-span alignment;
- transport and request-shape marker observations.

It must remain ignored by Git.

### Public output

```text
data/exchange/out/argentum-guild-progression-helper-reference.json
```

The public receipt contains only:

- occurrence counts and truncation flags;
- reference classifications;
- symbol scope classifications;
- context SHA-256 values and character counts;
- marker classes;
- definition-overlap and route-context booleans;
- explicit false downstream gates.

It must not publish raw callee, raw symbol, source offsets, raw context, guild identifiers or request payload values.

### Bounded controls

```text
max symbol occurrences: 500
max reference candidates: 500
private context characters per side: 1024
raw archive only: true
network requests performed: false
```

### Required reconciliation

The new scan must reconcile exactly with the versioned definition inventory:

```text
full-chain occurrence count
terminal-symbol occurrence count
scan truncation state
definition candidate overlap
asset payload SHA-256
private inventory SHA-256
public inventory SHA-256
helper-definition review SHA-256
```

Any mismatch stops the stage.

## Decision boundary

Until helper-reference evidence is privately executed and explicitly reviewed:

```text
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

## Acceptance criteria for this stage

1. The implementation reads only versioned receipts, the exact private definition inventory and the exact archived asset.
2. Full-chain and terminal-symbol counts reconcile with prior evidence.
3. All scans are bounded and non-truncated.
4. Raw symbols and contexts remain private.
5. The public receipt is scalar-free and passes its integrity checks.
6. The stage selects explicit helper-reference review as the next gate.
7. No route probe, full crawl or planner scoring gate is enabled.
