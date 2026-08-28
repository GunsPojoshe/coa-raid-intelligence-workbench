from datetime import datetime, timedelta, timezone

import pytest

from coa_workbench.analytics.weights import (
    DEFAULT_EVIDENCE_WEIGHT_POLICY,
    EvidenceCohort,
    observation_weight,
    recency_weight,
)


def test_recency_weight_halves_after_one_policy_half_life() -> None:
    reference = datetime(2026, 7, 27, tzinfo=timezone.utc)
    observed = reference - timedelta(days=DEFAULT_EVIDENCE_WEIGHT_POLICY.recency_half_life_days)
    assert recency_weight(
        observed,
        reference_at=reference,
        half_life_days=DEFAULT_EVIDENCE_WEIGHT_POLICY.recency_half_life_days,
    ) == pytest.approx(0.5)


def test_future_timestamp_does_not_receive_weight_above_one() -> None:
    reference = datetime(2026, 7, 27, tzinfo=timezone.utc)
    observed = reference + timedelta(days=10)
    assert recency_weight(
        observed,
        reference_at=reference,
        half_life_days=90,
    ) == pytest.approx(1.0)


def test_guild_observation_has_higher_weight_than_global_same_date() -> None:
    reference = datetime(2026, 7, 27, tzinfo=timezone.utc)
    observed = reference - timedelta(days=7)
    guild = observation_weight(
        observed,
        reference_at=reference,
        cohort=EvidenceCohort.GUILD,
    )
    global_sample = observation_weight(
        observed,
        reference_at=reference,
        cohort=EvidenceCohort.GLOBAL,
    )
    assert guild > global_sample
    assert guild / global_sample == pytest.approx(
        DEFAULT_EVIDENCE_WEIGHT_POLICY.guild_weight
        / DEFAULT_EVIDENCE_WEIGHT_POLICY.global_weight
    )


def test_quality_multiplier_cannot_be_negative() -> None:
    now = datetime(2026, 7, 27, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="cannot be negative"):
        observation_weight(
            now,
            reference_at=now,
            cohort=EvidenceCohort.GLOBAL,
            quality_multiplier=-0.1,
        )
