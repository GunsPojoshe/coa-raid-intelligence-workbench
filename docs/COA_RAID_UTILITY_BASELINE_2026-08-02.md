# CoA raid utility baseline — 2026-08-02

## Status

```text
status: provisional_reference
canonical_for_gameplay_scoring: false
requires_log_verification: true
source_scope_complete: false
```

This document records the current supplied working inventory of Conquest of Azeroth raid-wide and broad-area utility. It is allowed as a planning and research reference, but it is not verified gameplay truth and may not enter canonical planner scoring.

## Supplied source artifact

```text
source file: raid_utilities.html
source SHA-256: adbb2f7f06d750ddad4d981cca3f22b3141f471e8f9819e87f528f357fabdddd
source generated_at: 2026-08-02T12:49:15Z
source label: Raid Utility — кто что даёт рейду
```

The source artifact states that it combines:

- talents observed in the latest 30 public logs;
- all talent-grid entries marked `S`, including entries not selected in those logs;
- `S` as party/raid-wide;
- `M` as a broad-area effect.

## Exact structural inventory of the supplied artifact

```text
class cards: 28
class/spec associations represented: 87
unique specialization labels: 67
utility rows: 187
rows observed at least once in the 30-log sample: 132
rows with 0 observations in the 30-log sample: 55
combatants-info present in source logs: 23/30
```

The source header says `Уникальных в выборке: 187`; inspection confirms 187 class/spec/talent rows.

This file does **not** prove that the supplied artifact exhaustively covers the official CoA catalog of 69 specializations. The same specialization label appears under more than one class in the artifact, and the artifact contains 87 class/spec associations rather than a canonical class-to-specialization catalog.

## Classes represented

```text
Barbarian
Blood Mage
Chronomancer
Cultist
Demon Hunter
Felsworn
Fleshwarden
Guardian
Knight of Xoroth
Monk
Necromancer
Primalist
Prophet
Pyromancer
Ranger
Reaper
Runemaster
Son of Arugal
Spirit Mage
Starcaller
Stormbringer
Sun Cleric
Templar
Tinker
Venomancer
Wildwalker
Witch Doctor
Witch Hunter
```

## Utility categories represented

The supplied descriptions contain candidate evidence for categories including:

```text
raid damage modifiers
attack power / spell power
melee and ranged haste
spell haste
critical strike chance
hit chance
armor
maximum health
healing received
raid healing
absorption shields
damage reduction
resource restoration
movement speed
movement-impairing resistance or immunity
mass dispel and cleansing
encounter-specific or target-specific utility
```

These labels are provisional summaries created by the source artifact. They do not establish stacking groups, equivalence, runtime magnitude, target scope, uptime, encounter value or provider reliability.

## Required verification model

Every talent or ability must be promoted independently through evidence such as:

```text
exact CoA Armory/talent-grid source observation
-> exact spell/talent identity
-> immutable source payload and hash
-> combat-log observation from CoA
-> provider/target attribution
-> actual application and uptime
-> stacking/overwrite/coexistence tests
-> contradictory-observation review
-> trust decision
```

At minimum, verification must distinguish:

- talent text from runtime behavior;
- theoretical availability from actual character selection;
- character selection from actual use;
- use from successful application to intended targets;
- nominal raid scope from observed coverage;
- similar wording from verified equivalence;
- one observation from reproducible behavior;
- public external observations from Argentum-specific execution reliability.

## Current allowed use

Allowed:

- research backlog;
- candidate capability taxonomy;
- manual raid-leader reference;
- identifying which effects require capture and verification;
- designing future normalized capability records;
- comparing talent-grid candidates with combat-log observations.

Not allowed:

- automatic roster scoring;
- declaring a class/spec mandatory;
- declaring effects equivalent or mutually exclusive;
- assuming the displayed magnitude is current runtime truth;
- inferring utility coverage from class/spec presence alone;
- claiming all 69 CoA specializations are covered;
- treating the latest 30 public logs as a representative global sample.

## CoA-only boundary

This baseline is limited to entities represented as Conquest of Azeroth classes, specializations, talents and abilities in the supplied artifact and reviewed CoA sources.

Do not add or infer systems belonging to Bronzebeard or other Ascension realms. In particular, Mystic Enchants are outside the CoA domain unless a future exact CoA source independently proves otherwise.

## Future replacement

This provisional document should eventually be replaced by a generated, versioned capability corpus bound to:

- verified CoA class and specialization identities;
- verified talent-grid payloads;
- exact talent/spell identifiers;
- version or phase where available;
- independent combat-log observations;
- explicit stacking and scope reviews;
- per-provider reliability and encounter relevance;
- source and algorithm versions.
