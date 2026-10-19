# Day 6 Collection Contribution — Masaba Carl

**Course:** DSC2107 Data Mining and Wrangling  
**Project:** Group 2 — Jumia Nigeria  
**Collection date:** 18 October 2026  
**Git branch:** `masaba-day6-collection`

## Work completed

- Executed the existing Jumia Nigeria scraper using the approved daily collection settings.
- Collected 600 unique products across Phones & Tablets (200), Computing (200), and Electronics (200).
- Completed collection using 16 HTTP requests, with no reported scraper errors or duplicate product cards.
- Ran the raw-data validator and confirmed all validation checks passed.
- Cleaned 600 records with zero duplicates removed.
- Independently recalculated the raw CSV SHA-256 checksum and confirmed it matched the scraper manifest.
- Built a six-day SQLite candidate database containing 787 unique products and 3,713 observations.
- Verified SQLite integrity, foreign-key relationships and product/date uniqueness.
- Preserved all seven Day 6 evidence files in a local recovery backup.

## Data integrity

**Raw CSV SHA-256:** `f3ccc5487ab418c2ba02fa4457f4013b180cd5f86c6e3969928ee12d4116c1ac`

**Validation:** Passed  
**SQLite integrity:** OK  
**Foreign-key violations:** 0  
**Duplicate product/day observations:** 0

## Review status

Technical checks completed locally. Independent group-member verification and approval for publication of generated evidence are pending.

The existing production scraper and earlier daily raw datasets were not intentionally modified.