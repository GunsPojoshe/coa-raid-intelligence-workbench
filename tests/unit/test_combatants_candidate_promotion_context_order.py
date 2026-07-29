from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.combatants_candidate_promotion_compat import (
    promote_observed_combatants_info_candidates,
)
from tests.unit.test_combatants_candidate_promotion import _packet

_CONTEXT_DESIGN_ID = "coa-combatants-instance-context-v1"


def _rewrite_receipt_hash(receipt_path: Path, private_path: Path) -> None:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["private_extraction_sha256"] = hashlib.sha256(private_path.read_bytes()).hexdigest()
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def _promote(receipt_path: Path, private_path: Path) -> dict[str, object]:
    return promote_observed_combatants_info_candidates(
        receipt_path,
        private_path,
        reviewed_by="GunsPojoshe (operator), OpenAI-assisted review",
        reviewed_at="2026-07-30T01:40:00+03:00",
    )


def test_accepts_context_actor_arrays_sorted_independently(tmp_path: Path) -> None:
    receipt_path, private_path = _packet(tmp_path)
    private_payload = json.loads(private_path.read_text(encoding="utf-8"))
    context_rows = private_payload["observations"][_CONTEXT_DESIGN_ID]
    for row in context_rows:
        row["linked_actor_ids"] = sorted(row["linked_actor_ids"])
        row["linked_source_actor_ids"] = sorted(
            row["linked_source_actor_ids"], key=int
        )
        row["source_raw_match_paths"] = sorted(row["source_raw_match_paths"])
    private_path.write_text(
        json.dumps(private_payload, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    _rewrite_receipt_hash(receipt_path, private_path)

    result = _promote(receipt_path, private_path)

    assert result["summary"]["output_observation_count"] == 1343
    assert result["summary"]["linked_actor_count"] == 11
    assert result["summary"]["all_integrity_checks_passed"] is True


def test_rejects_context_actor_set_mismatch_after_independent_sorting(tmp_path: Path) -> None:
    receipt_path, private_path = _packet(tmp_path)
    private_payload = json.loads(private_path.read_text(encoding="utf-8"))
    context_rows = private_payload["observations"][_CONTEXT_DESIGN_ID]
    first_row = context_rows[0]
    second_row = context_rows[1]
    first_row["linked_actor_ids"][0] = second_row["linked_actor_ids"][0]
    for row in context_rows:
        row["linked_actor_ids"] = sorted(row["linked_actor_ids"])
        row["linked_source_actor_ids"] = sorted(
            row["linked_source_actor_ids"], key=int
        )
        row["source_raw_match_paths"] = sorted(row["source_raw_match_paths"])
    private_path.write_text(
        json.dumps(private_payload, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    _rewrite_receipt_hash(receipt_path, private_path)

    with pytest.raises(ValueError, match="context actor linkage mismatch"):
        _promote(receipt_path, private_path)
