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
python -m src.database_loader data/cleaned/jumia_ng_products_YYYY-MM-DD_cleaned.csv database/jumia_ng.sqlite
```

If an ordinary failure interrupts a collection, resume from its checkpoint
without requesting completed pages again:

```powershell
python -m src.scraper daily --resume data/checkpoints/daily_TIMESTAMP.json
```

The same email can instead be supplied with `--contact-email`. It is never
hard-coded into the project.

## Day 1 status

The repository was separated from the Books to Scrape warm-up on 13 October
2026. Reconnaissance, parser validation, the sample, and Daily Run 1 were then
completed in that order.

- sample: 120 valid unique products, 40 per category
- Daily Run 1: 639 valid unique products
- Daily category memberships: 239 Phones & Tablets, 200 Computing, 200 Electronics
- Daily HTTP attempts: 19, including two successful timeout retries
- duplicate rows in the saved daily CSV: 0
- raw checksum verified against the run manifest

Raw datasets, generated cleaned files, checkpoints, logs, and SQLite databases
remain local and are ignored by Git. They must not be manually edited.

## Important files

- `reconnaissance/reconnaissance_note.md` explains the live site findings.
- `src/scraper.py` performs controlled sample and daily collection.
- `src/validator.py` checks raw files without changing them.
- `src/cleaner.py` produces a separate analysis-ready CSV.
- `src/database_loader.py` rebuilds the normalized SQLite database.
- `report/data_dictionary.md` defines the dataset columns.
- `report/day1_quality_report.md` records the observed Day 1 evidence.


