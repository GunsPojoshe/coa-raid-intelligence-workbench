import pytest

from coa_workbench.analytics.trust import (
    DataTrustStatus,
    UntrustedDataError,
    is_canonical,
    require_canonical,
)


def test_only_corroborated_and_confirmed_are_canonical() -> None:
    assert is_canonical(DataTrustStatus.CORROBORATED)
    assert is_canonical(DataTrustStatus.CONFIRMED)
    assert not is_canonical(DataTrustStatus.LEGACY_UNVERIFIED)
    assert not is_canonical(DataTrustStatus.OBSERVED)
    assert not is_canonical(DataTrustStatus.CANDIDATE)
    assert not is_canonical(DataTrustStatus.CONTRADICTED)
    assert not is_canonical(DataTrustStatus.REJECTED)


def test_require_canonical_rejects_mixed_statuses() -> None:
    with pytest.raises(UntrustedDataError, match="legacy_unverified"):
        require_canonical(
            [DataTrustStatus.CONFIRMED, DataTrustStatus.LEGACY_UNVERIFIED],
            context="provider capabilities",
        )


def test_require_canonical_accepts_confirmed_evidence() -> None:
    require_canonical(
        [DataTrustStatus.CORROBORATED, DataTrustStatus.CONFIRMED],
        context="provider capabilities",
    )
