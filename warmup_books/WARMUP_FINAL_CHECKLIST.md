# Warm-up Final Checklist

Final offline audit date: **17 October 2026**

## Completed

- [x] Collected 50 catalogue pages during the original warm-up.
- [x] Saved 1,000 URL-index rows with 1,000 unique detail URLs.
- [x] Saved 1,000 detailed book records without rerunning collection during finalisation.
- [x] Confirmed zero remaining indexed URLs.
- [x] Confirmed zero duplicate URLs in the index and detailed dataset.
- [x] Confirmed zero duplicate UPCs.
- [x] Confirmed zero missing required fields.
- [x] Confirmed zero invalid prices, ratings, review counts, or catalogue page values.
- [x] Confirmed all records have status `complete`.
- [x] Confirmed zero detail URLs outside the original index.
- [x] Ran `validate_books.py` offline with `.venv\Scripts\python.exe`; exit code 0.
- [x] Updated the README to match the implementation and final verified results.
- [x] Documented the historical robots.txt HTTP 404 observation without treating it as permission.
- [x] Added a minimal, pinned `requirements.txt` for the two direct dependencies.
- [x] Added `.gitignore` rules for environments, caches, datasets, backups, request logs, and temporary files.
- [x] Replaced hard-coded contact addresses with the optional `BOOKS_TO_SCRAPE_CONTACT_EMAIL` environment variable.
- [x] Added `--data-dir` support so offline validation can use private CSVs outside the repository.
- [x] Preserved the original collected CSV files unchanged.
- [x] Created ignored backup copies of the final datasets, validation report, and README.
- [x] Kept the warm-up separate from the Jumia Nigeria assignment.
- [x] Performed no network requests during finalisation.

## Remaining manual action

- [ ] Decide whether the course submission requires the full datasets to be delivered through a private channel; `.gitignore` intentionally excludes them from Git.

## Recommended commit contents

- Python source files (`*.py`)
- `README.md`
- `requirements.txt`
- `.gitignore`
- `WARMUP_FINAL_CHECKLIST.md`
- `validation_report.txt`

Do not commit `.venv/`, CSV datasets, `backups/`, daily request logs, private backup files, caches, or temporary files.
