# Conquest of Azeroth domain boundary

## Status

```text
status: canonical
scope: Conquest of Azeroth only
last_reviewed: 2026-08-04
```

This document defines the canonical gameplay and source boundary for CoA Raid Intelligence Workbench.

## Included domain

The product is exclusively for **Conquest of Azeroth**.

Canonical domain entities may include only evidence-backed CoA concepts such as:

- CoA classes;
- CoA specializations;
- class-tree and specialization-tree talents;
- CoA abilities and spell effects;
- CoA items, equipment and item effects;
- CoA characters, realms and guilds;
- CoA raids, bosses, difficulties and encounters;
- CoA combat-log observations;
- CoA Ascension Logs reports, rankings, statistics, character pages and Armory data;
- CoA BisBeard talent, item, gear and BiS planning data;
- locally derived conclusions that remain explicitly separated from source facts.

No entity becomes canonical merely because it exists on another Ascension realm, in a shared frontend, in a reused FAQ, or in a similarly named class/spec system.

## Explicitly excluded

Unless independently observed in an exact CoA source and separately reviewed, the following are outside the project domain:

- Bronzebeard-specific mechanics;
- Mystic Enchants and Mystic Scroll systems;
- Classless Ascension freeform ability selection;
- Hero Architect assumptions;
- original-nine-class realm mechanics;
- Bronzebeard tank-role detection rules;
- class/spec examples copied from Bronzebeard documentation;
- mechanics inferred only from shared Ascension branding or shared UI text.

Mystic Enchants are not part of the current CoA model.

## Source hierarchy

### Primary observation sources

- exact immutable CoA Ascension Logs payloads;
- exact CoA combat logs;
- exact CoA Armory payloads;
- exact CoA talent-grid payloads;
- exact CoA report, encounter, rankings, statistics, character and guild payloads once discovered and reviewed.

### Secondary planning source

CoA BisBeard may provide talent, item, gear and BiS planning data. It is a planning/reference source, not automatic proof of runtime combat behavior.

### Provisional references

User-supplied summaries, exported HTML, screenshots, manually assembled catalogs and talent descriptions may be versioned as provisional references when their limitations are explicit.

They may guide capture and review work but may not enter canonical planner scoring until verified.

## Required separation of facts

Every capability record must distinguish:

```text
source text or displayed talent description
observed character selection
observed combat use
observed application to target
observed uptime and coverage
observed stacking or overwrite behavior
local interpretation
planner recommendation
```

These are different evidence layers.

## CoA Armory boundary

Verified Armory extraction currently proves only fields and relationships explicitly accepted by the versioned mappings and review.

The existing reviewed mappings establish reproducible extraction for selected character identity, upstream role, active specialization index, resolved talent ranks, talent-grid tree identity and talent nodes. They do not prove runtime magnitude, stacking, scope, provider equivalence or planner criticality.

Deferred or new fields require their own capture and review.

## CoA utility boundary

A class/spec/talent may be listed as a candidate provider when it appears in a reviewed CoA talent-grid source or a clearly marked provisional reference.

A current raid is considered to have a capability only after the applicable policy is satisfied. Future policy may combine:

- verified build selection;
- recent combat-log use;
- successful target application;
- uptime and target coverage;
- reliability across attempts;
- encounter relevance;
- explicit manual override by the raid leader.

Class or specialization presence alone never proves capability coverage.

## Shared or contaminated documentation

Shared Ascension pages and reused FAQ content must be treated as potentially cross-realm.

Before using a statement as CoA truth, require at least one of:

- exact CoA route/payload evidence;
- exact CoA page content bound to a reviewed source;
- exact CoA combat-log evidence;
- exact CoA talent-grid/Armory evidence;
- independent official CoA-specific documentation.

If realm scope is ambiguous, classify the statement as unverified and exclude it from scoring.

## Naming and identity

Canonical character identity must retain at least the source-supported name and realm relationship. Display name alone is not a global identifier.

Class, specialization and role must remain distinct:

- class is a CoA class identity;
- specialization is a CoA specialization identity;
- role may be source-provided, manually assigned or derived from encounter behavior;
- role derivation requires a versioned CoA-specific algorithm and supporting evidence.

## Product boundary

The system may analyze:

- roster composition;
- build and equipment state;
- combat performance;
- encounter mechanics;
- utility application;
- player reliability;
- external benchmarks;
- attendance-aware roster completion.

It must not claim certainty where the available CoA data supports only a candidate or correlation.

## Canonical rule

```text
CoA source observation != general Ascension truth
shared Ascension text != CoA mechanic proof
class/spec presence != capability coverage
provisional utility catalog != planner scoring input
```
