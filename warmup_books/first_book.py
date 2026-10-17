
import requests
from bs4 import BeautifulSoup

from scraper_config import HEADERS

# Step 1: Define the website
url = "https://books.toscrape.com/"

# Step 3: Download the webpage
response = requests.get(url, headers=HEADERS, timeout=20)
response.raise_for_status()

# Step 4: Parse the HTML
soup = BeautifulSoup(response.text, "html.parser")

# Step 5: Find the first book
book = soup.select_one("article.product_pod")

if book is None:
    raise RuntimeError("No book found on this page.")

# Step 6: Extract the book's information
title = book.select_one("h3 a")["title"]

price = book.select_one("p.price_color").get_text(strip=True)

rating = book.select_one("p.star-rating")["class"][1]

# Step 7: Display our results
print("BOOK INFORMATION")
print("Title:", title)
print("Price:", price)
print("Rating:", rating)
