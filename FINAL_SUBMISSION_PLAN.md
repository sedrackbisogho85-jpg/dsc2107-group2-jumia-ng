# Final submission plan

This is a packaging plan only. Do not create the final submission folder until
Daily Run 7, the independent Day 6 check, final analysis, report, presentation
and signed contribution statements are complete and verified.

The Books to Scrape warm-up and Jumia Nigeria must remain separate Git
repositories. At packaging time, copy only the requested warm-up deliverables
into the submission folder. Do not merge repository histories or copy `.git`.

## Target structure

```text
DSC2107_Group2_Final_Submission/
├── README.md
├── warmup/
│   ├── books_scraper.py
│   └── books.csv
├── reconnaissance/
│   └── reconnaissance_note.pdf
├── src/
│   ├── scraper.py
│   ├── cleaner.py
│   ├── database_loader.py
│   ├── validator.py
│   ├── config.py
│   ├── utils.py
│   └── __init__.py
├── data/
│   ├── raw/
│   │   ├── jumia_ng_products_2026-10-13.csv
│   │   ├── jumia_ng_products_2026-10-14.csv
│   │   └── five genuine daily CSV files for 15-19 October
│   └── cleaned/
│       └── jumia_ng_products_2026-10-13_to_2026-10-19_cleaned.csv
├── database/
│   └── jumia_ng.sqlite
├── notebook/
│   ├── jumia_analysis.ipynb
│   └── jumia_analysis.pdf
├── report/
│   └── final_report.pdf
├── presentation/
│   └── presentation.pptx
└── contributions/
    └── contribution_statements.pdf
```

## Source-to-submission mapping

| Final item | Planned source | Current status |
|---|---|---|
| Root `README.md` | Jumia `README.md`, updated after final validation | Exists but needs final results and run instructions. |
| `warmup/books_scraper.py` and `warmup/books.csv` | Selected files from the separate warm-up repository | Human review required; do not copy yet. |
| Reconnaissance PDF | `reconnaissance/reconnaissance_note.pdf` | Complete and verified as one page. |
| Main source code | Essential files under `src/` | Working; multi-day database loader is tested. |
| Seven raw CSVs | Accepted immutable files under `data/raw/` | Runs 1–5 are accepted; Run 6 is locally validated and awaits its checker; Run 7 is pending. |
| Combined cleaned CSV | Rebuild from all seven accepted raw CSVs | Not created because the final date is still pending. |
| Final SQLite database | `database/jumia_ng.sqlite` rebuilt from all validated cleaned data | Current local database contains Runs 1–6: 787 products and 3,713 observations. |
| Executed notebook | `notebooks/jumia_analysis.ipynb` | Six-day version executes cleanly; the final refresh after Run 7 is pending. |
| Notebook PDF | Export from the final executed notebook | Not created. |
| Final report | Final 5–8-page report based on verified seven-day results | Not created. |
| Presentation | Final ten-minute presentation | Not created. |
| Contributions PDF | Six truthful half-page contribution statements | Template exists; final document is not created. |

## Files to keep out of the final folder

- `.git`, `.gitignore`, Git metadata and branch information
- `.env`, credentials and runtime contact details
- virtual environments and package caches
- `__pycache__`, `.pytest_cache` and `.ipynb_checkpoints`
- `tmp/`, browser profiles, render images and builder scripts
- external backup folders and duplicate databases
- sample data, checkpoints and routine logs unless the lecturer specifically
  requests supporting evidence
- old drafts and duplicate exports

Manifests, checksum reports, validations and tests should remain available in
the working repository. Add them to the final archive only if the lecturer asks
for evidence or if the final README explicitly references them.

## Work remaining before packaging

1. Have a different group member independently verify Day 6, then complete the genuine Day 7 run on 19 October.
2. Verify every raw checksum and preserve each accepted raw CSV unchanged.
3. Clean all seven raw files through the existing cleaner.
4. Produce one combined cleaned CSV without losing the daily timestamps or
   missing values.
5. Rebuild the database from all seven cleaned inputs and verify foreign keys,
   daily counts and product/date uniqueness.
6. Refresh and execute the notebook from a clean kernel. Replace preliminary
   placeholders with genuine seven-day results only.
7. Export and visually inspect the notebook PDF.
8. Write and verify the 5–8-page report and presentation.
9. Complete and combine the six truthful contribution statements.
10. Copy the two approved warm-up files from the separate repository without
    merging repositories.
11. Build the final folder once, using only the approved files in the target
    structure.

## Final quality checks

- Seven raw dates are present and each accepted run has at least 500 unique
  products across the three categories.
- Raw checksums still match their manifests and backups.
- The cleaned combined CSV and database cover the same seven dates.
- SQLite reports zero foreign-key violations and no duplicate product/date
  observations.
- All unit tests pass.
- The notebook runs from beginning to end with visible outputs and no errors.
- Notebook, report, reconnaissance and contribution PDFs open correctly and
  have readable page layouts.
- The presentation opens correctly and fits the ten-minute limit.
- No private contact value, credential, environment file, cache or duplicate
  backup is included.
- Every member can explain collection, raw protection, cleaning, database
  loading, validation, analysis, ethics and their recorded contribution.
