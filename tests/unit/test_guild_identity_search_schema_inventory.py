from __future__ import annotations

import json

import pytest

from coa_workbench.collector.guild_identity_search_schema_inventory import (
    _field_roles,
    _inventory_fields,
    _value_kind,
)


def _row_by_path(rows: list[dict[str, object]], path: str) -> dict[str, object]:
    matches = [row for row in rows if row["path"] == path]
    assert len(matches) == 1
    return matches[0]


def test_inventory_fields_reports_shape_and_match_flags_without_values() -> None:
    guild_object = {
        "display_name": "ARGENTUM",
        "guild_identifier": "private-source-id",
        "region": "EU",
        "metadata": {"title": "Argentum Raiders"},
    }

    rows = _inventory_fields(
        guild_object,
        expected_guild_label="Argentum",
        source_guild_id="private-source-id",
    )

    display_name = _row_by_path(rows, "$.guilds[].display_name")
    assert display_name["value_kind"] == "string"
    assert display_name["exact_label_match"] is False
    assert display_name["casefold_label_match"] is True
    assert display_name["contains_label_casefold"] is True
    assert display_name["field_roles"] == ["label_candidate"]

    identifier = _row_by_path(rows, "$.guilds[].guild_identifier")
    assert identifier["source_id_match"] is True
    assert identifier["field_roles"] == ["id_candidate"]

    nested_title = _row_by_path(rows, "$.guilds[].metadata.title")
    assert nested_title["contains_label_casefold"] is True

    encoded = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    assert "private-source-id" not in encoded
    assert "ARGENTUM" not in encoded
    assert "Argentum Raiders" not in encoded
    assert all(row["contains_scalar_value"] is False for row in rows)


def test_inventory_fields_aggregates_repeated_array_shapes() -> None:
    guild_object = {
        "aliases": ["Argentum EU", "Argentum US"],
        "members": [{"character_id": 1}, {"character_id": 2}],
    }

    rows = _inventory_fields(
        guild_object,
        expected_guild_label="Argentum",
        source_guild_id="not-present",
    )

    alias_rows = [row for row in rows if row["path"] == "$.guilds[].aliases[]"]
    assert len(alias_rows) == 1
    assert alias_rows[0]["occurrence_count"] == 2
    assert alias_rows[0]["contains_label_casefold"] is True

    member_id_rows = [
        row for row in rows if row["path"] == "$.guilds[].members[].character_id"
    ]
    assert len(member_id_rows) == 1
    assert member_id_rows[0]["occurrence_count"] == 2
    assert member_id_rows[0]["source_id_match"] is False


def test_inventory_helpers_classify_json_types_and_roles() -> None:
    assert _value_kind(None) == "null"
    assert _value_kind(False) == "boolean"
    assert _value_kind(1) == "integer"
    assert _value_kind(1.5) == "number"
    assert _value_kind("value") == "string"
    assert _value_kind({}) == "object"
    assert _value_kind([]) == "array"
    assert _field_roles("guildName") == ["label_candidate"]
    assert _field_roles("guild_identifier") == ["id_candidate"]
    assert _field_roles("realm") == ["location_candidate"]
    assert _field_roles("faction") == ["faction_candidate"]

    with pytest.raises(ValueError, match="unsupported JSON value type"):
        _value_kind(object())
