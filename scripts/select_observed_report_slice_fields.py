from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_slice_field_selection import (
    select_observed_report_slice_fields,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Select exact candidate report-slice fields from the scalar-free scope review "
            "and write candidate mapping files. No network requests are performed."
        )
    )
    parser.add_argument(
        "--scope-review",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-scope-review.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-field-selection.json"),
    )
    parser.add_argument(
        "--mapping-output-dir",
        type=Path,
        default=Path("data/exchange/out/candidate-mappings"),
    )
    return parser.parse_args()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    args = _arguments()
    selection = select_observed_report_slice_fields(args.scope_review)
    _write_json(args.output, selection)

    written: list[Path] = []
    for row in selection["mappings"]:
        path = args.mapping_output_dir / row["mapping_file"]
        _write_json(path, row["mapping"])
        written.append(path)

    summary = selection["summary"]
    boundary = selection["decision_boundary"]
    print("OBSERVED_REPORT_SLICE_FIELD_SELECTION")
    print(f"schema_version={selection['schema_version']}")
    print(f"selection_kind={selection['selection_kind']}")
    print(f"mapping_count={summary['mapping_count']}")
    print(f"selected_scope_count={summary['selected_scope_count']}")
    print(f"selected_field_contract_count={summary['selected_field_contract_count']}")
    print(f"deferred_scope_count={summary['deferred_scope_count']}")
    print(f"contains_source_scalar_values={str(summary['contains_source_scalar_values']).lower()}")
    print(f"candidate_mapping_files_ready={str(summary['candidate_mapping_files_ready']).lower()}")
    print(f"can_promote={str(boundary['can_promote']).lower()}")
    print(f"normalization_allowed={str(boundary['normalization_allowed']).lower()}")
    print()
    print("CANDIDATE_MAPPINGS")
    for row, path in zip(selection["mappings"], written, strict=True):
        mapping = row["mapping"]
        print(
            f"mapping_id={mapping['mapping_id']} | endpoint={mapping['route_template']} | "
            f"status={mapping['status']} | entities={len(mapping['entities'])} | "
            f"field_contracts={row['selected_field_contract_count']} | output={path.as_posix()}"
        )
    print()
    print("DEFERRED_SCOPES")
    for row in selection["deferred_scopes"]:
        print(
            f"endpoint_kind={row['endpoint_kind']} | scope={row['scope']} | "
            f"decision={row['decision']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
