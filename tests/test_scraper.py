from pathlib import Path
import json
import tempfile
import unittest

from src.scraper import load_checkpoint, normalize_product_url, page_url, parse_product_cards


FIXTURE = Path(__file__).parent / "fixtures" / "listing_page.html"


class ScraperParserTests(unittest.TestCase):
    def test_parses_required_fields_and_preserves_missing_values(self):
        products, errors = parse_product_cards(
            FIXTURE.read_bytes(),
            "Phones & Tablets",
            "2026-10-13T18:00:00+03:00",
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0]["source_product_id"], "TE123AA")
        self.assertEqual(products[0]["brand"], "Tecno")
        self.assertEqual(products[0]["current_price_raw"], "₦ 120,000")
        self.assertEqual(products[0]["review_count_raw"], "(25)")
        self.assertIsNone(products[1]["old_price_raw"])
        self.assertIsNone(products[1]["displayed_discount_raw"])
        self.assertIsNone(products[1]["rating_raw"])
        self.assertIsNone(products[1]["review_count_raw"])

    def test_url_normalization_removes_query_and_fragment(self):
        value = normalize_product_url("/product-1.html?utm_source=test#details")
        self.assertEqual(value, "https://www.jumia.com.ng/product-1.html")

    def test_page_url(self):
        base = "https://www.jumia.com.ng/computing/"
        self.assertEqual(page_url(base, 1), base)
        self.assertEqual(page_url(base, 2), f"{base}?page=2")

    def test_checkpoint_can_be_loaded_without_changing_it(self):
        payload = {
            "products": [{"source_product_id": "A1", "product_name": "Example"}],
            "completed_pages": [{"category": "Computing", "page": 1}],
            "stats": {"request_count": 2},
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "checkpoint.json"
            original = json.dumps(payload)
            path.write_text(original, encoding="utf-8")
            products, pages, stats = load_checkpoint(path)

            self.assertEqual(products["A1"]["product_name"], "Example")
            self.assertEqual(pages[0]["page"], 1)
            self.assertEqual(stats["request_count"], 2)
            self.assertEqual(path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()

