from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.baseline import freeze_workbook_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze a workbook v9 baseline without resaving the source file.")
    parser.add_argument("workbook", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--source", action="append", type=Path, default=[])
    args = parser.parse_args()
    results = freeze_workbook_baseline(args.workbook, args.output_dir, additional_sources=args.source)
    for name, path in results.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
