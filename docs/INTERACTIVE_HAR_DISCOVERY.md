# Interactive HAR discovery — legacy/fallback E4 path

Status date: **2026-08-19**.

The original E4 experiment used a manually exported continuous HAR plus an ordered action list. That method remains supported for forensic replay and fallback analysis, but it is **no longer the primary E4 operator workflow**.

Current E4 operating document:

```text
docs/BROWSER_OBSERVATORY.md
```

Concept-change savepoint:

```text
docs/DEVELOPMENT_CONCEPT_PIVOT_2026-08-19.md
```

Local/private workspace boundary:

```text
docs/LOCAL_WORKSPACE_BOUNDARY.md
```

## When manual HAR remains useful

Use the manual path only when:

```text
live browser automation cannot run locally
an old HAR must be replayed
Browser Observatory itself needs forensic verification
an already-captured private HAR contains the only relevant evidence
```

Reusable fallback command:

```powershell
uv run --no-sync python scripts/review_interaction_session.py `
  "<PRIVATE_HAR>" `
  "<PRIVATE_ACTION_MANIFEST>" `
  --output "data/exchange/out/coa-interaction-review.json"
```

The same provider-neutral `NetworkObservation`, interaction-window and differential code is used. HAR is therefore an adapter, not a competing analysis architecture.

## Trust boundary

Manual HAR evidence does not bypass Browser Observatory/E3 rules:

```text
raw HAR remains private
scalar values stay private
network-silent is a valid result
UI labels do not prove semantics
reviewed deterministic contracts are required before promotion
planner/mechanic trust remains fail-closed
```

The historical controlled sequence and one-factor-at-a-time method remain useful experimental guidance, but new E4 work should start from `docs/BROWSER_OBSERVATORY.md`.
