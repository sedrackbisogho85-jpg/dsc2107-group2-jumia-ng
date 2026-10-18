
import unittest

from src.cleaner import clean_row, parse_percentage, parse_price, parse_rating, parse_review_count


class CleanerTests(unittest.TestCase):
    def test_numeric_parsers_preserve_missing_values(self):
        self.assertEqual(parse_price("₦ 1,250,500"), 1_250_500.0)
        self.assertEqual(parse_percentage("20%"), 20.0)
        self.assertEqual(parse_rating("4.5 out of 5"), 4.5)
        self.assertEqual(parse_review_count("(1,234)"), 1234)
        self.assertIsNone(parse_price(None))
        self.assertIsNone(parse_rating(None))

    def test_discount_calculation_and_tolerance_flag(self):
        row = {
            "source_product_id": "A1",
            "product_name": "Example",
            "brand": "Brand",
            "current_price_raw": "₦ 70",
            "old_price_raw": "₦ 100",
            "displayed_discount_raw": "20%",
            "rating_raw": "4 out of 5",
            "review_count_raw": "(10)",
            "category": "Electronics",
            "product_url": "https://www.jumia.com.ng/example.html",
            "currency": "NGN",
            "source_site": "Jumia Nigeria",
            "scraped_at": "2026-10-13T18:00:00+03:00",
            "scrape_date": "2026-10-13",
        }
        cleaned = clean_row(row)
        self.assertEqual(cleaned["calculated_discount_percentage"], 30.0)
        self.assertEqual(
            cleaned["discount_difference_flag"],
            "difference_over_2_percentage_points",
        )
# darren 

if __name__ == "__main__":
    unittest.main()

