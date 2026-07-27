from coa_workbench.normalizer import (
    NormalizationMapping,
    inspect_payload,
    normalize_payload,
    reconstruct_aura_intervals,
    structure_fingerprint,
)


def fixture_payload():
    return {
        "report": {"id": "R1", "created": "2026-07-27"},
        "encounters": [{"id": "E1", "report": "R1", "boss": "Boss", "duration": 1000}],
        "actors": [
            {"id": "A1", "name": "Caster", "type": "player"},
            {"id": "A2", "name": "Target", "type": "player"},
        ],
        "participants": [
            {"encounter": "E1", "actor": "A1"},
            {"encounter": "E1", "actor": "A2"},
        ],
        "events": [
            {"encounter": "E1", "ts": 100, "type": "SPELL_AURA_APPLIED", "source": "A1", "target": "A2", "spell": 77, "stacks": 1},
            {"encounter": "E1", "ts": 200, "type": "SPELL_AURA_REFRESH", "source": "A1", "target": "A2", "spell": 77, "stacks": 2},
            {"encounter": "E1", "ts": 300, "type": "SPELL_AURA_REMOVED", "source": "A1", "target": "A2", "spell": 77},
            {"encounter": "E1", "ts": 400, "type": "UNKNOWN", "source": "A1", "target": "A2", "spell": 77},
        ],
    }


def fixture_mapping(payload):
    return NormalizationMapping.from_dict(
        {
            "mapping_id": "synthetic-v1",
            "source_code": "test",
            "schema_fingerprint": structure_fingerprint(payload),
            "mapping_version": "1",
            "status": "verified",
            "entities": {
                "reports": {"collection": "/report", "fields": {"source_report_id": "/id", "raid_date": "/created"}, "required": ["source_report_id"]},
                "encounters": {"collection": "/encounters/*", "fields": {"source_encounter_id": "/id", "source_report_id": "/report", "boss_name": "/boss", "duration_ms": "/duration"}, "required": ["source_encounter_id", "source_report_id"]},
                "actors": {"collection": "/actors/*", "fields": {"source_actor_id": "/id", "nickname": "/name", "actor_type": "/type"}, "required": ["source_actor_id"]},
                "participants": {"collection": "/participants/*", "fields": {"source_encounter_id": "/encounter", "source_actor_id": "/actor"}, "required": ["source_encounter_id", "source_actor_id"]},
                "aura_events": {"collection": "/events/*", "fields": {"source_encounter_id": "/encounter", "timestamp_ms": "/ts", "event_type": "/type", "source_actor_id": "/source", "target_actor_id": "/target", "spell_id": "/spell", "stacks": "/stacks", "event_ordinal": "@index"}, "required": ["source_encounter_id", "timestamp_ms", "event_type", "spell_id"]},
            },
            "event_type_map": {
                "SPELL_AURA_APPLIED": "APPLIED",
                "SPELL_AURA_REFRESH": "REFRESH",
                "SPELL_AURA_REMOVED": "REMOVED",
            },
        }
    )


def test_inspector_only_proposes_candidates():
    inspection = inspect_payload(fixture_payload())
    assert inspection.schema_fingerprint
    assert inspection.collection_count >= 4
    assert any(item.path == "/events" for item in inspection.candidates)


def test_verified_mapping_normalizes_and_rejects_unknown_event():
    payload = fixture_payload()
    batch = normalize_payload(payload, fixture_mapping(payload), schema_fingerprint=structure_fingerprint(payload))
    assert batch.counts() == {"reports": 1, "encounters": 1, "actors": 2, "participants": 2, "aura_events": 3, "rejects": 1}
    assert batch.rejects[0]["reason"] == "unmapped_event_type"


def test_candidate_mapping_is_blocked():
    payload = fixture_payload()
    mapping = NormalizationMapping.from_dict(
        {"mapping_id": "x", "source_code": "test", "schema_fingerprint": structure_fingerprint(payload), "mapping_version": "1", "status": "candidate", "entities": {}, "event_type_map": {}}
    )
    try:
        normalize_payload(payload, mapping, schema_fingerprint=structure_fingerprint(payload))
    except ValueError as exc:
        assert "not verified" in str(exc)
    else:
        raise AssertionError("candidate mapping was accepted")


def test_aura_state_reconstructs_refresh_and_remove():
    payload = fixture_payload()
    batch = normalize_payload(payload, fixture_mapping(payload), schema_fingerprint=structure_fingerprint(payload))
    result = reconstruct_aura_intervals(batch.aura_events)
    assert len(result.intervals) == 1
    interval = result.intervals[0]
    assert (interval.started_at_ms, interval.ended_at_ms) == (100, 300)
    assert interval.refresh_count == 1
    assert interval.max_stack_count == 2
    assert interval.termination_reason == "removed"
    assert result.anomalies == ()
