"""Shared configuration for the Jumia Nigeria project."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECON_DIR = PROJECT_ROOT / "reconnaissance"
EVIDENCE_DIR = RECON_DIR / "evidence"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
CHECKPOINT_DIR = PROJECT_ROOT / "data" / "checkpoints"
LOG_DIR = PROJECT_ROOT / "logs"
DATABASE_DIR = PROJECT_ROOT / "database"

BASE_URL = "https://www.jumia.com.ng"
ROBOTS_URL = f"{BASE_URL}/robots.txt"
TIMEZONE_NAME = "Africa/Nairobi"
SOURCE_SITE = "Jumia Nigeria"
CURRENCY = "NGN"

CATEGORY_URLS = {
    "Phones & Tablets": f"{BASE_URL}/phones-tablets/",
    "Computing": f"{BASE_URL}/computing/",
    "Electronics": f"{BASE_URL}/electronics/",
}

RAW_FIELDS = [
    "source_product_id",
    "product_name",
    "brand",
    "current_price_raw",
    "old_price_raw",
    "displayed_discount_raw",
    "rating_raw",
    "review_count_raw",
    "category",
    "product_url",
    "currency",
    "source_site",
    "scraped_at",
    "scrape_date",
]

DEFAULT_DELAY_SECONDS = 3.0
DEFAULT_REQUEST_LIMIT = 1000
DEFAULT_SAMPLE_TARGET = 100
DEFAULT_DAILY_TARGET = 600
MINIMUM_DAILY_TARGET = 500
MAX_RETRIES = 3


def ensure_project_directories() -> None:
    """Create generated-output directories if they are missing."""

    for directory in (
        EVIDENCE_DIR,
        RAW_DIR,
        CLEANED_DIR,
        CHECKPOINT_DIR,
        LOG_DIR,
        DATABASE_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)

