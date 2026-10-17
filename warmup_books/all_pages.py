
import csv
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from scraper_config import HEADERS

# STEP 1: Starting page
url = "https://books.toscrape.com/"

# STEP 2: Prepare our storage
book_data = []

page_number = 0

# STEP 3: Visit a maximum of 2 pages
while url is not None and page_number < 50:

    # Wait between website requests
    if page_number > 0:
        time.sleep(3)

    print("Visiting:", url)

    # Download the webpage
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )
    response.raise_for_status()

    # Read the HTML
    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    page_number += 1

    # Find all books on the current page
    books = soup.select("article.product_pod")

    print("Page:", page_number)
    print("Books found:", len(books))

    # STEP 4: Extract every book
    for book in books:

        title = book.select_one("h3 a")["title"]

        price = book.select_one(
            "p.price_color"
        ).get_text(strip=True)

        rating = book.select_one(
            "p.star-rating"
        )["class"][1]

        book_info = {
            "page": page_number,
            "title": title,
            "price": price,
            "rating": rating
        }

        book_data.append(book_info)

    # STEP 5: Find the Next button
    next_link = soup.select_one("li.next a")

    if next_link is not None:
        url = urljoin(
            response.url,
            next_link["href"]
        )
    else:
        url = None

# STEP 6: Save collected data
with open(
    "books_all_pages.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "page",
            "title",
            "price",
            "rating"
        ]
    )

    writer.writeheader()
    writer.writerows(book_data)

print("-------------------------")
print("TOTAL PAGES:", page_number)
print("TOTAL BOOKS:", len(book_data))
print("CSV saved successfully!")



# STEP 7: Validate the full pagination results

expected_pages = 50
expected_books = 1000

if page_number == expected_pages and len(book_data) == expected_books:
    print("SUCCESS: All 50 pages and 1000 books collected!")
else:
    print("WARNING: The collection is incomplete or unexpected.")
    print("Expected pages:", expected_pages)
    print("Actual pages:", page_number)
    print("Expected books:", expected_books)
    print("Actual books:", len(book_data))
