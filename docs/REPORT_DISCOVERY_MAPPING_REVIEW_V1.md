# Public report discovery mapping review v1

Дата review: 2026-07-29.

## Scope

Проверен mapping:

- `config/mappings/coa_public_report_discovery_v1.json`.

Основание review:

- bounded request `GET /api/reports/public` with `page=1`, `limit=5`, `sortBy=created_at`, `sortOrder=desc`;
- exact immutable gzip archive;
- scalar-free structural review;
- scalar-free full-root mapping review and summary;
- exact payload hash and schema fingerprint;
- local raw-archive selector validation пользователя;
- green Ubuntu and Windows repository verification before promotion.

## Reviewed payload

```text
route: /api/reports/public
payload hash: 2203e52709fad4fbc8d5235bc3699abeec6b85cf1e13b9df3e24091ddf8775c2
schema fingerprint: 4f47885820e6931cd76db538cabd68405b4969778c1bede9dee53a7f1e005ed4
top-level keys: pagination, reports, success
field paths: 24
node occurrences: 84
numeric-map paths: 0
candidate collections: 6
```

The only report-like collection in the reviewed payload is `/reports`. Its bounded item selector is `/reports/*`, with five object occurrences in this exact response.

## Review decisions

### Accepted as structurally unambiguous

The verified mapping extracts only:

- source report ID from `/reports/*/id` as `integer`;
- title from `/reports/*/title` as non-null `string`;
- creation timestamp from `/reports/*/created_at` as non-null `string`;
- start timestamp from `/reports/*/start_time` as non-null `string`;
- end timestamp from `/reports/*/end_time` as non-null `string`;
- visibility from `/reports/*/visibility` as non-null `string`;
- uploader username from `/reports/*/uploader_username` as non-null `string`.

All eleven source keys were observed on every one of the five report objects:

```text
created_at
end_time
guild_id
guild_name
highest_difficulty
id
locations
start_time
title
uploader_username
visibility
```

Required-key validation is retained to detect structural drift, while only the seven reviewed scalar fields are selected.

### Nullable observations

```text
/reports/*/guild_id                         null x 5
/reports/*/guild_name                       null x 5
/reports/*/highest_difficulty/trial_level   null x 5
```

`guild_id` and `guild_name` remain deferred because the exact payload contains no non-null example from which a stable type contract could be reviewed.

## Deferred scopes

The following scopes are not part of the verified extraction contract:

- `/pagination`;
- `/reports/*/guild_id`;
- `/reports/*/guild_name`;
- `/reports/*/highest_difficulty`;
- `/reports/*/locations`.

The review does not establish:

- category or filter semantics;
- whether the endpoint consistently enforces `limit=5`;
- whether additional pages exist;
- pagination stopping rules;
- deterministic cross-page selection;
- guild field semantics;
- difficulty or trial-level semantics;
- location value semantics;
- any gameplay mechanic.

## Exact validation results

The local validator executed every selected field against the exact immutable archive and confirmed:

1. exact payload SHA-256;
2. exact schema fingerprint;
3. route equality;
4. top-level key presence;
5. `/reports/*` selector behavior;
6. five report objects;
7. all eleven required source keys on every object;
8. seven field contracts;
9. 35 successful scalar extractions;
10. zero nullable values among the seven selected fields;
11. no source scalar values in validation output.

Pre-promotion result:

```text
mapping_id: coa-public-report-discovery-v1
status: candidate
all_structurally_consistent: true
all_raw_archive_selectors_consistent: true
route_matched: true
raw_payload_validated: true
report_item_count: 5
field_contract_count: 7
extracted_value_count: 35
nullable_value_count: 0
production_ready: false
can_promote: false
contains_source_scalar_values: false
```

`production_ready: false` was expected because the checked-in mapping still had status `candidate`. `can_promote: false` means automatic promotion is forbidden.

## Promotion decision

The mapping was manually promoted to `verified` on 2026-07-29 after:

- scalar-free field/type/nullability review;
- unique `/reports/*` candidate-selector review;
- successful exact raw-archive selector execution;
- exact hash/fingerprint/route validation;
- explicit preservation of deferred scopes;
- green Ubuntu and Windows repository verification.

Reviewer metadata stored in the mapping contract:

```text
reviewed_by: GunsPojoshe (operator), OpenAI-assisted review
reviewed_at: 2026-07-29T16:41:00+03:00
```

## Completed post-promotion validation

After pulling the promotion commits, the same local validator was executed against the same private archive and produced:

```text
mapping_id: coa-public-report-discovery-v1
status: verified
all_structurally_consistent: true
all_raw_archive_selectors_consistent: true
route_matched: true
raw_payload_validated: true
report_item_count: 5
field_contract_count: 7
extracted_value_count: 35
nullable_value_count: 0
production_ready: true
can_promote: false
contains_source_scalar_values: false
```

This completes the exact public-report parser/schema production gate. `can_promote: false` remains correct because automatic promotion is forbidden and the manual promotion is already complete.

## Interpretation boundary

`verified` confirms reproducible parser/schema extraction only for the exact reviewed route, payload hash, fingerprint, selector and seven selected fields. Any new payload hash or schema fingerprint requires a new review decision. Deferred scopes remain unavailable until separately observed, structurally reviewed and validated.
