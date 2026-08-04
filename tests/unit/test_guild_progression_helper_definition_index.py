from __future__ import annotations

from coa_workbench.collector.guild_progression_helper_definition_index import definition_candidates


def test_function_declaration() -> None:
    rows, evidence = definition_candidates(
        'function request(url, options){return fetch(url, options)};request("x");',
        "request",
    )
    assert rows[0]["kind"] == "function_declaration"
    assert rows[0]["binding_scope"] == "terminal_symbol"
    assert rows[0]["parameter_count"] == 2
    assert "fetch" in rows[0]["marker_classes"]
    assert evidence["definition_candidate_count"] == 1


def test_const_arrow_definition() -> None:
    rows, evidence = definition_candidates(
        (
            'const q=async(url,body)=>{return fetch(url,{method:"POST",'
            'body:JSON.stringify(body)})};q("x",{});'
        ),
        "q",
    )
    assert rows[0]["kind"] == "variable_function_assignment"
    assert rows[0]["async_candidate"] is True
    assert rows[0]["parameter_count"] == 2
    assert evidence["marker_classes"] == ["JSON.stringify", "body", "fetch", "method", "url"]


def test_member_assignment() -> None:
    rows, evidence = definition_candidates(
        'api.request=(url,data)=>{return client.post(url,{data})};api.request("x",{});',
        "api.request",
    )
    assert rows[0]["kind"] == "member_function_assignment"
    assert rows[0]["binding_scope"] == "full_chain"
    assert evidence["full_chain_occurrence_count_observed"] == 2
    assert evidence["terminal_symbol_occurrence_count_observed"] == 2


def test_object_method_definition() -> None:
    rows, evidence = definition_candidates(
        (
            'const api={request(url,params){return fetch(url,{method:"POST",'
            'body:params})}};api.request("x",{});'
        ),
        "api.request",
    )
    assert any(row["kind"] == "method_definition" for row in rows)
    assert "params" in evidence["marker_classes"]


def test_alias_assignment_is_hashed_not_resolved() -> None:
    rows, evidence = definition_candidates('const request=transport;request("x");', "request")
    alias = rows[0]
    assert alias["kind"] == "alias_assignment"
    assert alias["alias_target"] == "transport"
    assert len(alias["alias_target_sha256"]) == 64
    assert evidence["alias_candidate_count"] == 1


def test_symbol_occurrences_are_bounded() -> None:
    text = ";".join("request()" for _ in range(4))
    rows, evidence = definition_candidates(text, "request", max_symbol_occurrences=3)
    assert rows == []
    assert evidence["full_chain_occurrence_count_observed"] == 3
    assert evidence["full_chain_occurrence_scan_truncated"] is True


def test_candidate_count_is_bounded() -> None:
    text = ";".join(f"const x{i}=0" for i in range(5)) + ";" + ";".join(
        "request=(x)=>x" for _ in range(3)
    )
    rows, evidence = definition_candidates(text, "request", max_candidates=2)
    assert len(rows) == 2
    assert evidence["definition_candidate_scan_truncated"] is True


def test_definition_like_text_inside_strings_and_comments_is_ignored() -> None:
    rows, evidence = definition_candidates(
        'const text="function request(x){return x}";/* request=(x)=>x */request("x");',
        "request",
    )
    assert rows == []
    assert evidence["definition_candidate_count"] == 0


def test_symbol_bound_ignores_strings_and_comments() -> None:
    text = '"request request request";/* request request */request();'
    rows, evidence = definition_candidates(text, "request", max_symbol_occurrences=1)
    assert rows == []
    assert evidence["full_chain_occurrence_count_observed"] == 1
