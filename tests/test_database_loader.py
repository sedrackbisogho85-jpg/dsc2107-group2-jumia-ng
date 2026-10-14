import csv
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from src.cleaner import CLEANED_FIELDS
from src.database_loader import build_database


def cleaned_row(scrape_date: str, current_price: float = 100.0) -> dict[str, object]:
    return {
        "source_product_id": "P1",
        "product_name": "Example product",
        "brand": "Example",
        "current_price": current_price,
        "old_price": 120.0,
        "displayed_discount_percentage": 17.0,
        "calculated_discount_percentage": 16.67,
        "rating": 4.0,
        "review_count": 10,
        "category": "Electronics",
        "product_url": "https://www.jumia.com.ng/example.html",
        "currency": "NGN",
        "source_site": "Jumia Nigeria",
        "scraped_at": f"{scrape_date}T12:00:00+03:00",
        "scrape_date": scrape_date,
        "discount_difference_flag": "",
        "validation_flags": "",
    }


def write_cleaned_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CLEANED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


class DatabaseLoaderTests(unittest.TestCase):
    def test_two_days_share_one_product_and_keep_two_observations(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            day_one = folder / "day_one.csv"
            day_two = folder / "day_two.csv"
            database = folder / "jumia.sqlite"
            write_cleaned_csv(day_one, [cleaned_row("2026-10-13")])
            write_cleaned_csv(day_two, [cleaned_row("2026-10-14", 90.0)])

            counts = build_database([day_one, day_two], database)

            self.assertEqual(counts["products"], 1)
            self.assertEqual(counts["observations"], 2)
            with closing(sqlite3.connect(database)) as connection:
                dates = connection.execute(
                    "SELECT scrape_date FROM observations ORDER BY scrape_date"
                ).fetchall()
            self.assertEqual(dates, [("2026-10-13",), ("2026-10-14",)])

    def test_duplicate_product_date_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            first = folder / "first.csv"
            duplicate = folder / "duplicate.csv"
            database = folder / "jumia.sqlite"
            write_cleaned_csv(first, [cleaned_row("2026-10-14")])
            write_cleaned_csv(duplicate, [cleaned_row("2026-10-14", 95.0)])

            with self.assertRaisesRegex(ValueError, "Duplicate product/date observation"):
                build_database([first, duplicate], database)


if __name__ == "__main__":
    unittest.main()
