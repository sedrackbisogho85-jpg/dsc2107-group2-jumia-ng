# Day 1 collection quality report

**Collection date:** 13 October 2026 (`Africa/Nairobi`)

**Website:** Jumia Nigeria

**Categories:** Phones & Tablets, Computing, Electronics

## Pre-collection checks

The live one-page check returned HTTP 200 and parsed 40 Phones & Tablets cards
with zero parsing errors. The three saved reconnaissance pages also produced 40
main catalogue cards each with zero parsing errors. Five unit tests passed.

## Sample result

The sample collected 120 unique products: 40 from each category. It used five
HTTP attempts because one Computing request timed out and succeeded on the
controlled retry. Validation found zero duplicate IDs, zero malformed cards,
and zero timestamp errors. Two products had no old price or displayed discount;
those values were correctly left missing rather than changed to zero.

## Daily Run 1 result

The accepted raw file is `data/raw/jumia_ng_products_2026-10-13.csv`.

| Check | Observed result |
|---|---:|
| Unique products | 639 |
| Phones & Tablets memberships | 239 |
| Computing memberships | 200 |
| Electronics memberships | 200 |
| Duplicate rows in saved file | 0 |
| Malformed cards | 0 |
| HTTP attempts | 19 |
| Configured minimum delay | 3 seconds |
| Missing old prices | 26 |
| Missing displayed discounts | 26 |
| Missing ratings | 3 |
| Missing review counts | 3 |
| Timestamp errors | 0 |

Two listing requests timed out and were retried successfully. There were no
403 responses, 429 responses, CAPTCHAs, or explicit access-denial pages. The
run stayed far below the 1,000-request limit.

The manifest-recorded SHA-256 and the independently recalculated SHA-256 both
equal `6d33a6b278c7ebc371d233624f94d46dd2222cdc0b71cd2537dc62a48bd52b48`.
This confirms that the accepted raw file was unchanged after collection.

## Cleaning and database check

Cleaning created 639 rows and removed zero duplicates. Missing values remained
missing. No impossible-price, invalid-rating, or discount-tolerance flags were
raised. The normalized SQLite build contains 639 products, three categories,
639 product-category links, and 639 observations. `PRAGMA foreign_key_check`
reported zero errors.

