# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата актуализации: **2026-08-13**.

## 1. Цель

Создать localhost-first evidence-first платформу рейдовой аналитики для **Conquest of Azeroth**, которая связывает фактическую явку, проверенные build/performance observations и encounter requirements и объясняет конкретные решения по составу.

Не использовать Bronzebeard/Classless/Mystic/Hero Architect/shared Ascension сведения как CoA-факты без exact CoA evidence.

## 2. Truth model

```text
combat-log event = observation
combat-log event != automatic mechanic proof
class/spec presence != verified capability coverage
```

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## 3. Evidence architecture

```text
source response
-> immutable raw payload
-> SHA-256 / schema fingerprint
-> reviewed extractor or mapping
-> deterministic normalization/extraction
-> immutable observations
-> supporting / contradicting evidence
-> trust decision
-> explainable recommendation
```

## 4. Implemented foundation

- localhost FastAPI planner;
- DuckDB migrations `0001`–`0008`;
- immutable raw archive;
- retrieval observations;
- JSON/HAR privacy-safe tooling;
- schema fingerprints and mapping gates;
- report/encounter/actor/participant/aura normalization;
- hypothesis/evidence/trust layers;
- repository verifier;
- Ubuntu/Windows CI and public-release audit.

## 5. Verified guild/report baseline

```text
public reports: 6454
unique public report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
```

## 6. Guild progression — corrected request contract

The old helper chain began from an incorrect semantic assumption: the exact literal `/api/guilds/progression` was treated as a request-endpoint candidate.

Review of the exact archived SPA asset proves that this literal appears as a **cache-exclusion configuration value**, not as a direct request.

Direct frontend evidence:

```text
API base: https://coa.ascensionlogs.gg/api
methods observed: GET only
direct progression calls: 4
POST observed: false

GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

Observed parameter-key sets:

```text
rankings:
  - bracket
  - bracket,difficulty,location,phaseId,realm
  - an explicit {} params branch is present

full-clears:
  - bracket,difficulty,location,page,phaseId,realm

rankings/{bossId}:
  - bracket,difficulty,page,phaseId,realm
```

Canonical public receipt:

```text
evidence/real-data/argentum-guild-progression-frontend-request-contract.json
```

No network request was performed to obtain this evidence.

## 7. Current decision boundary

```text
historical helper chain superseded: true
exact legacy /api/guilds/progression direct endpoint: false
bounded rankings GET contract observed: true
ready for bounded rankings GET probe: true
guild API response semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
ready for full guild crawl: false
planner scoring allowed: false
```

## 8. Next product path

```text
one bounded GET /api/guilds/progression/rankings using the observed empty-params branch
-> archive response unchanged
-> schema/fingerprint review
-> determine pagination/termination semantics
-> expand only after evidence
-> full guild progression corpus
-> multi-report character identity
-> verified build/capability observations
-> encounter requirement models
-> dynamic attendance-aware roster completion
```

Do not return to the old helper/owner graph unless a concrete future request path requires it.

## 9. Development model

The agent performs GitHub/PR/CI/repository work directly whenever tools permit it. The user is involved only for Windows/local/private boundaries the agent cannot access directly.

Private/raw files may be inspected for analysis. Publication/versioning remains separately controlled.

Use focused tests while iterating, one aggregate `scripts/verify_repo.py` before a meaningful push, then exact-head CI.
