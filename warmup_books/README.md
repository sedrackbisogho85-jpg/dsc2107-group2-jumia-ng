# DSC2107 Data Mining and Wrangling — Group 2 Books to Scrape Warm-up

**Programme:** BSc Data Science and Analytics, Year 2, Semester 1

**Institution:** Uganda Christian University

**Warm-up source:** Books to Scrape (`https://books.toscrape.com/`)

**Main-assignment site:** Jumia Nigeria (separate project; no Jumia data is stored here)

**Final offline validation:** 17 October 2026 — PASS

## Project objective

This warm-up practises a complete, responsible web-data collection workflow before Group 2 begins its separate Jumia Nigeria assignment. It demonstrates catalogue pagination, individual detail-page extraction, checkpointed CSV output, retry handling, request pacing, resumable collection, persistent daily request accounting, and offline data-quality validation.

The collection is complete. The local files contain 1,000 indexed book URLs and 1,000 detailed records. Finalisation did not perform any new web requests or modify either source dataset.

## Environment setup

From Windows PowerShell in this project directory:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Only two direct third-party packages are required: `requests` for HTTP and `beautifulsoup4` for HTML parsing. CSV, JSON, path handling, dates, URL parsing, and timing use the Python standard library.

If future network collection is explicitly authorised, configure the contact part of the User-Agent at runtime instead of placing an address in source control:

```powershell
$env:BOOKS_TO_SCRAPE_CONTACT_EMAIL = "<team-contact-email>"
```

`scraper_config.py` adds the configured value to `DSC2107-Group2-Warmup`. The variable is optional and its value is never written to the repository. No network collection is needed to reproduce the final validation.

## Files and responsibilities

| File | Purpose |
|---|---|
| `collect_book_links.py` | Follows catalogue pagination and writes the unique detail-page index. |
| `resume_book_details.py` | Resumable, rate-limited detail-page collector; checkpoints after each successful record. |
| `scraper_config.py` | Builds a shared User-Agent from an optional environment-provided contact email. |
| `validate_books.py` | Offline structural and data-quality validation; writes `validation_report.txt` and exits non-zero on failure. |
| `test_connection.py` | Early connectivity test. |
| `first_book.py` | Early one-book catalogue extraction test. |
| `page_one.py` | Early one-page extraction test. |
| `pagination_test.py` | Early two-page pagination test. |
| `all_pages.py` | Full 50-page catalogue-only extraction. |
| `book_details_test.py` | Early one-detail-page extraction test. |
| `five_book_details.py` | Early five-detail-page extraction test. |
| `book_links.csv` | Private local index: 1,000 rows and 1,000 unique detail URLs; not committed. |
| `books_detailed.csv` | Private local detailed dataset: 1,000 validated rows; not committed. |
| `books_all_pages.csv` | Private local catalogue-only result from 50 pages; not committed. |
| `daily_request_usage.json` | Private local request-accounting state; not committed. |
| `validation_report.txt` | Latest offline validation summary. |
| `WARMUP_FINAL_CHECKLIST.md` | Completion evidence and remaining manual actions. |

Files with names such as `*_backup.csv`, `*_backup.json`, and everything under `backups/` are local safety copies. Datasets, request logs, environments, and backups are excluded by `.gitignore`.

## Collection workflow and execution order

The network collection has already finished. Do not rerun the network scripts merely to reproduce the finalisation audit.

The original workflow was:

1. Use the small test scripts to confirm selectors on one book, one page, two pages, and a few detail pages.
2. Run `collect_book_links.py` to start at the catalogue root, follow each `Next` link with `urljoin`, stop after at most 50 pages, de-duplicate detail URLs, and checkpoint `book_links.csv` after every catalogue page.
3. Run `resume_book_details.py` as needed. It loads `book_links.csv` and any existing `books_detailed.csv`, skips URLs already saved, accepts only HTTPS URLs on `books.toscrape.com`, extracts the detail fields, and safely replaces the output through a temporary file after every successful book.
4. Run `validate_books.py` offline. If the private CSVs are in this directory, omit `--data-dir`. Otherwise, point it at their local directory:

```powershell
.\.venv\Scripts\python.exe validate_books.py --data-dir C:\path\to\private\warmup-data
```

The validator does not import `requests`, open remote URLs, or change either CSV dataset. It checks expected counts, URL coverage, duplicate index/detail URLs, duplicate UPCs, required fields, price/rating/review formats, catalogue page values, completion status, and URLs outside the original index.

## Pagination and detail-page extraction

`collect_book_links.py` parses `article.product_pod` entries, records the discovery page, title, and absolute detail URL, and follows `li.next a[href]` until pagination ends or 50 pages have been visited. Duplicate URLs are suppressed with an in-memory set.

`resume_book_details.py` reads each saved detail URL and extracts:

| Column | Meaning |
|---|---|
| `page` | Catalogue page where the detail URL was discovered. |
| `title` | Detail-page title. |
| `price` | Displayed price, retained in the source format such as `£51.77`. |
| `rating` | Text rating: `One`, `Two`, `Three`, `Four`, or `Five`. |
| `category` | Category read from the breadcrumb. |
| `upc` | Universal product code from the product-information table. |
| `availability` | Availability text from the product-information table. |
| `reviews` | Review count from the product-information table. |
| `detail_url` | Original book detail URL. |
| `status` | `complete` when all essential extracted fields are non-empty; otherwise `partial`. |

Structural validation cannot prove that every value exactly matches the historical web page. It confirms that the local final dataset conforms to the implemented schema and consistency rules.

## Resume, retry, and request controls

The final detail collector is designed to recover safely after interruption:

- Existing rows are loaded and their URLs are skipped.
- Each successful record is checkpointed using a temporary CSV followed by an atomic replace.
- A normal batch stops after 100 newly saved records.
- A run allows at most 110 HTTP attempts so retries cannot grow without a bound.
- Every HTTP attempt waits at least three seconds first.
- Connection failures and HTTP 5xx responses are retried up to three attempts with additional back-off.
- HTTP 403 and 429 responses stop collection.
- `daily_request_usage.json` reserves and persists each request before it is sent, with a conservative ceiling of 900 requests per day.
- When the date changes and no current-day count exists, the operator must enter requests already made by other scripts.

The daily counter is a local operational aid. It covers requests made through the final detail collector plus any manually entered prior count; it cannot automatically count requests made by the earlier standalone scripts. Only one collector instance should run at a time.

## Responsible-use notes

Earlier project notes record that `https://books.toscrape.com/robots.txt` returned HTTP 404 when it was checked during collection. This finalisation was intentionally offline and did not recheck that response. A missing robots file is not permission to scrape without limits.

The project used public practice pages, a course-identifying User-Agent, delays, bounded retries, request budgets, and stop conditions for access restrictions. A contact email can be supplied through `BOOKS_TO_SCRAPE_CONTACT_EMAIL`; no personal address is stored in the code. The project did not use authentication, CAPTCHA bypass, proxy evasion, or personal-data collection. The dataset is for coursework and is intentionally excluded from Git by default.

## Final verified results

`validate_books.py` was executed with `.venv\Scripts\python.exe` on 17 October 2026 and returned exit code 0:

| Check | Result |
|---|---:|
| Catalogue URL records | 1,000 |
| Unique URLs in index | 1,000 |
| Detailed records | 1,000 |
| Unique detailed URLs | 1,000 |
| Remaining URLs | 0 |
| Duplicate URLs in index | 0 |
| Duplicate detail URLs | 0 |
| Duplicate UPCs | 0 |
| Records with missing required fields | 0 |
| Invalid prices | 0 |
| Invalid ratings | 0 |
| Invalid review counts | 0 |
| Invalid catalogue page values | 0 |
| Records not marked complete | 0 |
| URLs outside the original index | 0 |
| Dataset count mismatches | 0 |

On the original workstation, the detailed and URL-index CSV files were copied unchanged into an ignored `backups/` directory during finalisation. Neither the datasets nor their backups are included in this Git branch.

## Repository integration

This warm-up is isolated under `warmup_books/` on the repository's `warmup` branch. It does not replace or alter the Jumia Nigeria files inherited from `origin/main`. Source code, documentation, dependency declarations, and the aggregate validation report are suitable for review; raw scraped CSVs, backups, request logs, environments, and temporary files remain local and ignored. If the instructor requires the full dataset, deliver it only through an approved private channel.
