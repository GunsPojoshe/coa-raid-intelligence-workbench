from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class EvidenceCohort(StrEnum):
    GLOBAL = "global"
    GUILD = "guild"


@dataclass(frozen=True, slots=True)
class EvidenceWeightPolicy:
    version: str
    recency_half_life_days: float
    guild_weight: float
    global_weight: float
    min_independent_reports: int
    min_independent_encounters: int
    confirmation_threshold: float
    rejection_threshold: float

    def __post_init__(self) -> None:
        if self.recency_half_life_days <= 0:
            raise ValueError("recency_half_life_days must be positive")
        if self.guild_weight <= 0 or self.global_weight <= 0:
            raise ValueError("cohort weights must be positive")
        if self.min_independent_reports < 1 or self.min_independent_encounters < 1:
            raise ValueError("minimum evidence counts must be positive")
        if not 0 <= self.rejection_threshold < self.confirmation_threshold <= 1:
            raise ValueError("thresholds must satisfy 0 <= rejection < confirmation <= 1")


DEFAULT_EVIDENCE_WEIGHT_POLICY = EvidenceWeightPolicy(
    version="evidence-weight-v1",
    recency_half_life_days=90.0,
    guild_weight=1.5,
    global_weight=1.0,
    min_independent_reports=3,
    min_independent_encounters=5,
    confirmation_threshold=0.85,
    rejection_threshold=0.20,
)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def recency_weight(
    observed_at: datetime,
    *,
    reference_at: datetime,
    half_life_days: float,
) -> float:
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    observed = ensure_utc(observed_at)
    reference = ensure_utc(reference_at)
    age_seconds = max(0.0, (reference - observed).total_seconds())
    age_days = age_seconds / 86_400.0
    return math.pow(0.5, age_days / half_life_days)


def observation_weight(
    observed_at: datetime,
    *,
    reference_at: datetime,
    cohort: EvidenceCohort | str,
    policy: EvidenceWeightPolicy = DEFAULT_EVIDENCE_WEIGHT_POLICY,
    quality_multiplier: float = 1.0,
) -> float:
    if quality_multiplier < 0:
        raise ValueError("quality_multiplier cannot be negative")
    normalized_cohort = EvidenceCohort(cohort)
    cohort_weight = (
        policy.guild_weight
        if normalized_cohort is EvidenceCohort.GUILD
        else policy.global_weight
    )
    return (
        recency_weight(
            observed_at,
            reference_at=reference_at,
            half_life_days=policy.recency_half_life_days,
        )
        * cohort_weight
        * quality_multiplier
    )
