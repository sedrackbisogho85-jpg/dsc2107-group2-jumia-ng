import csv
import requests
from bs4 import BeautifulSoup

from scraper_config import HEADERS

# STEP 1: Define the website
url = "https://books.toscrape.com/"

# STEP 3: Download the webpage
response = requests.get(url, headers=HEADERS, timeout=20)
response.raise_for_status()

# STEP 4: Parse the HTML
soup = BeautifulSoup(response.text, "html.parser")

# STEP 5: Find ALL books on the page
books = soup.select("article.product_pod")

# STEP 6: Create an empty list for our results
book_data = []

# STEP 7: Loop through each book
for number, book in enumerate(books, start=1):

    title = book.select_one("h3 a")["title"]

    price = book.select_one("p.price_color").get_text(strip=True)

    rating = book.select_one("p.star-rating")["class"][1]

    # Store the information in a dictionary
    book_info = {
        "title": title,
        "price": price,
        "rating": rating
    }

    # Add the dictionary to our list
    book_data.append(book_info)

    # Display the extracted information
    print(f"Book {number}")
    print("Title:", title)
    print("Price:", price)
    print("Rating:", rating)
    print("----------------------------")

# STEP 8: Count our collected records
print("TOTAL BOOKS COLLECTED:", len(book_data))

if len(book_data) != 20:
    print("WARNING: Expected 20 books on page 1.")

# STEP 9: Save the collected books to a CSV file

with open("books_page1.csv", "w", newline="", encoding="utf-8-sig") as file:

    writer = csv.DictWriter(
        file,
        fieldnames=["title", "price", "rating"]
    )

    writer.writeheader()

    writer.writerows(book_data)

print("CSV file saved successfully!")
print("Total records saved:", len(book_data))
