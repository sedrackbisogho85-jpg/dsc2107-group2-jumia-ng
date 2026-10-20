"""Validate raw Jumia CSV files without modifying them."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import CATEGORY_URLS, RAW_FIELDS
from .scraper import CATEGORY_SEPARATOR
from .utils import write_json


def validate_csv(path: Path, minimum_records: int) -> dict[str, Any]:
    with path.open("r", newline="", encoding="utf-8-sig") as file_handle:
        reader = csv.DictReader(file_handle)
        rows = list(reader)
        columns = reader.fieldnames or []

    missing_columns = [field for field in RAW_FIELDS if field not in columns]
    missing_values = {
        field: sum(not (row.get(field) or "").strip() for row in rows)
        for field in RAW_FIELDS
        if field in columns
    }
    id_counts = Counter(row.get("source_product_id", "") for row in rows)
    duplicate_count = sum(count - 1 for key, count in id_counts.items() if key and count > 1)

    category_counts = {category: 0 for category in CATEGORY_URLS}
    for row in rows:
        for category in row.get("category", "").split(CATEGORY_SEPARATOR):
            if category in category_counts:
                category_counts[category] += 1

    timestamp_errors: list[str] = []
    for row_number, row in enumerate(rows, start=2):
        try:
            parsed = datetime.fromisoformat(row.get("scraped_at", ""))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError("timestamp is not timezone-aware")
            if parsed.date().isoformat() != row.get("scrape_date"):
                raise ValueError("scrape_date differs from timestamp date")
        except ValueError as error:
            timestamp_errors.append(f"row {row_number}: {error}")

    passed = (
        not missing_columns
        and len(rows) >= minimum_records
        and duplicate_count == 0
        and all(category_counts.values())
        and not timestamp_errors
        and missing_values.get("source_product_id", 0) == 0
        and missing_values.get("product_name", 0) == 0
        and missing_values.get("product_url", 0) == 0
    )
    return {
        "passed": passed,
        "file": str(path),
        "record_count": len(rows),
        "minimum_required": minimum_records,
        "missing_columns": missing_columns,
        "missing_values": missing_values,
        "duplicate_count": duplicate_count,
        "category_counts": category_counts,
        "timestamp_error_count": len(timestamp_errors),
        "timestamp_errors": timestamp_errors[:20],
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--minimum-records", type=int, required=True)
    parser.add_argument("--save", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    report = validate_csv(args.csv_path, args.minimum_records)
    if args.save:
        write_json(args.save, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

