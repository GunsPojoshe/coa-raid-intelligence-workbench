from coa_workbench.collector.json_structure import (
    DYNAMIC_INTEGER_KEY_SEGMENT,
    SCHEMA_PATH_NORMALIZATION,
    json_structure_fingerprint,
    json_structure_shape,
    normalize_path_types,
)


def test_numeric_object_keys_do_not_change_structural_fingerprint() -> None:
    first = {
        "series": {
            "123": [{"amount": 1, "effective": 2}],
            "456": [{"amount": 3}],
        }
    }
    second = {
        "series": {
            "999": [{"amount": 9}],
            "1000": [{"amount": 8, "effective": 7}],
        }
    }

    assert json_structure_fingerprint(first) == json_structure_fingerprint(second)
    shape = json_structure_shape(first)
    assert DYNAMIC_INTEGER_KEY_SEGMENT in shape["series"]
    assert "123" not in str(shape)
    assert "456" not in str(shape)
    assert SCHEMA_PATH_NORMALIZATION == "numeric-object-key-wildcard-v1"


def test_fixed_field_changes_remain_structurally_visible() -> None:
    first = {"rows": {"123": [{"amount": 1}]}}
    second = {"rows": {"456": [{"amount": 1, "new_field": True}]}}

    assert json_structure_fingerprint(first) != json_structure_fingerprint(second)


def test_legacy_numeric_pointer_paths_merge_to_one_wildcard_path() -> None:
    normalized = normalize_path_types(
        {
            "/series/123/*/amount": ["int"],
            "/series/456/*/amount": ["float"],
            "/series/456/*/effective": ["int"],
        }
    )

    assert normalized == {
        "/series/{integer-key}/*/amount": ("float", "int"),
        "/series/{integer-key}/*/effective": ("int",),
    }
