from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector import review_report_pagination_semantics


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review a private bounded report-pagination batch through exact cross-page "
            "relationships and write a scalar-free semantic receipt."
        )
    )
    parser.add_argument(
        "--evidence",
        type=Path,
        default=Path("data/exchange/out/argentum-report-pagination-evidence.json"),
    )
    parser.add_argument(
        "--private-evidence",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/"
            "argentum-report-pagination-evidence.private.json"
        ),
    )
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-report-pagination-semantic-review.json"),
    )
    args = parser.parse_args()

    review = review_report_pagination_semantics(
        args.evidence,
        args.private_evidence,
        expected_guild_label=args.guild_label,
    )
    rendered = json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(args.output)

    summary = review["summary"]
    print(
        "pagination semantic review: "
        f"fields={summary['pagination_direct_field_count']} "
        f"verified={summary['relationship_verified_field_count']} "
        f"termination={summary['termination_condition_verified']}"
    )
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
