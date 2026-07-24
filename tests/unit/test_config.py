from pathlib import Path

from coa_workbench.config import load_raid_profiles


def test_checked_in_profiles_validate() -> None:
    root = Path(__file__).resolve().parents[2]
    config = load_raid_profiles(root / "config" / "raid_profiles.yaml")
    by_code = {profile.code: profile for profile in config.raid_profiles}
    assert by_code["legacy_v9_25"].target_size == 25
    assert by_code["legacy_v9_25"].spec_limit == 5
    assert by_code["legacy_v9_25"].class_limit == 3
    assert by_code["draft_10"].target_size == 10
    assert by_code["draft_40"].target_size == 40
