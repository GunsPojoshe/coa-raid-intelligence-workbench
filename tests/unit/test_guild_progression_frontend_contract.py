from __future__ import annotations

from coa_workbench.collector.guild_progression_frontend_contract import analyze_frontend_contract


def _asset() -> str:
    return r'''
const uo={},KB="https://coa.ascensionlogs.gg/api",Ft=Un.create({baseURL:KB,timeout:3e5});
const cv={noCacheEndpoints:["/api/guilds/progression","/api/analytics/"]};
function main(){const W={};b!==null&&(W.phaseId=b),o&&y&&(W.difficulty=y),l&&w!=="all"&&(W.bracket=w),j&&(W.location=j),c&&C&&(W.realm=C);const z=await Ft.get("/guilds/progression/rankings",{params:W})}
function clears(){const z={page:P};b!==null&&(z.phaseId=b),o&&y&&(z.difficulty=y),l&&w!=="all"&&(z.bracket=w),j&&(z.location=j),c&&C&&(z.realm=C);const V=await Ft.get("/guilds/progression/full-clears",{params:z})}
const Boss=({bossId:e})=>{const J={page:S};A!==null&&(J.phaseId=A),l&&x&&(J.difficulty=x),c&&k!=="all"&&(J.bracket=k),u&&v&&(J.realm=v);const q=await Ft.get(`/guilds/progression/rankings/${e}`,{params:J})};
const Guilds=()=>{const g=c==="all"?{}:{bracket:c},b=(await Ft.get("/guilds/progression/rankings",{params:g})).data};
'''


def test_contract_identifies_real_direct_get_calls() -> None:
    result = analyze_frontend_contract(_asset())

    assert result["legacy_prefix_literal_occurrence_count"] == 1
    assert result["legacy_prefix_cache_exclusion_occurrence_count"] == 1
    assert result["legacy_prefix_direct_request_occurrence_count"] == 0
    assert result["direct_progression_request_count"] == 4
    assert result["direct_progression_methods"] == ["GET"]
    assert result["post_request_observed"] is False
    assert result["bounded_rankings_get_contract_observed"] is True

    by_route = {row["route_template"]: row for row in result["direct_requests"]}
    assert by_route["/api/guilds/progression/rankings"]["occurrence_count"] == 2
    assert by_route["/api/guilds/progression/rankings"]["parameter_key_sets"] == [
        ["bracket"],
        ["bracket", "difficulty", "location", "phaseId", "realm"],
    ]
    assert by_route["/api/guilds/progression/rankings"]["explicit_empty_parameter_branch_observed"]
    assert by_route["/api/guilds/progression/full-clears"]["parameter_key_sets"] == [
        ["bracket", "difficulty", "location", "page", "phaseId", "realm"]
    ]
    assert by_route["/api/guilds/progression/rankings/{bossId}"]["parameter_key_sets"] == [
        ["bracket", "difficulty", "page", "phaseId", "realm"]
    ]
