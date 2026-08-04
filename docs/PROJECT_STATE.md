# Фактическое состояние проекта

Дата актуализации: **2026-08-04**.

Перед любой работой перепроверять live-состояние GitHub, текущий HEAD, PR, CI, versioned receipts и local-only artifacts. Этот документ фиксирует доказанный checkpoint, но его собственное обновление создаёт новый commit.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #7 остаётся Draft до явного закрытия evidence gates.

## Последний полностью проверенный implementation checkpoint

```text
implementation HEAD: 82265903a26bbf8e0032e6dc2512e623055da972
commit: Format guild progression helper definition CLI
Verify repository run: #578
conclusion: success
public-release-audit: success
Ubuntu: success
Windows: success
migrations: 0001–0008
working tree after push: clean
```

После этого checkpoint началась серия documentation-only commits. Для текущего HEAD CI проверять отдельно.

## Подтверждённые checkpoints

- public manifest: `6454` уникальных отчёта;
- Argentum identity decision;
- private comparison baseline: `17` отчётов;
- reviewed full-crawl collection contract;
- `/api/guilds/search` route/schema review;
- bounded multi-result limit capture `1 / 7 / 7`;
- explicit limit-truncation review;
- offline `/api/guilds/progression` usage-context inventory и review;
- offline helper/call-site inventory и review;
- evidence-backed unambiguous `POST` method candidate;
- offline helper-definition inventory implementation;
- deterministic helper-definition tests;
- Ruff formatting defect fixed and verified by run #578.

## Progression helper/call-site checkpoint

```text
inventory: evidence/real-data/argentum-guild-progression-callsite.json
inventory version: guild-progression-helper-callsite-inventory-v1
canonical LF SHA-256: ad8a5addf9ac9dd566284e0bc395ac40100986d0f14f0a49e9519a6aef28d351
integrity checks: 32/32
network requests: 0
route occurrences: 1
call candidates: 1
direct invocation candidates: 1
call class: generic_helper_call
HTTP method candidate: POST
method evidence: method_property_literal
method candidate unambiguous: true
```

```text
review: evidence/real-data/argentum-guild-progression-callsite-review.json
review version: guild-progression-helper-callsite-review-v1
SHA-256: d79302d755eab918ce3f85a9ad39e78231720391c8f0692925fe2e79b6adc60f
integrity checks: 36/36
helper/call-site reviewed: true
helper identity resolved: false
request payload mapping resolved: false
request shape sufficient for bounded probe: false
ready for helper-definition inventory: true
ready for bounded route probe: false
```

Blockers remain:

```text
generic_helper_identity_unresolved
structural_envelope_overbroad
request_payload_mapping_unresolved
```

`POST` is a method candidate inside the observed generic-helper call. It is not yet a verified request contract.

## Helper-definition inventory implementation

```text
src/coa_workbench/collector/guild_progression_helper_definition_command.py
src/coa_workbench/collector/guild_progression_helper_definition_index.py
src/coa_workbench/collector/guild_progression_helper_definition_inventory.py
scripts/inventory_guild_progression_helper_definition.py
tests/unit/test_guild_progression_helper_definition_command.py
tests/unit/test_guild_progression_helper_definition_index.py
tests/unit/test_guild_progression_helper_definition_inventory.py
```

Properties:

- offline-only;
- reads the exact archived SPA asset;
- binds to published call-site and recovery hashes;
- keeps raw helper definitions, aliases, callees and JavaScript contexts private;
- emits only scalar-free public receipt data;
- applies bounded scans and `36` integrity checks;
- never raises route/full-crawl/scoring gates automatically.

The implementation is complete and CI-green, but the inventory has not yet been executed against the current local private artifacts and no helper-definition receipt/review is versioned.

## Current exact boundary

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild-search route/schema verified: true
guild-search limit truncation verified: true
progression route candidate observed: true
progression usage context reviewed: true
progression helper/call-site inventory observed: true
progression helper/call-site reviewed: true
progression HTTP method candidate: POST
progression method candidate unambiguous: true
helper-definition inventory implementation complete: true
helper-definition inventory executed on private artifacts: false
helper-definition public receipt validated: false
helper-definition receipt versioned: false
helper-definition review complete: false
progression helper identity resolved: false
progression request payload mapping resolved: false
progression request shape verified: false
ready for bounded progression route probe: false
progression route semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Следующий допустимый bounded этап

```text
verify current documentation-only HEAD and CI
-> sync local branch by fast-forward
-> confirm clean working tree and preserved local evidence
-> run offline helper-definition inventory on exact private artifacts
-> inspect private output and integrity checks
-> validate scalar-free public receipt
-> version only the public receipt if privacy and bindings pass
-> implement explicit helper-definition review
-> bounded progression route probe only if helper identity and exact payload contract become verified
```

Until explicit helper-definition review passes, do not perform a guessed network request to `/api/guilds/progression`.

## Local Windows state and tooling

```text
repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
local implementation HEAD before documentation commits: 82265903a26bbf8e0032e6dc2512e623055da972
working tree: clean
evidence paths: preserved
```

Known environment detail:

- `.venv` was not activated;
- local `uv sync --frozen --extra dev` attempted to build Ruff `0.12.12` from source and failed because MSVC `link.exe` was unavailable;
- the CI formatting fix was applied with the official standalone Ruff `0.12.12` Windows binary and passed lint/format checks;
- future local instructions should use `git --no-pager diff` to avoid stopping at `(END)`.

## Workflow notification convention

After any push or GitHub connector write that starts a workflow:

1. check the exact new run immediately;
2. report current job states;
3. offer one opt-in completion notification for that exact run;
4. create the task only after user acceptance;
5. disable it after completion or supersession.

User preference is 15-minute polling. Current automation minimum is one hour, so never state that 15-minute polling is active unless platform support changes.

## Data and Git policy

Versioned: code/tests, migrations, reviewed mappings, canonical documentation and scalar-free evidence receipts.

Local-only:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never commit source guild IDs, report IDs, source rows, private queries, private receipts, raw JavaScript contexts, raw callees, DuckDB, credentials, cookies, tokens, Authorization headers, browser profiles, `.env` or unsanitized HAR.