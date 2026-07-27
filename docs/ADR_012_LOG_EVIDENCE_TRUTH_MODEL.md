# ADR-012: Log evidence truth model

## Status

Accepted for implementation on branch `e2/log-evidence-refactor`.

## Context

The current 45-effect catalog and class/spec provider links originated from the legacy Excel workbook. They are useful migration evidence, but spot checks and raid-log behaviour show that a simple relation

```text
class/spec present -> effect covered
```

is not a reliable model.

Observed mechanics can depend on source, target, application order, target count, refresh/overwrite behaviour, simultaneous sources, game version and actual player execution. A targeted aura applied to forty players before a raid-wide aura can produce a different state from the reverse order. This cannot be represented by a boolean provider table.

`coa.ascensionlogs.gg` is therefore the primary observation source. A log event is evidence of an event, not automatically proof of a general mechanic.

## Decision

### 1. Legacy data classification

All Excel-derived effects and provider capabilities are classified as `legacy_unverified`.

They:

- remain available for migration audit and forensic comparison;
- are excluded from canonical scoring by default;
- can be enabled only with `COA_ENABLE_LEGACY_EFFECTS=1`;
- may not be promoted without log evidence.

### 2. Evidence layers

The warehouse separates:

1. immutable raw payloads;
2. normalized observations;
3. reconstructed aura-state intervals;
4. mechanic hypotheses;
5. links between hypotheses and supporting/contradicting observations;
6. confirmed or rejected mechanics;
7. versioned inference runs and weighting policies.

### 3. Trust states

```text
legacy_unverified
observed
candidate
corroborated
confirmed
contradicted
rejected
```

Only `corroborated` and `confirmed` data may participate in canonical planner scoring.

### 4. Temporal and cohort weighting

Evidence weight is versioned and includes:

- exponential recency decay;
- separate global and guild cohorts;
- a higher default weight for guild observations when estimating reproducibility by the guild;
- independent report and encounter minimums;
- explicit confirmation and rejection thresholds.

The initial policy uses a 90-day half-life. This is an implementation default, not a game truth, and must remain configurable and versioned.

### 5. Route discovery

Collector routes are not production-ready merely because they were observed once. Each route requires:

- route template;
- authentication mode;
- successful probe;
- response/schema fingerprint;
- pagination and rate policy;
- raw sample;
- current status.

Unverified routes are rejected by the collector registry.

### 6. Aura State Engine target

The canonical engine will reconstruct per-target intervals from apply/refresh/remove events and retain:

- source actor;
- target actor;
- spell ID;
- start/end timestamps;
- stack count;
- application and removal ordinals;
- reconstruction version;
- unresolved/ambiguous state.

Order-sensitive stacking and overwrite hypotheses are inferred from these intervals, never from display names alone.

## Consequences

- Current coverage and Top-N advice disappear from canonical preview until confirmed evidence exists.
- The UI may show data unavailable instead of a fabricated 0/45 score.
- Legacy comparisons remain possible for regression research.
- Database growth increases because observations and contradictions are retained.
- Planner results become reproducible through dataset, policy and inference versions.

## Initial implementation

- migration `0003_log_evidence_refactor.sql`;
- source registry `config/ascension_logs_sources.yaml`;
- canonical trust policy module;
- recency/cohort weighting module;
- default legacy-scoring gate;
- regression tests for trust, weighting, route verification and migration schema.
