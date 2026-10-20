"""Build the normalized SQLite database from one or more cleaned CSV files."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from pathlib import Path

from .scraper import CATEGORY_SEPARATOR


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    source_product_id TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    brand TEXT,
    product_url TEXT NOT NULL,
    source_site TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS product_categories (
    product_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (product_id, category_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE IF NOT EXISTS observations (
    observation_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    scraped_at TEXT NOT NULL,
    scrape_date TEXT NOT NULL,
    current_price REAL,
    old_price REAL,
    displayed_discount_percentage REAL,
    calculated_discount_percentage REAL,
    rating REAL,
    review_count INTEGER,
    currency TEXT NOT NULL,
    UNIQUE (product_id, scraped_at),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
"""


def nullable_number(value: str, converter):
    return None if value == "" else converter(value)


def build_database(
    cleaned_csvs: Path | Iterable[Path],
    database_path: Path,
    replace: bool = False,
) -> dict[str, int]:
    if isinstance(cleaned_csvs, Path):
        input_paths = [cleaned_csvs]
    else:
        input_paths = list(cleaned_csvs)
    if not input_paths:
        raise ValueError("At least one cleaned CSV file is required.")

    if database_path.exists():
        if not replace:
            raise FileExistsError(
                f"Database exists: {database_path}. Use --replace to rebuild it."
            )
        database_path.unlink()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    counts = {"products": 0, "categories": 0, "product_categories": 0, "observations": 0}
    rows: list[dict[str, str]] = []
    for cleaned_csv in input_paths:
        with cleaned_csv.open("r", newline="", encoding="utf-8-sig") as file_handle:
            rows.extend(csv.DictReader(file_handle))

    seen_observations: set[tuple[str, str]] = set()
    for row in rows:
        observation_key = (row["source_product_id"], row["scrape_date"])
        if observation_key in seen_observations:
            raise ValueError(
                "Duplicate product/date observation: "
                f"{row['source_product_id']} on {row['scrape_date']}"
            )
        seen_observations.add(observation_key)

    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            connection.executescript(SCHEMA)
            for row in rows:
                cursor = connection.execute(
                    """
                    INSERT INTO products
                        (source_product_id, product_name, brand, product_url, source_site)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(source_product_id) DO UPDATE SET
                        product_name=excluded.product_name,
                        brand=excluded.brand,
                        product_url=excluded.product_url,
                        source_site=excluded.source_site
                    RETURNING product_id
                    """,
                    (
                        row["source_product_id"],
                        row["product_name"],
                        row["brand"] or None,
                        row["product_url"],
                        row["source_site"],
                    ),
                )
                product_id = cursor.fetchone()[0]

                for category in row["category"].split(CATEGORY_SEPARATOR):
                    connection.execute(
                        "INSERT OR IGNORE INTO categories(category_name) VALUES (?)",
                        (category,),
                    )
                    category_id = connection.execute(
                        "SELECT category_id FROM categories WHERE category_name = ?",
                        (category,),
                    ).fetchone()[0]
                    connection.execute(
                        "INSERT OR IGNORE INTO product_categories(product_id, category_id) VALUES (?, ?)",
                        (product_id, category_id),
                    )

                connection.execute(
                    """
                    INSERT INTO observations (
                        product_id, scraped_at, scrape_date, current_price, old_price,
                        displayed_discount_percentage, calculated_discount_percentage,
                        rating, review_count, currency
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        row["scraped_at"],
                        row["scrape_date"],
                        nullable_number(row["current_price"], float),
                        nullable_number(row["old_price"], float),
                        nullable_number(row["displayed_discount_percentage"], float),
                        nullable_number(row["calculated_discount_percentage"], float),
                        nullable_number(row["rating"], float),
                        nullable_number(row["review_count"], int),
                        row["currency"],
                    ),
                )

        for table in counts:
            counts[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return counts


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cleaned_csv", type=Path, nargs="+")
    parser.add_argument("database_path", type=Path)
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    counts = build_database(args.cleaned_csv, args.database_path, args.replace)
    for table, count in counts.items():
        print(f"{table}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

