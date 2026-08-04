# Фактическое состояние проекта

Дата актуализации: **2026-08-04**.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #7 открыт, Draft и mergeable. Его base — `e2/log-evidence-refactor`, head — `e3/real-log-capture`.

## Последний полностью завершённый CI до текущей documentation series

```text
HEAD: 49bf9cdae01817cc0a7c6eb073d23d588ba6045e
Verify repository run: #583
conclusion: success
public-release-audit: success
Ubuntu: success
Windows: success
migrations: 0001–0008
```

После этого HEAD добавлена серия documentation-only commits, актуализирующая CoA-only предметную область, provisional utility baseline и целевую формулировку продукта. Exact текущий HEAD и CI необходимо проверять live, так как этот документ сам создаёт новый commit.

## Исправленная предметная граница

Проект теперь канонически ограничен **Conquest of Azeroth only**.

Добавлены:

```text
docs/COA_DOMAIN_BOUNDARY.md
docs/COA_TARGET_PRODUCT_DEFINITION.md
docs/COA_RAID_UTILITY_BASELINE_2026-08-02.md
```

Удалены из канонических предположений:

- Mystic Enchants;
- Bronzebeard-specific mechanics;
- Classless Ascension ability-selection model;
- Hero Architect assumptions;
- shared FAQ statements without exact CoA evidence.

## Целевой продукт

Главный конечный сценарий больше не формулируется как один постоянный `optimal BiS 25 roster`.

Каноническая цель:

```text
actual attendance
+
verified player/build/performance evidence
+
encounter requirements
+
relevant external benchmarks
=
explainable dynamic roster completion
```

Система должна объяснять, почему конкретный игрок нужен именно текущему составу.

## Provisional raid utility baseline

Supplied HTML был структурно проанализирован и зафиксирован как research reference:

```text
source SHA-256: adbb2f7f06d750ddad4d981cca3f22b3141f471e8f9819e87f528f357fabdddd
class cards: 28
class/spec associations: 87
unique specialization labels: 67
utility rows: 187
rows observed in latest 30-log sample: 132
rows with 0 observations: 55
combatants-info present: 23/30 logs
```

Это не доказанный полный каталог 69 специализаций и не input для planner scoring.

## Подтверждённые data checkpoints

```text
public reports: 6454
unique public report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
```

Guild-search:

```text
route/schema verified: true
limit result counts: 1 / 7 / 7
limit truncation semantics verified: true
```

Progression helper/call-site:

```text
route candidate observed: true
call class: generic_helper_call
HTTP method candidate: POST
method candidate unambiguous: true
helper identity resolved: false
request payload mapping resolved: false
ready for bounded route probe: false
```

## Armory boundary

Reviewed mappings support selected extraction of character identity, realm, class, upstream role, active specialization index, resolved talent ranks, selected stats and talent-grid structure.

They do not prove runtime magnitude, stacking, scope, provider equivalence or planner criticality.

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
- exact archived SPA asset;
- exact bound private/public inputs;
- raw definitions and aliases private;
- scalar-free public receipt;
- 36 integrity checks;
- all downstream gates remain false.

## Current exact boundary

```text
helper-definition inventory implementation complete: true
helper-definition inventory executed on private artifacts: false
helper-definition public receipt validated: false
helper-definition receipt versioned: false
helper-definition review complete: false
progression helper identity resolved: false
progression request payload mapping resolved: false
progression request shape verified: false
ready for bounded progression route probe: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for encounter-aware roster completion: false
planner scoring allowed: false
```

## Следующий bounded этап

```text
verify exact documentation HEAD and CI
-> fast-forward local e3/real-log-capture
-> confirm clean working tree and preserved private evidence
-> run offline helper-definition inventory
-> inspect private output and all 36 checks
-> validate scalar-free public receipt
-> version only the public receipt
-> implement deterministic helper-definition review
```

Do not perform a guessed network request to `/api/guilds/progression`.

## Local Windows facts

```text
repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
last known local implementation HEAD before documentation pull: 82265903a26bbf8e0032e6dc2512e623055da972
private evidence paths: preserve
```

Known local issue:

```text
uv sync --frozen --extra dev
-> attempted source build of ruff==0.12.12
-> failed because MSVC link.exe was unavailable
```

Do not install Visual Studio Build Tools solely for formatting. Use `git --no-pager diff`.
