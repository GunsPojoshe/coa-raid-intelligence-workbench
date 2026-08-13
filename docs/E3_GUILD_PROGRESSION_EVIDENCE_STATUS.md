# E3 guild progression evidence status

Дата актуализации: **2026-08-13**.

## 1. Remote checkpoint

```text
scope: Conquest of Azeroth only
branch: e3/real-log-capture
remote HEAD before this docs cleanup: be899cc5f66c7bd82a1006116dbe57d91ecaed84
Verify repository: #613
run ID: 31651028612
conclusion: success
public-release-audit: success
ubuntu: success
windows: success
```

The remote helper receipts at that checkpoint remain immutable history. Their previous semantic interpretation is partially superseded by a newly demonstrated lexical defect described below.

## 2. Progression boundary

```text
route candidate: /api/guilds/progression
HTTP method candidate: POST
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
request shape verified: false
ready for bounded route probe: false
network requests performed by current evidence work: false
```

`POST` remains evidence-backed as a method candidate, not a complete request contract.

## 3. Lexical defect discovered

The original definition/reference/owner chain relied on lexical masking that treated an entire JavaScript backtick template as a simple string boundary and did not correctly distinguish template text from executable `${...}` expressions.

A narrow offline diagnostic classified the two suspicious relevant anchors as:

```text
plain_code: 9
template_text: 2
template_expression_code: 0
```

A contamination-boundary check then established:

```text
non-code owner candidates: 2
non-code reference symbols for those candidates: 2
lexical pair: template_text__reference_template_text
earliest affected stage: helper_reference_inventory
```

Inspection of the shared definition/reference lexical implementation showed the same simplified masking assumption also influenced occurrence counts feeding definition evidence. Therefore the safe correction boundary is the shared lexical scanner, not an owner-only patch.

## 4. Historical versioned evidence — reproducible but superseded for inference

The remote history contains successful versioned stages with contracts:

```text
helper-definition inventory: 36/36
helper-definition review: 42/42
helper-reference inventory: 40/40
helper-reference review: 46/46
helper-owner inventory: 54/54
helper-owner review: 16/16
```

Historical interpretation included:

```text
definition candidates: 1
references: 31
definition overlaps: 1
owner candidates: 17
owner groups: 8
full-chain owner group: 5
definition owner group: 7
```

Do not use those counts/groups as current helper-identity evidence. The files remain historical/auditable receipts; they are not deleted merely because a later defect invalidated part of the interpretation.

## 5. Provisional corrected local evidence

The following results were generated offline after introducing lexical hardening. They are **not yet versioned canonical evidence**.

### Helper-definition inventory/review

```text
full-chain occurrences: 2
terminal-symbol occurrences: 45
definition candidates: 3
definition kinds: [method_definition]
binding scopes: [terminal_symbol]
marker classes: []
review disposition: unresolved_multiple_terminal_method_definitions_without_transport_semantics
helper identity resolved: false
request payload mapping resolved: false
ready for bounded route probe: false
```

### Helper-reference inventory/review

```text
reference count: 45
full-chain occurrences: 2
terminal-symbol occurrences: 45
terminal-symbol-only occurrences: 43
definition overlaps: 3
reference kinds: [definition_candidate, invocation, member_reference, object_key]
symbol scopes: [full_chain, terminal_symbol]
route-context references: 0
direct transport contexts: 0
request-shape contexts: 29
request-shape markers: [JSON.stringify, body, data, method, params, url]
disposition: unresolved_references_without_route_or_transport_binding
```

Blockers remain:

```text
route_not_observed_in_reference_contexts
direct_transport_markers_not_observed
receiver_or_owner_binding_unresolved
request_shape_markers_not_bound_to_route_invocation
```

### Helper-owner inventory

Latest provisional public receipt produced from the corrected 45-reference set:

```text
integrity checks: 54/54
reference count: 45
owner candidates: 21
owner groups: 12
definition owner candidates: 1
member receiver candidates: 21
definition container candidates: 0
references without owner candidates: 24
owner depths: [1, 2]
cross-definition owner groups: 1
helper owner binding resolved: false
ready for bounded route probe: false
network requests performed: false
```

Relevant topology:

```text
full-chain invocations: refs 6, 20 -> owner group 6
cross-definition owner group: 8
  definition ref: 1
  non-definition refs: 2, 3, 4, 15, 16, 17, 29, 40
```

This is not owner convergence. Group 8 does not own the two full-chain invocations.

The corrected owner review has **not** been completed/versioned. Do not infer `6 == 8` or `6 != 8` as a semantic identity relation merely from opaque group indexes.

## 6. Current implementation state

The local analyzer repair is partially applied. A generated updater failed after modifying owner code because its test-fixture text replacement did not match the actual file:

```text
owner inventory test asset block not found
```

Subsequent focused Ruff/tests passed, but the final local diff has not had a full aggregate repository verification and is not committed/pushed.

The final `finish-e3-owner-hardening.py` proposed afterward was not executed.

Therefore:

```text
lexical analyzer repair versioned: false
corrected public receipts versioned: false
corrected owner review complete: false
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
ready for bounded route probe: false
```

## 7. Correct next sequence

Stop the open-ended owner/alias investigation.

```text
finish one coherent lexical/analyzer repair
-> regression-test template text vs ${...} expression behavior
-> remove stale hardcoded 31/1 assumptions from affected validators
-> focused tests
-> one full verify_repo.py
-> one coherent commit/push
-> exact-head CI
-> trace the two concrete full-chain invocations (refs 6 and 20)
-> locate their actual helper provenance/definition
-> map exact call arguments into request payload
-> review exact bounded request contract
-> only then perform one bounded route probe
```

Use a narrow diagnostic only if it directly distinguishes two concrete provenance paths. Do not introduce another permanent evidence layer merely to continue graph exploration.

## 8. Privacy

Private/raw files can be read for analysis. The publication boundary remains strict: do not version raw JavaScript, private source IDs, request values, raw owner chains, private contexts, secrets or private receipts by default.

No guessed request to `/api/guilds/progression`.
