# Real CoA Logs capture protocol

## Purpose

This document defines the first evidence checkpoint for a real `coa.ascensionlogs.gg` report.

The goal is not to guess API routes or game mechanics. The goal is to capture one real browser session safely, inventory the response payloads, fingerprint their structures and select candidates for an explicitly reviewed normalization mapping.

## Security rule

A browser HAR may contain cookies, authorization headers, account identifiers and private URLs.

- Never commit a HAR file.
- Never attach an unsanitized HAR to a GitHub issue, pull request or chat.
- Store it only under a gitignored local path such as `data/exchange/in/`.
- Do not copy authentication headers into configuration files.
- The current `import-har` implementation archives response bodies and sanitized URLs; it does not persist request headers or cookie values.
- The original HAR remains sensitive even after import and must stay local.

## Browser capture

Use Chrome or another Chromium browser.

1. Open a real report that contains at least one completed encounter.
2. Sign in only when the report requires it.
3. Open Developer Tools with `F12`.
4. Open the **Network** tab.
5. Enable **Preserve log**.
6. Enable **Disable cache** while Developer Tools is open.
7. Clear the existing network list.
8. Reload the report page.
9. Open one completed encounter.
10. Visit the report views that trigger data loading, including the encounter summary, roster/participants, casts or events, and aura/buff/debuff views when they exist.
11. Wait until visible requests have completed.
12. In the Network request list, use **Save all as HAR with content**.
13. Save the file locally, for example:

```text
data/exchange/in/coa-report-YYYYMMDD.har
```

Do not rename a HAR to JSON and do not edit it before import.

## Local import

From the repository root:

```powershell
uv sync --frozen --extra dev
uv run coa-workbench init-db
uv run coa-workbench import-har data/exchange/in/coa-report-YYYYMMDD.har
uv run coa-workbench inventory-har data/exchange/in/coa-report-YYYYMMDD.har \
  --output data/exchange/out/coa-report-inventory.json
```

The import must:

- accept entries only from the configured `coa.ascensionlogs.gg` host;
- archive response bodies immutably by SHA-256;
- record observations separately from deduplicated payload bodies;
- sanitize stored URLs;
- record content type, HTTP status and schema fingerprint when the response is JSON;
- avoid storing request headers and cookies.

## Discovery output required before normalization

The next implementation block must produce a deterministic inventory for the HAR with one row per response candidate:

- HTTP method;
- sanitized path;
- query-key names only;
- HTTP status;
- content type;
- uncompressed byte count;
- payload SHA-256;
- schema fingerprint for JSON;
- top-level JSON kind and keys;
- candidate collection paths;
- archive raw/observation identifiers;
- reason when an entry is skipped.

The inventory must not contain:

- request or response header values;
- cookies;
- authorization tokens;
- unredacted query values;
- full local usernames or home-directory paths.

`inventory-har` records only the registered hostname's safe request shape, response metadata and
content-derived identifiers. It archives non-empty response bodies through the immutable raw
archive. Use `inspect-archived <payload-path-or-hash>` to inspect an archived gzip JSON body; its
output reports only a path relative to `--raw-root`.

## Mapping gate

A normalization mapping may be created only after the inventory and selected payload are inspected.

The mapping must contain:

- the exact schema fingerprint;
- explicit collection paths;
- explicit field mappings;
- provenance type;
- mapping version;
- status `verified`;
- a note identifying the reviewed payload hash.

A `candidate` or fingerprint-mismatched mapping must remain rejected.

## First checkpoint acceptance criteria

The checkpoint is complete only when all of the following are true:

1. one real HAR is retained locally and not committed;
2. one or more response bodies are archived immutably;
3. the HAR inventory is generated without credentials or private header values;
4. a report payload and an encounter payload are identified from evidence;
5. roster/participant and aura-event candidates are identified or explicitly recorded as absent;
6. the selected JSON structures have stable fingerprints;
7. one mapping is manually reviewed and marked `verified`;
8. one report/encounter normalizes successfully;
9. actors, participants and aura events retain source pointers and provenance;
10. Aura State Engine output is reproducible from the archived payload hash;
11. anomalies and contradicting observations remain visible;
12. the full repository verification pipeline remains green on Ubuntu and Windows.

## Non-goals for this checkpoint

- inferring raid-wide scope;
- inferring overwrite or stacking rules;
- assigning a mechanic to a class/spec from one observation;
- enabling planner scoring;
- uploading private logs or HAR files to the repository;
- treating upstream class/spec detection as proof of a provider mechanic.
