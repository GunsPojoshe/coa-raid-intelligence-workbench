from __future__ import annotations

import os
from typing import Any, Iterable

from coa_workbench.web.effects import analyze_composition as analyze_legacy_composition

LEGACY_EFFECTS_ENV = "COA_ENABLE_LEGACY_EFFECTS"


def legacy_effects_enabled() -> bool:
    return os.getenv(LEGACY_EFFECTS_ENV, "").strip().casefold() in {"1", "true", "yes", "on"}


def unavailable_analytics() -> dict[str, Any]:
    return {
        "coverage": {
            "availability": "unavailable",
            "reason_code": "canonical_log_evidence_not_loaded",
            "data_trust_status": "legacy_unverified",
            "total_effects": 0,
            "covered_effects": 0,
            "missing_effects": 0,
            "coverage_percent": 0.0,
            "categories": {},
            "priorities": {},
            "covered": [],
            "missing": [],
        },
        "recommendations": [],
        "scoring": {
            "algorithm": "disabled-unverified-data",
            "canonical": False,
            "legacy_available_for_forensics": True,
            "legacy_enable_env": LEGACY_EFFECTS_ENV,
            "role_targets_used": False,
        },
    }


def analyze_composition(
    slots: Iterable[Any],
    *,
    top_n: int = 3,
) -> dict[str, Any]:
    if not legacy_effects_enabled():
        return unavailable_analytics()

    result = analyze_legacy_composition(slots, top_n=top_n)
    result["coverage"]["availability"] = "forensic_only"
    result["coverage"]["data_trust_status"] = "legacy_unverified"
    result["scoring"]["canonical"] = False
    result["scoring"]["algorithm"] = "legacy-missing-effect-priority-v1"
    result["scoring"]["warning"] = (
        "Historical static provider links are enabled for non-canonical comparison only."
    )
    return result
