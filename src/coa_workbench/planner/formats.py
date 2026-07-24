from __future__ import annotations

from enum import StrEnum

MAX_RAID_SLOTS = 40


class RaidFormat(StrEnum):
    FLEX = "FLEX"
    TEN = "10"
    TWENTY_FIVE = "25"
    FORTY = "40"


def resolve_target_size(
    raid_format: RaidFormat | str,
    target_size: int | None = None,
    *,
    flex_min: int = 1,
    flex_max: int = MAX_RAID_SLOTS,
) -> int:
    """Resolve and validate a raid target size without embedding role rules."""
    fmt = RaidFormat(str(raid_format).upper())
    fixed_sizes = {
        RaidFormat.TEN: 10,
        RaidFormat.TWENTY_FIVE: 25,
        RaidFormat.FORTY: 40,
    }
    if fmt in fixed_sizes:
        expected = fixed_sizes[fmt]
        if target_size is not None and target_size != expected:
            raise ValueError(f"Format {fmt.value} requires target_size={expected}, got {target_size}")
        return expected

    if target_size is None:
        raise ValueError("FLEX requires an explicit target_size")
    if not flex_min <= target_size <= flex_max:
        raise ValueError(
            f"FLEX target_size must be within configured range {flex_min}..{flex_max}, got {target_size}"
        )
    return target_size


def active_slot_flags(target_size: int, *, max_slots: int = MAX_RAID_SLOTS) -> tuple[bool, ...]:
    """Return the canonical 40-slot ActiveSlot mask."""
    if not 1 <= target_size <= max_slots:
        raise ValueError(f"target_size must be between 1 and {max_slots}, got {target_size}")
    return tuple(slot_no <= target_size for slot_no in range(1, max_slots + 1))
