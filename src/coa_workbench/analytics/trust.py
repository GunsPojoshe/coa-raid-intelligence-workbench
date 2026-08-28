from __future__ import annotations

from enum import StrEnum
from typing import Iterable


class DataTrustStatus(StrEnum):
    LEGACY_UNVERIFIED = "legacy_unverified"
    OBSERVED = "observed"
    CANDIDATE = "candidate"
    CORROBORATED = "corroborated"
    CONFIRMED = "confirmed"
    CONTRADICTED = "contradicted"
    REJECTED = "rejected"


CANONICAL_TRUST_STATUSES = frozenset(
    {
        DataTrustStatus.CORROBORATED,
        DataTrustStatus.CONFIRMED,
    }
)


class UntrustedDataError(ValueError):
    pass


def normalize_trust_status(value: DataTrustStatus | str) -> DataTrustStatus:
    if isinstance(value, DataTrustStatus):
        return value
    return DataTrustStatus(value.strip().casefold())


def is_canonical(value: DataTrustStatus | str) -> bool:
    return normalize_trust_status(value) in CANONICAL_TRUST_STATUSES


def require_canonical(
    values: Iterable[DataTrustStatus | str],
    *,
    context: str,
) -> None:
    rejected = [normalize_trust_status(value).value for value in values if not is_canonical(value)]
    if rejected:
        unique = ", ".join(sorted(set(rejected)))
        raise UntrustedDataError(
            f"{context} contains non-canonical trust statuses: {unique}"
        )
