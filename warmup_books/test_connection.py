
import requests

from scraper_config import HEADERS

# The website we want to access
url = "https://books.toscrape.com/"

# Send a request to the website
try:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    print("Status code:", response.status_code)

    response.raise_for_status()

    print("Connection successful!")
    print("Website URL:", response.url)
    print("HTML characters received:", len(response.text))

except requests.RequestException as error:
    print("Connection failed:", error)
