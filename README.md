# DSC2107 Group 2 Jumia Nigeria Project

This is the independent main assignment repository for Uganda Christian
University's **Data Mining and Wrangling** course.

The project collects public product information from Jumia Nigeria for:

1. Phones & Tablets
2. Computing
3. Electronics

The intended observation period is 13–19 October 2026. Each observation uses
the real `Africa/Nairobi` date and a timezone-aware timestamp. Data must never
be fabricated or backdated.

## Responsible-use rule

The contact email is supplied at runtime and is not stored in source code:

```powershell
$env:JUMIA_CONTACT_EMAIL = "your-email@example.com"
python -m src.reconnaissance
python -m unittest discover -s tests -v
python -m src.live_test
python -m src.scraper sample --target 100 --max-pages 1
```

The scraper is sequential, uses a three-second delay by default, respects the
configured request limit, checks `robots.txt`, and stops on access denial,
CAPTCHA, HTTP 403, or persistent HTTP 429 responses.

For a daily run after the sample passes:

```powershell
python -m src.scraper daily --target 600 --max-pages 8
python -m src.validator data/raw/jumia_ng_products_YYYY-MM-DD.csv --minimum-records 500
python -m src.cleaner data/raw/jumia_ng_products_YYYY-MM-DD.csv
```

Rebuild the database from every accepted cleaned daily file. For the current
three-day dataset, use:

```powershell
python -m src.database_loader data/cleaned/jumia_ng_products_2026-10-13_cleaned.csv data/cleaned/jumia_ng_products_2026-10-14_cleaned.csv data/cleaned/jumia_ng_products_2026-10-15_cleaned.csv database/jumia_ng.sqlite --replace
```

The loader rejects duplicate observations for the same product and collection
date. Add each later accepted cleaned CSV to the same command when refreshing
the database.

If an ordinary failure interrupts a collection, resume from its checkpoint
without requesting completed pages again:

```powershell
python -m src.scraper daily --resume data/checkpoints/daily_TIMESTAMP.json
```

The same email can instead be supplied with `--contact-email`. It is never
hard-coded into the project.

## Current collection status

The repository was separated from the Books to Scrape warm-up on 13 October
2026. Reconnaissance, parser validation, the sample, and Daily Run 1 were then
completed in that order.

- sample: 120 valid unique products, 40 per category
- Daily Run 1: 639 valid unique products
- Daily category memberships: 239 Phones & Tablets, 200 Computing, 200 Electronics
- Daily HTTP attempts: 19, including two successful timeout retries
- duplicate rows in the saved daily CSV: 0
- raw checksum verified against the run manifest

Daily Run 2 was completed on 14 October 2026 before midnight in
`Africa/Nairobi`:

- 600 valid unique products, with 200 from each category
- 22 HTTP attempts, including 6 successful controlled timeout retries
- 0 duplicate product IDs and 0 malformed cards
- no CAPTCHA, HTTP 403, HTTP 429 or access-denial signal
- accepted SHA-256:
  `d0d48535403804ebce0bb63fad837c0c70a52954f47753c2c00c60bd17f2d091`

Daily Run 3 was completed on 15 October 2026 from 21:26:16 to 21:29:55 in
`Africa/Nairobi`:

- 639 valid unique products: 239 Phones & Tablets, 200 Computing and 200 Electronics
- 18 HTTP attempts, including 1 successful controlled timeout retry
- 0 duplicate saved product IDs and 0 malformed cards
- no CAPTCHA, HTTP 403, HTTP 429 or access-denial signal
- accepted SHA-256:
  `2e7102f2bd4dbf9d33e8b677640f1dbbc0a844029df88c321768efb68c91cfe5`

Daily Run 4 was completed on 16 October 2026 from 21:26:31 to 21:28:32 in Africa/Nairobi:

- 600 valid unique products, with 200 from each category
- 16 HTTP requests, with no errors recorded
- 0 duplicate cards merged and 0 malformed cards
- no CAPTCHA, HTTP 403, HTTP 429 or access-denial signal
- accepted SHA-256: ac3a696a396560e9c123cb710e600ffffa8ca365ea83486074316d8cf59aafacd

The project has completed 4 of 7 planned daily runs. The four-day database
contains 756 unique products and 2,478 observations. Day 3 shares 601 products
with previous days, adds 38 products not seen earlier, and omits 88 products
seen in an earlier sample. Day 4 adds 29 products not seen in the earlier three
daily runs. These are preliminary sample checks, not final seven-day
conclusions. All eight current unit tests pass.

Accepted raw datasets, generated cleaned files, checkpoints, logs, manifests,
and the SQLite database are committed so a fresh clone contains the complete
project evidence. Raw files must not be manually edited; verify their SHA-256
values against the manifests after cloning or merging.
## Important files

- `reconnaissance/reconnaissance_note.md` explains the live site findings.
- `src/scraper.py` performs controlled sample and daily collection.
- `src/validator.py` checks raw files without changing them.
- `src/cleaner.py` produces a separate analysis-ready CSV.
- `src/database_loader.py` rebuilds the normalized SQLite database.
- `report/data_dictionary.md` defines the dataset columns.
- `report/day1_quality_report.md` records the observed Day 1 evidence.


