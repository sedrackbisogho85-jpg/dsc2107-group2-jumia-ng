
import csv
import json
import os
import time

from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from scraper_config import HEADERS


# =====================================================
# STEP 1: CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "book_links.csv"
OUTPUT_FILE = BASE_DIR / "books_detailed.csv"
DAILY_LOG = BASE_DIR / "daily_request_usage.json"

BATCH_SIZE = 100
MAX_REQUESTS = 110
DELAY_SECONDS = 3

# Conservative daily request limit
DAILY_REQUEST_LIMIT = 900

FIELDS = [
    "page",
    "title",
    "price",
    "rating",
    "category",
    "upc",
    "availability",
    "reviews",
    "detail_url",
    "status"
]

# =====================================================
# STEP 2: CUSTOM STOP EXCEPTION
# =====================================================

class StopRun(Exception):
    """Stop scraping safely when a limit is reached."""
    pass


# =====================================================
# STEP 3: PERSISTENT DAILY REQUEST TRACKING
# =====================================================

def reserve_daily_request():

    today = date.today().isoformat()

    # Check whether the daily log already exists
    if DAILY_LOG.exists():

        try:
            usage = json.loads(
                DAILY_LOG.read_text(encoding="utf-8")
            )

            # Validate the existing request log
            if (
                not isinstance(usage, dict)
                or not isinstance(usage.get("date"), str)
                or type(usage.get("used")) is not int
                or usage["used"] < 0
            ):
                raise ValueError("Invalid request log")

        except (OSError, ValueError) as error:
            raise StopRun(
                f"Cannot safely read request log: {error}"
            )

    else:
        usage = None

    # Start a new record if the date has changed
    if usage is None or usage["date"] != today:

        answer = input(
            "HTTP requests already made today "
            "across all scraping scripts: "
        )

        try:
            previous_requests = int(answer)

            if previous_requests < 0:
                raise ValueError("Negative request count")

        except ValueError:
            raise StopRun(
                "Enter a valid non-negative request count."
            )

        usage = {
            "date": today,
            "used": previous_requests
        }

    # Stop if daily request limit has been reached
    if usage["used"] >= DAILY_REQUEST_LIMIT:
        raise StopRun(
            "Daily request limit reached. "
            "Resume on another day."
        )

    # Count the next request before sending it
    usage["used"] += 1

    # Save the updated request count
    temporary = DAILY_LOG.with_suffix(".json.tmp")

    temporary.write_text(
        json.dumps(usage, indent=2),
        encoding="utf-8"
    )

    os.replace(temporary, DAILY_LOG)

    return usage["used"]


# =====================================================
# STEP 4: FETCH WEBPAGE WITH RETRIES
# =====================================================

def fetch_page(session, url, counter):

    for attempt in range(1, 4):

        # Check current execution's request budget
        if counter["used"] >= MAX_REQUESTS:
            raise StopRun(
                "Request budget for this run reached."
            )

        # Respect the website request delay
        time.sleep(DELAY_SECONDS)

        # Record request in persistent daily tracker
        reserve_daily_request()

        # Count this execution's request
        counter["used"] += 1

        try:
            response = session.get(
                url,
                timeout=20
            )

        except (
            requests.Timeout,
            requests.ConnectionError
        ) as error:

            if attempt == 3:
                raise

            print(
                f"Connection problem: {error}"
            )

            print("Retrying after back-off...")

            time.sleep(3 * attempt)

            continue

        # Stop if the website restricts access
        if response.status_code in (403, 429):

            raise StopRun(
                "Website restricted access: "
                f"HTTP {response.status_code}"
            )

        # Retry temporary server errors
        if 500 <= response.status_code <= 599:

            if attempt == 3:
                response.raise_for_status()

            print(
                "Temporary server error. Retrying..."
            )

            time.sleep(3 * attempt)

            continue

        # Raise errors for other bad responses
        response.raise_for_status()

        # Fix character encoding
        response.encoding = "utf-8"

        # Convert HTML into BeautifulSoup
        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        return soup

    raise RuntimeError(
        "Page could not be fetched."
    )


# =====================================================
# STEP 5: EXTRACT INFORMATION FROM ONE BOOK
# =====================================================

def extract_book(soup, source):

    # Find the main product section
    product = soup.select_one("div.product_main")

    if product is None:
        raise ValueError(
            "Product information section missing."
        )

    # Extract title, price and rating
    title_tag = product.select_one("h1")

    price_tag = product.select_one(
        "p.price_color"
    )

    rating_tag = product.select_one(
        "p.star-rating"
    )

    title = (
        title_tag.get_text(strip=True)
        if title_tag else ""
    )

    price = (
        price_tag.get_text(strip=True)
        if price_tag else ""
    )

    # Extract star rating
    rating = ""

    if rating_tag:

        for name in rating_tag.get("class", []):

            if name in (
                "One",
                "Two",
                "Three",
                "Four",
                "Five"
            ):
                rating = name

    # Extract category from breadcrumbs
    breadcrumbs = soup.select(
        "ul.breadcrumb li a"
    )

    category = (
        breadcrumbs[-1].get_text(strip=True)
        if breadcrumbs else ""
    )

    # Extract the product information table
    details = {}

    rows = soup.select(
        "table.table-striped tr"
    )

    for row in rows:

        heading = row.select_one("th")
        value = row.select_one("td")

        if heading and value:

            key = heading.get_text(strip=True)

            data = value.get_text(
                " ",
                strip=True
            )

            details[key] = data

    # Combine extracted information
    record = {
        "page": source["page"],
        "title": title,
        "price": price,
        "rating": rating,
        "category": category,
        "upc": details.get("UPC", ""),
        "availability": details.get(
            "Availability", ""
        ),
        "reviews": details.get(
            "Number of reviews", ""
        ),
        "detail_url": source["detail_url"]
    }

    # Check that important fields exist
    essential_fields = [
        "title",
        "price",
        "rating",
        "category",
        "upc",
        "availability",
        "reviews"
    ]

    record["status"] = (
        "complete"
        if all(
            record[field] != ""
            for field in essential_fields
        )
        else "partial"
    )

    return record


# =====================================================
# STEP 6: SAVE PROGRESS SAFELY
# =====================================================

def save_progress(records):

    temporary_file = OUTPUT_FILE.with_suffix(
        ".csv.tmp"
    )

    with temporary_file.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS
        )

        writer.writeheader()

        writer.writerows(records)

    # Replace old CSV only after successful writing
    os.replace(
        temporary_file,
        OUTPUT_FILE
    )


# =====================================================
# STEP 7: LOAD THE 1000 BOOK URLS
# =====================================================

if not INPUT_FILE.exists():

    raise SystemExit(
        "ERROR: book_links.csv was not found."
    )

with INPUT_FILE.open(
    "r",
    newline="",
    encoding="utf-8-sig"
) as file:

    reader = csv.DictReader(file)

    if (
        not reader.fieldnames
        or "detail_url" not in reader.fieldnames
        or "page" not in reader.fieldnames
    ):
        raise SystemExit(
            "ERROR: Required URL columns are missing."
        )

    links = list(reader)


# =====================================================
# STEP 8: RECOVER PREVIOUSLY SAVED RECORDS
# =====================================================

saved_records = []

if OUTPUT_FILE.exists():

    with OUTPUT_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames != FIELDS:
            raise SystemExit(
                "ERROR: Existing CSV columns differ."
            )

        saved_records = list(reader)

# Identify URLs already processed
completed_urls = {
    record["detail_url"]
    for record in saved_records
}

print("Previously saved:", len(saved_records))
print("Available URLs:", len(links))


# =====================================================
# STEP 9: SCRAPE THE NEXT BATCH
# =====================================================

session = requests.Session()

session.headers.update(HEADERS)

counter = {
    "used": 0
}

new_records = 0

try:

    for source in links:

        # Stop once the batch target is reached
        if new_records >= BATCH_SIZE:
            break

        detail_url = source["detail_url"].strip()

        # Skip books already collected
        if detail_url in completed_urls:
            continue

        # Check that URL belongs to practice website
        parsed = urlparse(detail_url)

        if (
            parsed.scheme != "https"
            or parsed.hostname != "books.toscrape.com"
        ):
            print(
                "Skipping unexpected URL:",
                detail_url
            )
            continue

        try:

            # Download book detail page
            soup = fetch_page(
                session,
                detail_url,
                counter
            )

            # Extract information
            record = extract_book(
                soup,
                source
            )

        except StopRun as error:

            print(
                "Collection stopped:",
                error
            )

            break

        except (
            requests.RequestException,
            ValueError
        ) as error:

            print(
                "Failed:",
                detail_url,
                error
            )

            continue

        # Save the completed record
        saved_records.append(record)

        completed_urls.add(detail_url)

        # Save progress after each book
        save_progress(saved_records)

        new_records += 1

        print(
            f"Saved book {new_records}: "
            f"{record['title']} "
            f"({record['status']})"
        )

finally:

    session.close()


# =====================================================
# STEP 10: COLLECTION SUMMARY
# =====================================================

print("\nCOLLECTION SUMMARY")
print("-----------------------------")

print(
    "New records this run:",
    new_records
)

print(
    "Total saved records:",
    len(saved_records)
)

print(
    "HTTP requests this run:",
    counter["used"]
)

print(
    "Remaining URLs:",
    len(links) - len(completed_urls)
)

print(
    "Output:",
    OUTPUT_FILE.name
)

partial_count = sum(
    record["status"] == "partial"
    for record in saved_records
)

print(
    "Records needing review:",
    partial_count
)


# =====================================================
# STEP 11: SHOW DAILY REQUEST USAGE
# =====================================================

if DAILY_LOG.exists():

    try:
        usage = json.loads(
            DAILY_LOG.read_text(
                encoding="utf-8"
            )
        )

        if usage.get("date") == date.today().isoformat():

            print(
                "Daily requests counted:",
                usage["used"],
                "/",
                DAILY_REQUEST_LIMIT
            )

    except (OSError, ValueError, AttributeError, KeyError) as error:

        print(
            "WARNING: Could not display daily usage:",
            error
        )


# =====================================================
# STEP 12: FINAL STATUS
# =====================================================

if len(completed_urls) == len(links):

    print(
        "\nSUCCESS: All book URLs have saved records!"
    )

else:

    print(
        "\nScraper checkpoint saved."
    )

    print(
        "Run again when your request budget allows."
    )
