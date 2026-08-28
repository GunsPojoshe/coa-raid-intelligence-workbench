# Interactive HAR discovery — historical/fallback protocol

Status: **fallback/historical**, updated classification **2026-08-26**.

This document no longer defines the active E4 roadmap. The current source order is in `docs/CURRENT_PARADIGM.md`.

## When to use

Use manual browser HAR only when:

```text
the official API does not cover the needed surface
AND pinned executable source does not answer it
AND existing RawArchive/report evidence is insufficient
AND a browser observation is permitted/appropriate
```

Do not use HAR merely to repeat a contract already documented elsewhere.

## Safe interaction protocol

When an exact UI→Network relation genuinely must be tested:

```text
clear Network log
preserve log
change one UI factor at a time
include at least one neighbouring negative control
repeat the same physical control when practical
save one bounded HAR with content
```

Treat the HAR as private. Feed it into the existing provider-neutral observation/review tooling rather than writing report-specific parsing helpers.

## Evidence rule

```text
ordered action window
-> request burst structure
-> repeated structural correlation
-> negative-control comparison
-> candidate relation
-> separate semantic review
```

A UI label is not a contract. A correlation is not a gameplay mechanic.

## Privacy

Never commit raw HAR, source scalar values, report/encounter/player/guild identities, cookies, headers, tokens, query/body values or screenshots containing private state.

## No evasion

Do not use stealth/fingerprint/challenge-bypass techniques. If ordinary access is unavailable or the source is unstable, stop the browser experiment and use another evidence lane.

## Current project status

The active population-statistics gate uses the official `/statistics` API and requires no HAR. Historical difficulty interaction work remains an unresolved evidence branch, not the current next step.
