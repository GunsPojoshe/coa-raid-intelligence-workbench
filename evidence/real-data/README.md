# Real-data evidence checkpoint

Дата актуализации: **2026-07-30**.

Этот каталог содержит versioned scalar-free receipts и описание trust boundary для real CoA Logs pipeline. Он делает результат проверяемым без публикации private payload contents.

## Versioned artifacts

```text
observed-combatants-info-candidate-extraction.json
```

Receipt содержит:

- exact source payload hash и schema fingerprint;
- source/design filenames;
- private extraction filename и SHA-256;
- counts по каждому design unit;
- boolean integrity gates;
- decision boundary;
- отсутствие source scalar values в receipt.

## Local-only artifacts

Следующие каталоги могут содержать names, GUIDs, talents, gear, report/encounter identifiers, normalized entities или DuckDB:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Они gitignored. Полный локальный контекст разрешено использовать для анализа, но Git по умолчанию хранит только минимальный воспроизводимый evidence layer.

Never commit credentials, cookies, tokens, Authorization headers, browser profiles, `.env` secrets or unsanitized HAR.

## Observed report slice

Routes:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

Bindings:

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

## Completed report/encounter evidence chain

```text
published mappings: 2
field contracts:    54

normalized:
  reports:       2
  encounters:   15
  actors:       31
  participants: 31
  aura_events:   0
  rejects:       0

reconstructed:
  reports:       1
  encounters:   14
  actors:       31
  participants: 31
  aura_events:   0
  rejects:       0
  field conflicts: 0

persisted:
  canonical entity observations: 77
  transaction committed: true
```

The full normalized/reconstructed records and DuckDB are private local artifacts.

## Combatants-info evidence chain

```text
deep review:
  scope candidates: 12
  present scopes:   10
  direct fields:    56

field selection:
  groups:            8
  selected fields:  37
  deferred fields:  19

mapping design:
  dedicated units:   6
  core mutations:    forbidden
```

Exact candidate extraction:

```text
source matches:       1350
output observations:  1343
deduplicated matches: 7
linked actors:        11
actor name matches:   11
integrity checks:     12/12
core mutations:       0
```

Per design unit:

```text
actor enrichment:       11
instance context:         4
talent container:        11
classless talent rank:  564
hero build entry:       564
gear slot:              189
```

## Trust boundary

Verified for this exact payload:

- archive and observation manifest;
- route context;
- persisted report/encounter references;
- stable actor IDs;
- exact existing actor names;
- selected field types;
- source counts;
- record hashes;
- no core mutation.

Not verified:

- companion-addon provenance;
- nested collection semantics;
- global uniqueness of nested IDs;
- gameplay meaning of talents/gear;
- automatic persistence or promotion;
- canonical build snapshot projection;
- mechanic semantics;
- planner scoring.

## Next evidence artifact

The next versioned artifact should be a scalar-free manual promotion/persistence receipt for the six immutable combatants observation types. It must reference the exact private extraction SHA-256 and preserve all current semantic boundaries.
