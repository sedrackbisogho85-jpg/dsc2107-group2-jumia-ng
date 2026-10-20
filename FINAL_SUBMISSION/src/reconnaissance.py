"""Polite first-page reconnaissance for the public Jumia Nigeria website."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    CATEGORY_URLS,
    DEFAULT_DELAY_SECONDS,
    EVIDENCE_DIR,
    ROBOTS_URL,
    ensure_project_directories,
)
from .utils import build_user_agent, nairobi_now, safe_filename, write_json


@dataclass
class PageEvidence:
    label: str
    requested_url: str
    final_url: str
    status_code: int
    retrieved_at: str
    content_type: str
    response_bytes: int
    sha256: str
    title: str | None
    product_card_counts: dict[str, int]
    next_links: list[str]
    blocked_signal: str | None
    saved_html: str


def detect_block(response: requests.Response) -> str | None:
    """Return a reason when the response looks like an access block."""

    if response.status_code == 403:
        return "HTTP 403 access denial"
    if response.status_code == 429:
        return "HTTP 429 rate limit"
    lowered = response.text[:250_000].lower()
    signals = {
        "captcha": "CAPTCHA text detected",
        "access denied": "Access-denied text detected",
        "unusual traffic": "Unusual-traffic text detected",
    }
    for needle, description in signals.items():
        if needle in lowered:
            return description
    return None


def selector_counts(soup: BeautifulSoup) -> dict[str, int]:
    """Count likely product-card selectors without assuming one is correct."""

    selectors = (
        "article.prd",
        "article.prd._fb.col.c-prd",
        "article[data-sku]",
        "article[data-id]",
        "a.core",
        "a.core[data-gtm-id]",
        "h3.name",
        "div.prc",
        "div.old",
        "div.bdg._dsct",
        "div.stars",
        "a[aria-label='Next Page']",
    )
    return {selector: len(soup.select(selector)) for selector in selectors}


def find_next_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Collect likely pagination links for later human verification."""

    links: list[str] = []
    for anchor in soup.select("a[href]"):
        label = " ".join(anchor.get_text(" ", strip=True).split()).lower()
        aria = (anchor.get("aria-label") or "").lower()
        rel = " ".join(anchor.get("rel") or []).lower()
        href = anchor.get("href") or ""
        if "next" in label or "next" in aria or "next" in rel or "page=2" in href:
            absolute = urljoin(base_url, href)
            if absolute not in links:
                links.append(absolute)
    return links


def fetch_public_page(
    session: requests.Session,
    label: str,
    url: str,
    timeout: float,
) -> tuple[requests.Response, PageEvidence]:
    """Fetch one public page and save an exact local HTML evidence copy."""

    retrieved_at = nairobi_now()
    response = session.get(url, timeout=timeout, allow_redirects=True)
    content = response.content
    digest = hashlib.sha256(content).hexdigest()
    suffix = "txt" if label == "robots" else "html"
    evidence_name = f"{safe_filename(label)}_{retrieved_at:%Y%m%dT%H%M%S%z}.{suffix}"
    evidence_path = EVIDENCE_DIR / evidence_name
    evidence_path.write_bytes(content)

    soup = BeautifulSoup(content, "html.parser")
    evidence = PageEvidence(
        label=label,
        requested_url=url,
        final_url=response.url,
        status_code=response.status_code,
        retrieved_at=retrieved_at.isoformat(),
        content_type=response.headers.get("Content-Type", ""),
        response_bytes=len(content),
        sha256=digest,
        title=soup.title.get_text(" ", strip=True) if soup.title else None,
        product_card_counts=selector_counts(soup) if label != "robots" else {},
        next_links=find_next_links(soup, response.url) if label != "robots" else [],
        blocked_signal=detect_block(response),
        saved_html=str(evidence_path.relative_to(EVIDENCE_DIR.parent.parent)),
    )
    return response, evidence


def run_reconnaissance(
    contact_email: str,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    timeout: float = 30.0,
    labels: set[str] | None = None,
) -> list[PageEvidence]:
    """Retrieve robots.txt and one page for each assigned category."""

    if not 2.0 <= delay_seconds <= 5.0:
        raise ValueError("Reconnaissance delay must be between 2 and 5 seconds.")

    ensure_project_directories()
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": build_user_agent(contact_email),
            "Accept-Language": "en-NG,en;q=0.9",
        }
    )

    all_targets: Iterable[tuple[str, str]] = (
        ("robots", ROBOTS_URL),
        *CATEGORY_URLS.items(),
    )
    targets = [
        (label, url)
        for label, url in all_targets
        if labels is None or label in labels
    ]
    evidence_items: list[PageEvidence] = []
    previous_request_finished: float | None = None

    for label, url in targets:
        if previous_request_finished is not None:
            elapsed = time.monotonic() - previous_request_finished
            time.sleep(max(0.0, delay_seconds - elapsed))

        response, evidence = fetch_public_page(session, label, url, timeout)
        previous_request_finished = time.monotonic()
        evidence_items.append(evidence)

        if evidence.blocked_signal:
            break
        if response.status_code >= 400:
            break

    timestamp = nairobi_now()
    metadata_path = EVIDENCE_DIR / f"reconnaissance_http_{timestamp:%Y%m%dT%H%M%S%z}.json"
    write_json(metadata_path, [asdict(item) for item in evidence_items])
    return evidence_items


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    runtime_email = os.environ.get("JUMIA_CONTACT_EMAIL")
    parser.add_argument(
        "--contact-email",
        default=runtime_email,
        required=runtime_email is None,
        help="Contact email, or set JUMIA_CONTACT_EMAIL.",
    )
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--labels",
        nargs="+",
        choices=["robots", *CATEGORY_URLS.keys()],
        help="Optional subset to retrieve when continuing interrupted reconnaissance.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    evidence_items = run_reconnaissance(
        contact_email=args.contact_email,
        delay_seconds=args.delay,
        timeout=args.timeout,
        labels=set(args.labels) if args.labels else None,
    )
    print(json.dumps([asdict(item) for item in evidence_items], indent=2))
    if not evidence_items:
        return 1
    final = evidence_items[-1]
    return 2 if final.blocked_signal or final.status_code >= 400 else 0


if __name__ == "__main__":
    raise SystemExit(main())

