# Documentation overhaul scope — 2026-08-26

This short file records what “documentation fully updated” means for the current overhaul so later sessions can distinguish intentionally historical files from stale canonical files.

## Rewritten canonical entry points

```text
README.md
AGENTS.md
docs/CURRENT_PARADIGM.md
docs/DOCUMENTATION_INDEX.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/CONTINUATION_PROMPT.md
docs/NEXT_CHAT_HANDOFF.md
docs/OFFICIAL_PUBLIC_API.md
docs/UPSTREAM_ASCENSION_LOGS_EVIDENCE.md
docs/LOCAL_WORKSPACE_BOUNDARY.md
docs/BROWSER_OBSERVATORY.md
docs/CI_OPERATIONS.md
docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md
CHANGELOG.md
```

## Added integrity tooling

```text
docs/PROJECT_INTEGRITY_AUDIT_2026-08-26.md
docs/LOCAL_WORKSPACE_AUDIT.md
scripts/inventory_local_workspace.py
evidence/real-data/coa-public-api-statistics-shape-real.json
```

## Intentionally not rewritten as current-state documents

Dated experiment/milestone documents remain historical evidence. Their old “next gate” text is not edited because rewriting it would falsify project history. `docs/DOCUMENTATION_INDEX.md` explicitly classifies them and prevents them from outranking current canonical state.

Long-form stable product definition and ADRs are retained unless a concrete domain decision has changed; current source/acquisition priority is supplied by `docs/CURRENT_PARADIGM.md`.

## Local limitation

GitHub tooling cannot inspect ignored/untracked operator files. The tracked-tree audit is completed remotely; exact workstation integrity becomes complete after the generated private local manifest is reviewed.
