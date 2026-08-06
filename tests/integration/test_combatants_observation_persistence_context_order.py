from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from coa_workbench.collector.combatants_candidate_promotion_compat import (
    promote_observed_combatants_info_candidates,
)
from coa_workbench.storage.migrations import apply_migrations


duckdb = pytest.importorskip("duckdb")

_CONTEXT_DESIGN_ID = "coa-combatants-instance-context-v1"


def _support_module() -> ModuleType:
    path = Path(__file__).with_name("test_combatants_observation_persistence.py")
    spec = importlib.util.spec_from_file_location("combatants_persistence_test_support", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load combatants persistence test support")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_persists_real_extractor_context_arrays_sorted_independently(tmp_path: Path) -> None:
    support = _support_module()
    promotion_path, extraction_receipt_path, private_path, _ = support._packet(tmp_path)

    private_payload = json.loads(private_path.read_text(encoding="utf-8"))
    context_rows = private_payload["observations"][_CONTEXT_DESIGN_ID]
    for row in context_rows:
        row["linked_actor_ids"] = sorted(row["linked_actor_ids"])
        row["linked_source_actor_ids"] = sorted(row["linked_source_actor_ids"], key=int)
        row["source_raw_match_paths"] = sorted(row["source_raw_match_paths"])
    _write(private_path, private_payload)

    extraction_receipt = json.loads(extraction_receipt_path.read_text(encoding="utf-8"))
    extraction_receipt["private_extraction_sha256"] = hashlib.sha256(
        private_path.read_bytes()
    ).hexdigest()
    _write(extraction_receipt_path, extraction_receipt)

    promotion = promote_observed_combatants_info_candidates(
        extraction_receipt_path,
        private_path,
        reviewed_by="GunsPojoshe (operator), OpenAI-assisted review",
        reviewed_at="2026-07-30T01:44:41+03:00",
    )
    _write(promotion_path, promotion)

    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    apply_migrations(database, root / "migrations")
    support._seed_core(database, private_payload)

    result = support._persist(
        root,
        database,
        promotion_path,
        extraction_receipt_path,
        private_path,
    )

    assert result["summary"]["persisted_observation_count"] == 1343
    assert result["summary"]["actor_build_observation_count"] == 1339
    assert result["summary"]["linked_actor_count"] == 11
    assert result["summary"]["transaction_committed"] is True
    assert result["summary"]["core_entity_mutation_performed"] is False
