from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from coa_workbench.collector.report_slice_scope_review import (
    build_observed_report_slice_scope_review,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a scalar-free direct-field review packet for explicit observed "
            "report-slice scopes. No network requests are performed."
        )
    )
    parser.add_argument(
        "--mapping-review",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-mapping-review.json"),
    )
    parser.add_argument(
        "--mapping-summary",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-mapping-summary.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-scope-review.json"),
    )
    parser.add_argument(
        "--text-output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-scope-review.txt"),
    )
    return parser.parse_args()


def _join(values: object) -> str:
    if not isinstance(values, list):
        return ""
    return ",".join(str(value) for value in values)


def _boolean(value: object) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def _render(review: dict[str, Any]) -> str:
    totals = review["summary"]
    boundary = review["decision_boundary"]
    lines = [
        "OBSERVED_REPORT_SLICE_SCOPE_REVIEW",
        f"schema_version={review['schema_version']}",
        f"review_kind={review['review_kind']}",
        f"endpoint_count={totals['endpoint_count']}",
        f"scope_candidate_count={totals['scope_candidate_count']}",
        f"direct_field_count={totals['direct_field_count']}",
        f"all_archives_consistent={_boolean(totals['all_archives_consistent'])}",
        "contains_source_scalar_values="
        f"{_boolean(totals['contains_source_scalar_values'])}",
        "semantic_verification_required="
        f"{_boolean(totals['semantic_verification_required'])}",
        f"normalization_allowed={_boolean(totals['normalization_allowed'])}",
        "ready_for_manual_field_selection="
        f"{_boolean(totals['ready_for_manual_field_selection'])}",
        "automatic_scope_selection="
        f"{_boolean(boundary['automatic_scope_selection'])}",
        "automatic_field_selection="
        f"{_boolean(boundary['automatic_field_selection'])}",
        f"can_promote={_boolean(boundary['can_promote'])}",
        "",
        "SCOPE_CANDIDATES",
    ]
    for scope in review["scopes"]:
        scope_shape = scope["scope_shape"]
        summary = scope["summary"]
        lines.append(
            " | ".join(
                [
                    f"kind={scope['endpoint_kind']}",
                    f"scope={scope['scope']}",
                    f"review_label={scope['review_label']}",
                    f"types={_join(scope_shape['types'])}",
                    f"occurrence_count={summary['scope_occurrence_count']}",
                    f"direct_field_count={summary['direct_field_count']}",
                    "nullable_direct_field_count="
                    f"{summary['nullable_direct_field_count']}",
                    f"review_status={scope['review_status']}",
                    f"semantic_status={scope['semantic_status']}",
                ]
            )
        )

    lines.extend(["", "DIRECT_FIELDS"])
    for scope in review["scopes"]:
        for field in scope["direct_fields"]:
            lines.append(
                " | ".join(
                    [
                        f"kind={scope['endpoint_kind']}",
                        f"scope={scope['scope']}",
                        f"name={field['name']}",
                        f"path={field['path']}",
                        f"types={_join(field['types'])}",
                        f"nullable={_boolean(field['nullable'])}",
                        f"occurrence_count={field['occurrence_count']}",
                        "observed_on_all_scope_occurrences="
                        f"{_boolean(field['observed_on_all_scope_occurrences'])}",
                        f"is_array={_boolean(field['is_array'])}",
                        f"is_object={_boolean(field['is_object'])}",
                    ]
                )
            )
    return "\n".join(lines) + "\n"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    args = _arguments()
    review = build_observed_report_slice_scope_review(
        args.mapping_review,
        args.mapping_summary,
    )
    _write_text(
        args.output,
        json.dumps(review, indent=2, sort_keys=True) + "\n",
    )
    rendered = _render(review)
    _write_text(args.text_output, rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
