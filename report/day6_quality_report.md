# Day 6 collection quality report

**Collection date:** 18 October 2026 (`UTC+03:00`)

**Website:** Jumia Nigeria

**Run ID:** `2026-10-18T222042+0300`

**Contributor:** Masaba Carl

## Evidence used

This report uses only the saved Day 6 raw CSV, cleaned CSV, validation JSON,
scraper manifest, scraper log and six-day candidate SQLite database. No new
scraping was performed. The evidence files were:

- `data/raw/jumia_ng_products_2026-10-18.csv`
- `data/cleaned/jumia_ng_products_2026-10-18_cleaned.csv`
- `data/raw/validation_daily_2026-10-18.json`
- `data/raw/manifest_daily_2026-10-18T222042+0300.json`
- `logs/scrape_daily_2026-10-18T222042+0300.log`
- `BACKUPS/jumia_ng_day6_candidate.sqlite`

## 1. Objective and collection method

The Day 6 objective was to create a dated product snapshot from the three
selected Jumia Nigeria categories. The manifest set a target of 600 products,
while the validator required at least 500 records.

The scraper ran in daily mode. It first requested `robots.txt`, which returned
HTTP 200. It then visited five listing pages in each category. The pages were
requested in a repeating order: Phones & Tablets, Computing, then Electronics.
Each of the 15 listing pages produced 40 product cards and 40 new unique
products. The run started at `22:20:42.501667` and finished at
`22:22:25.268596`, both at `UTC+03:00`, giving a recorded duration of about
102.77 seconds.

## 2. Product categories

All three planned categories were present and contributed equally to the raw
dataset.

| Category | Pages visited | Products | Share of records |
|---|---:|---:|---:|
| Phones & Tablets | 5 | 200 | 33.33% |
| Computing | 5 | 200 | 33.33% |
| Electronics | 5 | 200 | 33.33% |
| **Total** | **15** | **600** | **100.00%** |

## 3. Collected and validated products

The manifest reports 600 records and 600 unique products. Therefore, the
600-product target was met. The validation file independently read 600 records,
found all required columns, and returned `passed: true`. The result was also
100 records above the validator's minimum requirement of 500.

## 4. Requests, delay and scraping errors

| Check | Observed result |
|---|---:|
| Total HTTP requests | 16 |
| `robots.txt` requests | 1 |
| Listing-page requests | 15 |
| Recorded delay setting | 3.0 seconds |
| Request limit shown in the log | 1,000 |
| Listing responses with HTTP 200 | 15 of 15 |
| Retries | 0 |
| Scraper errors | 0 |
| Malformed cards | 0 |
| Duplicate cards merged | 0 |

Every request in the log is marked `attempt=1`, so no retry was needed. The
manifest records the run as `complete`, with an empty error list. The 16
requests were far below the 1,000-request limit shown in the log.

## 5. Missing values and interpretation

The raw validation results were:

| Raw field | Missing values | Percentage of 600 records |
|---|---:|---:|
| Old price | 27 | 4.50% |
| Displayed discount | 27 | 4.50% |
| Rating | 3 | 0.50% |
| Review count | 3 | 0.50% |
| Every other raw field | 0 | 0.00% |

The same 27 products were missing both an old price and a displayed discount.
This means that no comparison price or discount was available in the captured
listing for those products; it does not mean that their value was zero. The
same three products were missing both a rating and a review count. The evidence
does not show whether they were unrated or whether those values were simply not
displayed, so they are correctly treated as unavailable.

The complete product IDs, names, brands, current prices, categories, URLs and
timestamps, together with zero malformed cards and zero scraper errors, show
that these optional missing values were not recorded as failed product rows.

## 6. Duplicate and timestamp validation

The validation file reports zero duplicates and zero timestamp errors. A direct
check of the raw CSV also found zero repeated full rows, zero repeated product
IDs and zero repeated product/date pairs.

All 600 rows have the scrape date `2026-10-18`. Their `scraped_at` values range
from `2026-10-18T22:20:48.839984+03:00` to
`2026-10-18T22:22:25.094781+03:00`. There are 15 distinct timestamps, matching
the 15 listing pages; the 40 cards from each page share that page's collection
timestamp. This is expected page-level timestamp behaviour rather than a
duplicate-data problem.

## 7. SHA-256 data integrity

The manifest-recorded SHA-256 for the raw CSV is:

`f3ccc5487ab418c2ba02fa4457f4013b180cd5f86c6e3969928ee12d4116c1ac`

The SHA-256 recalculated from the current raw CSV is exactly the same. This
confirms that the file currently being reviewed is byte-for-byte consistent
with the checksum saved in the scraper manifest. The checksum protects against
an unnoticed file change after collection, although it does not by itself prove
that every value shown by the website was correct.

## 8. Cleaned dataset results

Cleaning produced 600 rows. The set of 600 product IDs is identical in the raw
and cleaned files, so no product was removed and no duplicate was introduced.
The cleaned category totals also remain 200 products per category.

| Cleaned-data check | Result |
|---|---:|
| Rows | 600 |
| Unique product IDs | 600 |
| Parsed current prices | 600 |
| Parsed old prices | 573 |
| Parsed displayed discounts | 573 |
| Calculated discounts | 573 |
| Parsed ratings | 597 |
| Parsed review counts | 597 |
| Discount-difference flags | 0 |
| Other validation flags | 0 |

The cleaner converted price, discount, rating and review-count text into
numeric columns. It preserved all missing information: 27 old prices, 27
displayed discounts and 27 calculated discounts remain blank, while three
ratings and three review counts remain blank. Missing values were not changed
to zero.

## 9. Six-day candidate database integrity

The candidate database contains 787 distinct products, three categories, 787
product-category links and 3,713 dated observations. The daily observation
counts are:

| Scrape date | Observations | Unique products that day |
|---|---:|---:|
| 13 October 2026 | 639 | 639 |
| 14 October 2026 | 600 | 600 |
| 15 October 2026 | 639 | 639 |
| 16 October 2026 | 600 | 600 |
| 17 October 2026 | 635 | 635 |
| 18 October 2026 | 600 | 600 |
| **Total observations** | **3,713** | **787 distinct products across all six days** |

The total in the final row is a six-day observation total, while 787 is the
number of distinct products after the same product is linked across dates.
For 18 October, the database contains 600 observations and 600 unique products.

Read-only database checks returned `ok` from `PRAGMA integrity_check`, zero
rows from `PRAGMA foreign_key_check`, zero orphan records and zero duplicate
product/date observations. The candidate database SHA-256 at the time of this
review is
`4fd03196a9b51403cc42d7c15e54faa6b2a0660ea933c4a96651b3fd7bf31784`.
This database is a review candidate; the original database was not replaced or
modified during this reporting work.

## 10. Limitations and pending review

- The collection covers five listing pages per category, not the complete
  Jumia Nigeria catalogue.
- Product listings can change during and after the approximately 103-second
  run, so this is a snapshot rather than a permanent description of the site.
- Page-level timestamps do not show the exact time at which each individual
  card was parsed.
- The saved evidence confirms no reported scraper errors, but it cannot prove
  that the website itself contained no incorrect or temporarily omitted data.
- Missing optional values cannot be classified further without evidence beyond
  the saved files.
- The six-day SQLite file remains a candidate. A different group member still
  needs to recalculate the raw checksum, review the evidence and approve the
  run before publication or replacement of the original database.

Based on the available local evidence, Day 6 met its collection target and all
recorded validation, integrity, duplicate and timestamp checks passed. Final
acceptance remains subject to independent group-member review.
