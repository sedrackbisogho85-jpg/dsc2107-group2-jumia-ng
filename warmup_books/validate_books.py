
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

# STEP 1: Locate our files
BASE_DIR = Path(__file__).resolve().parent

parser = argparse.ArgumentParser(
    description="Validate the private Books to Scrape CSV files offline."
)
parser.add_argument(
    "--data-dir",
    type=Path,
    default=BASE_DIR,
    help="Directory containing books_detailed.csv and book_links.csv.",
)
args = parser.parse_args()

DATA_DIR = args.data_dir.resolve()
DATA_FILE = DATA_DIR / "books_detailed.csv"
LINKS_FILE = DATA_DIR / "book_links.csv"
REPORT_FILE = BASE_DIR / "validation_report.txt"
EXPECTED_RECORDS = 1000

# STEP 2: Read CSV files
def read_csv(path, required_columns):
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    with path.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise SystemExit(f"No CSV header: {path}")

        missing = set(required_columns) - set(reader.fieldnames)

        if missing:
            raise SystemExit(
                f"Missing columns in {path.name}: {sorted(missing)}"
            )

        return list(reader)


required = [
    "page", "title", "price", "rating", "category",
    "upc", "availability", "reviews",
    "detail_url", "status"
]

books = read_csv(DATA_FILE, required)
links = read_csv(LINKS_FILE, ["detail_url"])

print("Starting data validation...\n")

# STEP 3: Check duplicate URLs
urls = [book["detail_url"].strip() for book in books]
url_counts = Counter(urls)

duplicate_urls = [
    url for url, count in url_counts.items()
    if count > 1
]

# STEP 4: Check duplicate UPCs
upcs = [
    book["upc"].strip()
    for book in books
    if book["upc"].strip()
]

upc_counts = Counter(upcs)

duplicate_upcs = [
    upc for upc, count in upc_counts.items()
    if count > 1
]

# STEP 5: Check missing information
missing_records = []

for number, book in enumerate(books, start=2):
    missing_fields = [
        field for field in required
        if not book[field].strip()
    ]

    if missing_fields:
        missing_records.append((number, missing_fields))

# STEP 6: Check prices
invalid_prices = []

for number, book in enumerate(books, start=2):
    price = book["price"].strip()

    if not re.fullmatch(r"£\d+\.\d{2}", price):
        invalid_prices.append((number, price))

# STEP 7: Check ratings
valid_ratings = {"One", "Two", "Three", "Four", "Five"}

invalid_ratings = [
    (number, book["rating"])
    for number, book in enumerate(books, start=2)
    if book["rating"].strip() not in valid_ratings
]

# STEP 8: Check review counts
invalid_reviews = [
    (number, book["reviews"])
    for number, book in enumerate(books, start=2)
    if not re.fullmatch(r"\d+", book["reviews"].strip())
]

# STEP 9: Check catalogue page values
invalid_pages = []

for number, book in enumerate(books, start=2):
    try:
        page = int(book["page"].strip())
    except ValueError:
        invalid_pages.append((number, book["page"]))
        continue

    if not 1 <= page <= 50:
        invalid_pages.append((number, book["page"]))

# STEP 10: Check status values
non_complete = [
    number
    for number, book in enumerate(books, start=2)
    if book["status"].strip() != "complete"
]

# STEP 11: Compare with original URL index
index_url_values = [
    link["detail_url"].strip() for link in links
]

index_url_counts = Counter(index_url_values)
duplicate_index_urls = [
    url for url, count in index_url_counts.items()
    if count > 1
]

index_urls = set(index_url_values)

collected_urls = set(urls)

unknown_urls = collected_urls - index_urls
remaining_urls = index_urls - collected_urls

# STEP 12: Check expected final counts
count_errors = []

if len(links) != EXPECTED_RECORDS:
    count_errors.append(
        f"URL index has {len(links)} rows; expected {EXPECTED_RECORDS}."
    )

if len(index_urls) != EXPECTED_RECORDS:
    count_errors.append(
        f"URL index has {len(index_urls)} unique URLs; "
        f"expected {EXPECTED_RECORDS}."
    )

if len(books) != EXPECTED_RECORDS:
    count_errors.append(
        f"Detailed dataset has {len(books)} rows; "
        f"expected {EXPECTED_RECORDS}."
    )

if len(collected_urls) != EXPECTED_RECORDS:
    count_errors.append(
        f"Detailed dataset has {len(collected_urls)} unique URLs; "
        f"expected {EXPECTED_RECORDS}."
    )

# STEP 13: Prepare results
results = [
    "BOOKS TO SCRAPE - VALIDATION REPORT",
    "===================================",
    f"Original URL records: {len(links)}",
    f"Unique URLs in index: {len(index_urls)}",
    f"Detailed records: {len(books)}",
    f"Unique detailed URLs: {len(collected_urls)}",
    f"Remaining book URLs: {len(remaining_urls)}",
    "",
    f"Duplicate URLs in index: {len(duplicate_index_urls)}",
    f"Duplicate detail URLs: {len(duplicate_urls)}",
    f"Duplicate UPCs: {len(duplicate_upcs)}",
    f"Records with missing fields: {len(missing_records)}",
    f"Invalid prices: {len(invalid_prices)}",
    f"Invalid ratings: {len(invalid_ratings)}",
    f"Invalid review counts: {len(invalid_reviews)}",
    f"Invalid catalogue page values: {len(invalid_pages)}",
    f"Records not marked complete: {len(non_complete)}",
    f"URLs not found in original index: {len(unknown_urls)}",
    f"Dataset count mismatches: {len(count_errors)}",
]

if count_errors:
    results.extend(["", "Count mismatch details:", *count_errors])

# STEP 14: Display and save the report
report = "\n".join(results)

print(report)

REPORT_FILE.write_text(report, encoding="utf-8")

print("\nReport saved:", REPORT_FILE.name)

# STEP 15: Overall quality check
problem_count = sum([
    len(duplicate_index_urls),
    len(duplicate_urls),
    len(duplicate_upcs),
    len(missing_records),
    len(invalid_prices),
    len(invalid_ratings),
    len(invalid_reviews),
    len(invalid_pages),
    len(non_complete),
    len(unknown_urls),
    len(remaining_urls),
    len(count_errors),
])

if problem_count == 0:
    print("\nPASS: No problems detected in the checks.")
else:
    print("\nWARNING: Data quality problems detected.")
    print("Review the validation report and source CSV.")
    print("First invalid prices:", invalid_prices[:5])
    print("First missing records:", missing_records[:5])
    raise SystemExit(1)
