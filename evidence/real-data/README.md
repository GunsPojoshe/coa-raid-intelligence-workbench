# Real-data evidence checkpoint

This directory contains versioned, scalar-free receipts that make the observed CoA Logs pipeline reproducible without committing private payload contents.

## Versioned here

- parser and extraction stage receipts that contain hashes, counts, route shapes and boolean integrity gates;
- reviewed mapping contracts and source/schema fingerprints;
- documentation of the current trust and promotion boundary.

## Local only

The following directories may contain source-derived names, GUIDs, talents, gear, report identifiers, reconstructed entities or a local DuckDB warehouse. They are intentionally ignored by Git:

- `data/raw/`
- `data/warehouse/`
- `data/normalized/`
- `data/reconstructed/`
- `data/extracted/`
- `data/exchange/in/`
- `data/exchange/out/`

Never commit HAR files, cookies, tokens, browser profiles, `.env` files, DuckDB files or raw response bodies.

## Current observed report slice

Observed route shapes:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

Exact payload bindings:

```text
report_detail
payload:     161739896f0b8321f884bcc24d1896efb894a9c6e05166269189f9871c64cba9
fingerprint: 3d533a4178b67957bbd31544ddf5484bd5959635ebd5edcdd0c7689a4bace216

encounter_detail
payload:     955437d6c9c287cc7db280dd2388b88603af2785508061b95c7811dcd272fe22
fingerprint: 567f36824efb37a29b835df01ce9b1fcc79eae57d6230202d16a6265c6ca0e85

combatants_info
payload:     45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14
fingerprint: 41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff
```

## Current combatants-info boundary

The candidate extractor validates exact archive, observation manifest, route context, persisted report/encounter references, stable actor IDs, actor names, selected field types and record hashes.

The current exact payload produced:

```text
source matches:       1350
output observations:  1343
deduplicated matches: 7
linked actors:        11
integrity checks:     12/12
```

This verifies parser linkage for the exact payload only. It does not verify companion-addon provenance, nested collection semantics, gameplay mechanics or planner scoring. Automatic persistence, promotion and core entity mutation remain disabled.
