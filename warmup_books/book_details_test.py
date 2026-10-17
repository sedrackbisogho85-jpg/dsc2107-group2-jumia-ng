
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from scraper_config import HEADERS

# STEP 1: Define the starting website
url = "https://books.toscrape.com/"

# STEP 2: Download the catalogue page
response = requests.get(url, headers=HEADERS, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# STEP 3: Find the first book's link
book_link = soup.select_one("article.product_pod h3 a")

if book_link is None or not book_link.get("href"):
    raise RuntimeError("Could not find the first book link.")

# STEP 4: Build the complete detail page URL
detail_url = urljoin(response.url, book_link["href"])

print("Book detail URL:", detail_url)

# STEP 5: Wait before making another request
time.sleep(3)

# STEP 6: Visit the individual book page
detail_response = requests.get(
    detail_url,
    headers=HEADERS,
    timeout=20
)


detail_response.raise_for_status()

# Decode the website text using UTF-8
detail_response.encoding = "utf-8"

detail_soup = BeautifulSoup(
    detail_response.text,
    "html.parser"
)

# STEP 7: Extract main book information
product = detail_soup.select_one("div.product_main")

if product is None:
    raise RuntimeError("Product information was not found.")

title = product.select_one("h1").get_text(strip=True)

price = product.select_one(
    "p.price_color"
).get_text(strip=True)

rating_tag = product.select_one("p.star-rating")

rating = "Unknown"
if rating_tag:
    for class_name in rating_tag.get("class", []):
        if class_name != "star-rating":
            rating = class_name

# STEP 8: Extract the book category
breadcrumbs = detail_soup.select("ul.breadcrumb li a")

category = (
    breadcrumbs[-1].get_text(strip=True)
    if breadcrumbs else "Unknown"
)

# STEP 9: Read the product information table
details = {}

rows = detail_soup.select("table.table-striped tr")

for row in rows:
    heading = row.select_one("th")
    value = row.select_one("td")

    if heading and value:
        key = heading.get_text(strip=True)
        data = value.get_text(" ", strip=True)

        details[key] = data

# STEP 10: Display our results
print("\nBOOK DETAILS")
print("---------------------------")
print("Title:", title)
print("Price:", price)
print("Rating:", rating)
print("Category:", category)
print("UPC:", details.get("UPC", "Unknown"))
print("Availability:", details.get("Availability", "Unknown"))
print("Reviews:", details.get("Number of reviews", "Unknown"))
print("---------------------------")
