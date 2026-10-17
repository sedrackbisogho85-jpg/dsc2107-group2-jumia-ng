
import csv
import time
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from scraper_config import HEADERS

# STEP 1: Configuration
START_URL = "https://books.toscrape.com/"
OUTPUT_FILE = "book_links.csv"

MAX_PAGES = 50
DELAY = 3

session = requests.Session()
session.headers.update(HEADERS)


# STEP 2: Request a page safely
def fetch_page(url):
    for attempt in range(1, 4):

        time.sleep(DELAY)

        try:
            response = session.get(url, timeout=20)

            # Stop if the website restricts access
            if response.status_code in (403, 429):
                raise RuntimeError(
                    f"Access restricted: HTTP {response.status_code}"
                )

            # Retry temporary server errors
            if response.status_code >= 500:
                if attempt == 3:
                    response.raise_for_status()

                print("Temporary server error. Retrying...")
                time.sleep(3 * attempt)
                continue

            response.raise_for_status()
            response.encoding = "utf-8"

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            return soup, response.url

        except (requests.Timeout, requests.ConnectionError):
            if attempt == 3:
                raise

            print("Connection issue. Retrying...")
            time.sleep(3 * attempt)


# STEP 3: Save progress
def save_links(records):
    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["page", "title", "detail_url"]
        )

        writer.writeheader()
        writer.writerows(records)


# STEP 4: Visit catalogue pages
url = START_URL
page_number = 0

book_links = []
seen_urls = set()

while url is not None and page_number < MAX_PAGES:

    soup, current_url = fetch_page(url)

    page_number += 1

    books = soup.select("article.product_pod")

    for book in books:

        link = book.select_one("h3 a[href]")

        if link is None:
            print("WARNING: Book link missing")
            continue

        detail_url = urljoin(
            current_url,
            link["href"]
        )

        # Prevent duplicate records
        if detail_url in seen_urls:
            continue

        seen_urls.add(detail_url)

        book_info = {
            "page": page_number,
            "title": link.get("title", ""),
            "detail_url": detail_url
        }

        book_links.append(book_info)

    # Save after every successful page
    save_links(book_links)

    print(
        f"Page {page_number}: "
        f"{len(book_links)} unique links collected"
    )

    # Find the Next button
    next_link = soup.select_one("li.next a[href]")

    if next_link:
        url = urljoin(current_url, next_link["href"])
    else:
        url = None


# STEP 5: Validate
print("\nCOLLECTION SUMMARY")
print("-------------------------")
print("Pages visited:", page_number)
print("Unique book URLs:", len(book_links))
print("Output file:", OUTPUT_FILE)

if page_number == 50 and len(book_links) == 1000:
    print("SUCCESS: URL index complete!")
else:
    print("WARNING: Check missing pages or book links.")

session.close()
