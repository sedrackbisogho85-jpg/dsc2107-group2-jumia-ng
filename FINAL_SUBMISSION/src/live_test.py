"""Two-request live check: robots.txt followed by one category page."""

from __future__ import annotations

import argparse
import json
import os
from urllib.robotparser import RobotFileParser

from .config import CATEGORY_URLS, DEFAULT_DELAY_SECONDS, ROBOTS_URL
from .scraper import PoliteFetcher, make_logger, parse_product_cards
from .utils import BOT_TOKEN, nairobi_now


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    runtime_email = os.environ.get("JUMIA_CONTACT_EMAIL")
    parser.add_argument(
        "--contact-email",
        default=runtime_email,
        required=runtime_email is None,
        help="Contact email, or set JUMIA_CONTACT_EMAIL.",
    )
    parser.add_argument("--category", choices=CATEGORY_URLS, default="Phones & Tablets")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS)
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    run_id = nairobi_now().strftime("%Y-%m-%dT%H%M%S%z")
    logger, log_path = make_logger(run_id, "live_test")
    fetcher = PoliteFetcher(args.contact_email, args.delay, 5, logger)

    robots_response, _ = fetcher.get(ROBOTS_URL)
    robots = RobotFileParser()
    robots.parse(robots_response.text.splitlines())
    category_url = CATEGORY_URLS[args.category]
    if not robots.can_fetch(BOT_TOKEN, category_url):
        print(json.dumps({"passed": False, "reason": "robots.txt denial"}, indent=2))
        return 2

    response, scraped_at = fetcher.get(category_url)
    products, errors = parse_product_cards(response.content, args.category, scraped_at)
    result = {
        "passed": response.status_code == 200 and bool(products) and not errors,
        "category": args.category,
        "status_code": response.status_code,
        "product_cards": len(products),
        "parsing_errors": errors,
        "request_count": fetcher.request_count,
        "delay_seconds": args.delay,
        "pagination_expected": "?page=2",
        "log": str(log_path),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

