"""Clean preserved Jumia raw CSV files into analysis-ready CSV files."""

from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .config import CLEANED_DIR, CURRENCY


CLEANED_FIELDS = [
    "source_product_id",
    "product_name",
    "brand",
    "current_price",
    "old_price",
    "displayed_discount_percentage",
    "calculated_discount_percentage",
    "rating",
    "review_count",
    "category",
    "product_url",
    "currency",
    "source_site",
    "scraped_at",
    "scrape_date",
    "discount_difference_flag",
    "validation_flags",
]
DISCOUNT_TOLERANCE = 2.0
IMPOSSIBLE_PRICE_LIMIT = 1_000_000_000.0


def numeric_match(value: str | None, pattern: str) -> str | None:
    if not value:
        return None
    match = re.search(pattern, value.replace(",", ""))
    return match.group(1) if match else None


def parse_price(value: str | None) -> float | None:
    matched = numeric_match(value, r"(-?\d+(?:\.\d+)?)")
    return float(matched) if matched is not None else None


def parse_percentage(value: str | None) -> float | None:
    matched = numeric_match(value, r"(-?\d+(?:\.\d+)?)\s*%")
    return float(matched) if matched is not None else None


def parse_rating(value: str | None) -> float | None:
    matched = numeric_match(value, r"(\d+(?:\.\d+)?)")
    return float(matched) if matched is not None else None


def parse_review_count(value: str | None) -> int | None:
    matched = numeric_match(value, r"(\d+)")
    return int(matched) if matched is not None else None


def csv_value(value: Any) -> Any:
    return "" if value is None else value


def clean_row(row: dict[str, str]) -> dict[str, Any]:
    current_price = parse_price(row.get("current_price_raw"))
    old_price = parse_price(row.get("old_price_raw"))
    displayed_discount = parse_percentage(row.get("displayed_discount_raw"))
    rating = parse_rating(row.get("rating_raw"))
    review_count = parse_review_count(row.get("review_count_raw"))

    calculated_discount: float | None = None
    if current_price is not None and old_price is not None and old_price > 0:
        calculated_discount = round(((old_price - current_price) / old_price) * 100, 2)

    flags: list[str] = []
    for label, price in (("current_price", current_price), ("old_price", old_price)):
        if price is not None and price < 0:
            flags.append(f"negative_{label}")
        if price is not None and price > IMPOSSIBLE_PRICE_LIMIT:
            flags.append(f"impossible_{label}")
    if rating is not None and not 0 <= rating <= 5:
        flags.append("rating_out_of_range")
    if review_count is not None and review_count < 0:
        flags.append("negative_review_count")

    discount_difference_flag = ""
    if displayed_discount is not None and calculated_discount is not None:
        if abs(displayed_discount - calculated_discount) > DISCOUNT_TOLERANCE:
            discount_difference_flag = "difference_over_2_percentage_points"

    scraped_at = row.get("scraped_at", "")
    if scraped_at:
        try:
            scraped_at = datetime.fromisoformat(scraped_at).isoformat()
        except ValueError:
            flags.append("invalid_scraped_at")

    cleaned = {
        "source_product_id": row.get("source_product_id", "").strip(),
        "product_name": row.get("product_name", "").strip(),
        "brand": row.get("brand", "").strip() or None,
        "current_price": current_price,
        "old_price": old_price,
        "displayed_discount_percentage": displayed_discount,
        "calculated_discount_percentage": calculated_discount,
        "rating": rating,
        "review_count": review_count,
        "category": row.get("category", "").strip(),
        "product_url": row.get("product_url", "").strip(),
        "currency": row.get("currency", "").strip() or CURRENCY,
        "source_site": row.get("source_site", "").strip(),
        "scraped_at": scraped_at,
        "scrape_date": row.get("scrape_date", "").strip(),
        "discount_difference_flag": discount_difference_flag,
        "validation_flags": " | ".join(flags),
    }
    return {key: csv_value(value) for key, value in cleaned.items()}


def clean_csv(raw_path: Path, output_path: Path | None = None) -> tuple[Path, int, int]:
    output_path = output_path or CLEANED_DIR / f"{raw_path.stem}_cleaned.csv"
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite cleaned file: {output_path}")

    with raw_path.open("r", newline="", encoding="utf-8-sig") as input_handle:
        rows = list(csv.DictReader(input_handle))

    seen: set[str] = set()
    duplicate_count = 0
    cleaned_rows: list[dict[str, Any]] = []
    for row in rows:
        product_id = row.get("source_product_id", "")
        if product_id in seen:
            duplicate_count += 1
            continue
        seen.add(product_id)
        cleaned_rows.append(clean_row(row))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", newline="", encoding="utf-8-sig") as output_handle:
        writer = csv.DictWriter(output_handle, fieldnames=CLEANED_FIELDS)
        writer.writeheader()
        writer.writerows(cleaned_rows)
    return output_path, len(cleaned_rows), duplicate_count


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_csv", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    output_path, row_count, duplicates = clean_csv(args.raw_csv, args.output)
    print(f"Cleaned file: {output_path}")
    print(f"Rows: {row_count}")
    print(f"Duplicate raw rows removed: {duplicates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

