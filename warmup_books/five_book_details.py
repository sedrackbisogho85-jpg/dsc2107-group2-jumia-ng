
import requests
import csv
import time

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from scraper_config import HEADERS

# STEP 1: Website and request settings
url = "https://books.toscrape.com/"

# STEP 2: Request the catalogue page
response = requests.get(
    url,
    headers=HEADERS,
    timeout=20
)

response.raise_for_status()
response.encoding = "utf-8"

soup = BeautifulSoup(response.text, "html.parser")

# STEP 3: Find all books on page 1
books = soup.select("article.product_pod")

# STEP 4: Prepare an empty list
book_data = []

# STEP 5: Process only the first 5 books
for number, book in enumerate(books[:5], start=1):

    # Get the link to the individual book
    link = book.select_one("h3 a")

    detail_url = urljoin(
        response.url,
        link["href"]
    )

    # Wait before requesting the next page
    time.sleep(3)

    # Open the individual book page
    detail_response = requests.get(
        detail_url,
        headers=HEADERS,
        timeout=20
    )

    detail_response.raise_for_status()
    detail_response.encoding = "utf-8"

    detail_soup = BeautifulSoup(
        detail_response.text,
        "html.parser"
    )

    # Extract title, price and rating
    product = detail_soup.select_one("div.product_main")

    title = product.select_one("h1").get_text(strip=True)

    price = product.select_one(
        "p.price_color"
    ).get_text(strip=True)

    rating = product.select_one(
        "p.star-rating"
    )["class"][1]

    # Extract category
    breadcrumbs = detail_soup.select(
        "ul.breadcrumb li a"
    )

    category = breadcrumbs[-1].get_text(strip=True)

    # Extract product information table
    details = {}

    rows = detail_soup.select("table.table-striped tr")

    for row in rows:
        heading = row.select_one("th")
        value = row.select_one("td")

        if heading and value:
            key = heading.get_text(strip=True)
            data = value.get_text(" ", strip=True)

            details[key] = data

    # Combine all information in one dictionary
    book_info = {
        "title": title,
        "price": price,
        "rating": rating,
        "category": category,
        "upc": details.get("UPC", "Unknown"),
        "availability": details.get(
            "Availability", "Unknown"
        ),
        "reviews": details.get(
            "Number of reviews", "Unknown"
        ),
        "url": detail_url
    }

    # Add the book to our dataset
    book_data.append(book_info)

    print(f"Book {number}: {title} - Collected!")

# STEP 6: Save results to CSV
with open(
    "five_book_details.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "title",
            "price",
            "rating",
            "category",
            "upc",
            "availability",
            "reviews",
            "url"
        ]
    )

    writer.writeheader()
    writer.writerows(book_data)

print("--------------------------")
print("TOTAL BOOKS:", len(book_data))
print("Detailed CSV saved successfully!")
