"""Shared, privacy-safe HTTP configuration for the warm-up scrapers."""

import os


CONTACT_EMAIL_ENV = "BOOKS_TO_SCRAPE_CONTACT_EMAIL"
PROJECT_USER_AGENT = "DSC2107-Group2-Warmup"


def build_headers():
    """Build request headers without storing a personal email in source control."""
    contact_email = os.getenv(CONTACT_EMAIL_ENV, "").strip()
    user_agent = PROJECT_USER_AGENT

    if contact_email:
        user_agent = f"{user_agent} ({contact_email})"

    return {"User-Agent": user_agent}


HEADERS = build_headers()
