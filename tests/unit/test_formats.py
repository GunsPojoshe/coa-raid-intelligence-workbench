import pytest

from coa_workbench.planner.formats import RaidFormat, active_slot_flags, resolve_target_size


@pytest.mark.parametrize(
    ("raid_format", "expected"),
    [(RaidFormat.TEN, 10), (RaidFormat.TWENTY_FIVE, 25), (RaidFormat.FORTY, 40)],
)
def test_fixed_formats(raid_format: RaidFormat, expected: int) -> None:
    assert resolve_target_size(raid_format) == expected
    flags = active_slot_flags(expected)
    assert len(flags) == 40
    assert sum(flags) == expected
    assert all(flags[:expected])
    assert not any(flags[expected:])


def test_fixed_format_rejects_conflicting_target() -> None:
    with pytest.raises(ValueError):
        resolve_target_size(RaidFormat.TWENTY_FIVE, 24)


def test_flex_requires_explicit_target_and_range() -> None:
    with pytest.raises(ValueError):
        resolve_target_size(RaidFormat.FLEX)
    assert resolve_target_size(RaidFormat.FLEX, 17, flex_min=10, flex_max=25) == 17
    with pytest.raises(ValueError):
        resolve_target_size(RaidFormat.FLEX, 26, flex_min=10, flex_max=25)
