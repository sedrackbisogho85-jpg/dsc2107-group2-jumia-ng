"""Responsible, resumable Jumia Nigeria category scraper."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup, Tag

from .config import (
    BASE_URL,
    CATEGORY_URLS,
    CHECKPOINT_DIR,
    CURRENCY,
    DEFAULT_DAILY_TARGET,
    DEFAULT_DELAY_SECONDS,
    DEFAULT_REQUEST_LIMIT,
    DEFAULT_SAMPLE_TARGET,
    LOG_DIR,
    MAX_RETRIES,
    MINIMUM_DAILY_TARGET,
    RAW_DIR,
    RAW_FIELDS,
    ROBOTS_URL,
    SOURCE_SITE,
    ensure_project_directories,
)
from .utils import BOT_TOKEN, build_user_agent, nairobi_now, sha256_file, write_json


CATEGORY_SEPARATOR = " | "


class AccessBlocked(RuntimeError):
    """Raised when Jumia explicitly blocks or challenges the scraper."""

    def __init__(self, message: str, url: str, status_code: int | None = None):
        super().__init__(message)
        self.url = url
        self.status_code = status_code


class RequestLimitExceeded(RuntimeError):
    """Raised before a request would exceed the configured limit."""


class RobotsDenied(RuntimeError):
    """Raised when robots.txt does not permit a requested URL."""


@dataclass
class RunStats:
    run_id: str
    mode: str
    started_at: str
    finished_at: str | None = None
    request_count: int = 0
    actual_delay_seconds: float = DEFAULT_DELAY_SECONDS
    pages_visited: list[dict[str, Any]] = field(default_factory=list)
    duplicates: int = 0
    malformed_cards: int = 0
    failures: list[str] = field(default_factory=list)
    robots_url: str = ROBOTS_URL
    robots_status: int | None = None
    robots_sha256: str | None = None


class PoliteFetcher:
    """Sequential HTTP client with rate limiting and bounded retries."""

    def __init__(
        self,
        contact_email: str,
        delay_seconds: float,
        request_limit: int,
        logger: logging.Logger,
    ) -> None:
        if not 2.0 <= delay_seconds <= 5.0:
            raise ValueError("The request delay must be between 2 and 5 seconds.")
        if request_limit < 1:
            raise ValueError("The request limit must be positive.")
        self.delay_seconds = delay_seconds
        self.request_limit = request_limit
        self.logger = logger
        self.request_count = 0
        self.last_request_finished: float | None = None
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": build_user_agent(contact_email),
                "Accept-Language": "en-NG,en;q=0.9",
            }
        )

    def _wait(self) -> None:
        if self.last_request_finished is None:
            return
        elapsed = time.monotonic() - self.last_request_finished
        time.sleep(max(0.0, self.delay_seconds - elapsed))

    @staticmethod
    def _block_signal(response: requests.Response) -> str | None:
        if response.status_code == 403:
            return "HTTP 403 access denial"
        if response.status_code == 429:
            return "HTTP 429 rate limit"
        lowered = response.text[:250_000].lower()
        for needle, message in (
            ("captcha", "CAPTCHA text detected"),
            ("access denied", "Access-denied text detected"),
            ("unusual traffic", "Unusual-traffic text detected"),
        ):
            if needle in lowered:
                return message
        return None

    def get(self, url: str, timeout: float = 30.0) -> tuple[requests.Response, str]:
        """Fetch a URL, retrying only temporary failures and 5xx responses."""

        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            if self.request_count >= self.request_limit:
                raise RequestLimitExceeded(
                    f"Stopped before exceeding request limit {self.request_limit}."
                )

            self._wait()
            self.request_count += 1
            self.logger.info(
                "Request %s/%s attempt=%s url=%s",
                self.request_count,
                self.request_limit,
                attempt,
                url,
            )
            try:
                response = self.session.get(url, timeout=timeout, allow_redirects=True)
                retrieved_at = nairobi_now().isoformat()
                self.last_request_finished = time.monotonic()
            except (requests.ConnectionError, requests.Timeout) as error:
                self.last_request_finished = time.monotonic()
                last_error = error
                self.logger.warning("Temporary network failure: %s", error)
                if attempt < MAX_RETRIES:
                    time.sleep(self.delay_seconds * attempt)
                    continue
                raise RuntimeError(f"Request failed after {MAX_RETRIES} attempts: {url}") from error

            block_signal = self._block_signal(response)
            if block_signal:
                raise AccessBlocked(block_signal, response.url, response.status_code)

            if 500 <= response.status_code <= 599:
                last_error = RuntimeError(
                    f"Temporary HTTP {response.status_code} at {response.url}"
                )
                self.logger.warning("%s", last_error)
                if attempt < MAX_RETRIES:
                    time.sleep(self.delay_seconds * attempt)
                    continue
                raise last_error

            response.raise_for_status()
            return response, retrieved_at

        raise RuntimeError(f"Unable to fetch {url}: {last_error}")


def normalize_product_url(href: str) -> str:
    """Return a canonical absolute product URL without tracking data."""

    absolute = urljoin(BASE_URL, href)
    parts = urlsplit(absolute)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, "", ""))


def text_or_none(card: Tag, selector: str) -> str | None:
    element = card.select_one(selector)
    if element is None:
        return None
    value = " ".join(element.get_text(" ", strip=True).split())
    return value or None


def parse_product_card(card: Tag, category: str, scraped_at: str) -> dict[str, str | None]:
    """Parse one observed main-listing card using reconnaissance selectors."""

    core = card.select_one("a.core")
    if core is None:
        raise ValueError("Product card has no a.core link.")

    source_product_id = core.get("data-gtm-id") or core.get("data-ga4-item_id")
    href = core.get("href")
    product_name = text_or_none(card, "h3.name") or core.get("data-gtm-name")
    if not source_product_id or not href or not product_name:
        raise ValueError("Product card is missing its stable ID, URL, or name.")

    brand = core.get("data-gtm-brand") or core.get("data-ga4-item_brand")
    review_text = text_or_none(card, "div.rev")
    review_match = re.search(r"\([\d,]+\)\s*$", review_text or "")

    return {
        "source_product_id": str(source_product_id).strip(),
        "product_name": str(product_name).strip(),
        "brand": str(brand).strip() if brand else None,
        "current_price_raw": text_or_none(card, "div.prc"),
        "old_price_raw": text_or_none(card, "div.old"),
        "displayed_discount_raw": text_or_none(card, "div.bdg._dsct"),
        "rating_raw": text_or_none(card, "div.stars"),
        "review_count_raw": review_match.group(0) if review_match else None,
        "category": category,
        "product_url": normalize_product_url(str(href)),
        "currency": CURRENCY,
        "source_site": SOURCE_SITE,
        "scraped_at": scraped_at,
        "scrape_date": scraped_at[:10],
    }


def parse_product_cards(
    html: bytes | str,
    category: str,
    scraped_at: str,
) -> tuple[list[dict[str, str | None]], list[str]]:
    """Parse only the 40-card catalogue grid, continuing past malformed cards."""

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("article.prd._fb.col.c-prd")
    products: list[dict[str, str | None]] = []
    errors: list[str] = []
    for index, card in enumerate(cards, start=1):
        try:
            products.append(parse_product_card(card, category, scraped_at))
        except (AttributeError, TypeError, ValueError) as error:
            errors.append(f"card {index}: {error}")
    return products, errors


def page_url(category_url: str, page_number: int) -> str:
    if page_number == 1:
        return category_url
    return f"{category_url}?page={page_number}"


def make_logger(run_id: str, mode: str) -> tuple[logging.Logger, Path]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"scrape_{mode}_{run_id}.log"
    logger = logging.getLogger(f"jumia.{mode}.{run_id}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger, path


def save_checkpoint(
    checkpoint_path: Path,
    products: dict[str, dict[str, str | None]],
    completed_pages: list[dict[str, Any]],
    stats: RunStats,
    status: str,
) -> None:
    payload = {
        "status": status,
        "saved_at": nairobi_now().isoformat(),
        "products": list(products.values()),
        "completed_pages": completed_pages,
        "stats": asdict(stats),
    }
    temporary = checkpoint_path.with_suffix(".tmp")
    write_json(temporary, payload)
    temporary.replace(checkpoint_path)


def load_checkpoint(
    checkpoint_path: Path,
) -> tuple[dict[str, dict[str, str | None]], list[dict[str, Any]], dict[str, Any]]:
    """Load preserved progress without changing the original checkpoint."""

    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    product_rows = payload.get("products", [])
    products = {
        str(row["source_product_id"]): row
        for row in product_rows
        if row.get("source_product_id")
    }
    completed_pages = payload.get("completed_pages", [])
    previous_stats = payload.get("stats", {})
    return products, completed_pages, previous_stats


def merge_product(
    products: dict[str, dict[str, str | None]],
    product: dict[str, str | None],
    stats: RunStats,
) -> None:
    product_id = str(product["source_product_id"])
    existing = products.get(product_id)
    if existing is None:
        products[product_id] = product
        return

    stats.duplicates += 1
    existing_categories = str(existing["category"]).split(CATEGORY_SEPARATOR)
    new_category = str(product["category"])
    if new_category not in existing_categories:
        existing["category"] = CATEGORY_SEPARATOR.join([*existing_categories, new_category])


def category_counts(products: dict[str, dict[str, str | None]]) -> dict[str, int]:
    counts = {category: 0 for category in CATEGORY_URLS}
    for product in products.values():
        for category in str(product["category"]).split(CATEGORY_SEPARATOR):
            if category in counts:
                counts[category] += 1
    return counts


def output_path(mode: str, completed: bool, run_id: str, scrape_date: str) -> Path:
    if mode == "sample":
        return RAW_DIR / f"jumia_ng_sample_{run_id}.csv"
    preferred = RAW_DIR / f"jumia_ng_products_{scrape_date}.csv"
    if completed and not preferred.exists():
        return preferred
    suffix = "" if completed else "_incomplete"
    return RAW_DIR / f"jumia_ng_products_{run_id}{suffix}.csv"


def write_raw_csv(path: Path, rows: list[dict[str, str | None]]) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing raw file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", newline="", encoding="utf-8-sig") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=RAW_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def record_incident(
    run_id: str,
    error: Exception,
    delay_seconds: float,
    request_count: int,
) -> Path:
    path = LOG_DIR / f"incident_{run_id}.json"
    write_json(
        path,
        {
            "date_time": nairobi_now().isoformat(),
            "url": getattr(error, "url", None),
            "http_status": getattr(error, "status_code", None),
            "delay_seconds": delay_seconds,
            "request_count": request_count,
            "error": str(error),
            "action_taken": "Stopped immediately; no circumvention attempted.",
        },
    )
    return path


def write_manifest(
    mode: str,
    run_id: str,
    stats: RunStats,
    products: dict[str, dict[str, str | None]],
    raw_path: Path | None,
    completion_status: str,
    target: int,
    log_path: Path,
) -> Path:
    counts = category_counts(products)
    manifest = {
        "run_id": run_id,
        "mode": mode,
        "start_time": stats.started_at,
        "finish_time": stats.finished_at,
        "record_count": len(products),
        "unique_product_count": len(products),
        "category_counts": counts,
        "request_count": stats.request_count,
        "actual_delay_seconds": stats.actual_delay_seconds,
        "completion_status": completion_status,
        "target": target,
        "target_met": len(products) >= target,
        "duplicate_cards_merged": stats.duplicates,
        "malformed_cards": stats.malformed_cards,
        "errors": stats.failures,
        "pages_visited": stats.pages_visited,
        "robots_url": stats.robots_url,
        "robots_status": stats.robots_status,
        "robots_sha256": stats.robots_sha256,
        "raw_file": str(raw_path.relative_to(RAW_DIR.parent.parent)) if raw_path else None,
        "raw_file_sha256": sha256_file(raw_path) if raw_path else None,
        "log_file": str(log_path.relative_to(LOG_DIR.parent)),
    }
    manifest_path = RAW_DIR / f"manifest_{mode}_{run_id}.json"
    if manifest_path.exists():
        raise FileExistsError(f"Refusing to overwrite manifest: {manifest_path}")
    write_json(manifest_path, manifest)
    with (RAW_DIR / "run_manifest.jsonl").open("a", encoding="utf-8") as file_handle:
        file_handle.write(json.dumps(manifest, ensure_ascii=False) + "\n")
    return manifest_path


def run_collection(
    mode: str,
    contact_email: str,
    target: int,
    max_pages: int,
    delay_seconds: float,
    request_limit: int,
    resume_checkpoint: Path | None = None,
) -> dict[str, Any]:
    """Run a sample or daily collection and preserve all outcome evidence."""

    ensure_project_directories()
    started = nairobi_now()
    run_id = started.strftime("%Y-%m-%dT%H%M%S%z")
    logger, log_path = make_logger(run_id, mode)
    stats = RunStats(
        run_id=run_id,
        mode=mode,
        started_at=started.isoformat(),
        actual_delay_seconds=delay_seconds,
    )
    fetcher = PoliteFetcher(contact_email, delay_seconds, request_limit, logger)
    checkpoint_path = CHECKPOINT_DIR / f"{mode}_{run_id}.json"
    products: dict[str, dict[str, str | None]] = {}
    completed_pages: list[dict[str, Any]] = []
    fatal_error: Exception | None = None

    if resume_checkpoint is not None:
        products, completed_pages, previous_stats = load_checkpoint(resume_checkpoint)
        stats.pages_visited = list(completed_pages)
        stats.duplicates = int(previous_stats.get("duplicates", 0))
        stats.malformed_cards = int(previous_stats.get("malformed_cards", 0))
        fetcher.request_count = int(previous_stats.get("request_count", 0))
        logger.info(
            "Resuming from %s with products=%s completed_pages=%s prior_requests=%s",
            resume_checkpoint,
            len(products),
            len(completed_pages),
            fetcher.request_count,
        )

    completed_keys = {
        (str(page.get("category")), int(page.get("page", 0)))
        for page in completed_pages
    }

    try:
        robots_response, _ = fetcher.get(ROBOTS_URL)
        stats.robots_status = robots_response.status_code
        stats.robots_sha256 = __import__("hashlib").sha256(robots_response.content).hexdigest()
        robots = RobotFileParser()
        robots.parse(robots_response.text.splitlines())

        initial_counts = category_counts(products)
        stop_requested = len(products) >= target and all(initial_counts.values())
        for page_number in range(1, max_pages + 1):
            if stop_requested:
                break
            new_products_this_round = 0
            requested_pages_this_round = 0
            for category, category_url in CATEGORY_URLS.items():
                if (category, page_number) in completed_keys:
                    logger.info(
                        "Skipping completed category=%s page=%s",
                        category,
                        page_number,
                    )
                    continue
                url = page_url(category_url, page_number)
                if not robots.can_fetch(BOT_TOKEN, url):
                    raise RobotsDenied(f"robots.txt does not permit {url}")

                response, scraped_at = fetcher.get(url)
                requested_pages_this_round += 1
                parsed, parsing_errors = parse_product_cards(
                    response.content,
                    category,
                    scraped_at,
                )
                if not parsed:
                    stats.failures.append(f"No catalogue cards found at {url}")
                stats.malformed_cards += len(parsing_errors)
                stats.failures.extend(f"{url}: {error}" for error in parsing_errors)

                before = len(products)
                for product in parsed:
                    merge_product(products, product, stats)
                added = len(products) - before
                new_products_this_round += added
                page_record = {
                    "category": category,
                    "page": page_number,
                    "url": response.url,
                    "status": response.status_code,
                    "cards": len(parsed),
                    "new_unique_products": added,
                    "scraped_at": scraped_at,
                }
                stats.pages_visited.append(page_record)
                completed_pages.append(page_record)
                stats.request_count = fetcher.request_count
                save_checkpoint(
                    checkpoint_path,
                    products,
                    completed_pages,
                    stats,
                    "in_progress",
                )
                logger.info(
                    "Parsed category=%s page=%s cards=%s unique_total=%s",
                    category,
                    page_number,
                    len(parsed),
                    len(products),
                )

                counts = category_counts(products)
                if len(products) >= target and all(counts.values()):
                    stop_requested = True
                    break

            if stop_requested:
                break
            if requested_pages_this_round and new_products_this_round == 0:
                stats.failures.append("Stopped because a full page round added no products.")
                break

    except (AccessBlocked, RequestLimitExceeded, RobotsDenied, requests.RequestException, RuntimeError) as error:
        fatal_error = error
        stats.failures.append(str(error))
        logger.error("Collection stopped: %s", error)
        if isinstance(error, AccessBlocked):
            record_incident(run_id, error, delay_seconds, fetcher.request_count)
    finally:
        stats.request_count = fetcher.request_count
        stats.finished_at = nairobi_now().isoformat()

    counts = category_counts(products)
    required_minimum = DEFAULT_SAMPLE_TARGET if mode == "sample" else MINIMUM_DAILY_TARGET
    completed = (
        fatal_error is None
        and len(products) >= required_minimum
        and all(counts.values())
    )
    completion_status = "complete" if completed else "incomplete"
    raw_path: Path | None = None
    if products:
        raw_path = output_path(mode, completed, run_id, started.date().isoformat())
        write_raw_csv(raw_path, list(products.values()))

    save_checkpoint(
        checkpoint_path,
        products,
        completed_pages,
        stats,
        completion_status,
    )
    manifest_path = write_manifest(
        mode,
        run_id,
        stats,
        products,
        raw_path,
        completion_status,
        target,
        log_path,
    )
    result = {
        "completion_status": completion_status,
        "record_count": len(products),
        "category_counts": counts,
        "duplicate_cards_merged": stats.duplicates,
        "malformed_cards": stats.malformed_cards,
        "request_count": stats.request_count,
        "delay_seconds": delay_seconds,
        "errors": stats.failures,
        "raw_file": str(raw_path) if raw_path else None,
        "manifest": str(manifest_path),
        "checkpoint": str(checkpoint_path),
        "log": str(log_path),
    }
    logger.info("Run result: %s", json.dumps(result, ensure_ascii=False))
    return result


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("sample", "daily"))
    runtime_email = os.environ.get("JUMIA_CONTACT_EMAIL")
    parser.add_argument(
        "--contact-email",
        default=runtime_email,
        required=runtime_email is None,
        help="Contact email, or set JUMIA_CONTACT_EMAIL.",
    )
    parser.add_argument("--target", type=int)
    parser.add_argument("--max-pages", type=int, default=8)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--request-limit", type=int, default=DEFAULT_REQUEST_LIMIT)
    parser.add_argument(
        "--resume",
        type=Path,
        help="Optional checkpoint to resume; completed pages will not be requested again.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    target = args.target or (
        DEFAULT_SAMPLE_TARGET if args.mode == "sample" else DEFAULT_DAILY_TARGET
    )
    result = run_collection(
        mode=args.mode,
        contact_email=args.contact_email,
        target=target,
        max_pages=args.max_pages,
        delay_seconds=args.delay,
        request_limit=args.request_limit,
        resume_checkpoint=args.resume,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["completion_status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())

