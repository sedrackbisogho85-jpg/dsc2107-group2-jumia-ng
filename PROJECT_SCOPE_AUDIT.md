# Project scope audit

**Audit date:** 14 October 2026
**Scope:** Independent Jumia Nigeria repository after accepted Daily Runs 1 and 2

This audit classifies the current project without deleting or moving files. The
final submission is not yet complete because five daily runs, the notebook PDF,
final report, presentation and contribution statements are still pending.

## A. Required final deliverables

| Current file or folder | Reason and final use |
|---|---|
| `README.md` | Main project explanation, setup, ethical rules and reproducible commands. It needs a final update after Run 7. |
| `requirements.txt` | Lists the packages needed to run the scraper, cleaner and notebook. |
| `reconnaissance/reconnaissance_note.pdf` | Required one-page reconnaissance deliverable. |
| `src/scraper.py` | Main sequential Jumia collector with pagination, delay, retries, request counting, checkpoints and block detection. |
| `src/cleaner.py` | Required reproducible cleaning pipeline that preserves missing values. |
| `src/database_loader.py` | Required normalized SQLite loader. It now accepts multiple cleaned daily files. |
| `src/config.py`, `src/utils.py`, `src/__init__.py` | Essential supporting files used by the main scripts. |
| `src/validator.py` | Required validation step for accepted raw files. |
| `data/raw/jumia_ng_products_2026-10-13.csv` and `data/raw/jumia_ng_products_2026-10-14.csv` | The first two immutable daily raw files. Five genuine daily files are still required. |
| `data/cleaned/jumia_ng_products_2026-10-13_cleaned.csv` and `data/cleaned/jumia_ng_products_2026-10-14_cleaned.csv` | Current reproducible cleaned inputs. A combined cleaned CSV should be produced after Run 7 for the final package. |
| `database/jumia_ng.sqlite` | Current normalized two-day database with 689 products, 3 categories and 1,239 observations. It must be refreshed after every accepted run. |
| `notebooks/jumia_analysis.ipynb` | Executed preliminary notebook. It currently uses two dates and contains seven interpreted charts. |
| `report/data_dictionary.md` | Required explanation of fields, types, sources and meanings. It can be included directly or incorporated into the final report. |
| `report/final_report.pdf` | Required final 5–8-page report; not yet created. |
| `notebooks/jumia_analysis.pdf` | Required final notebook export; not yet created. |
| `presentation/presentation.pptx` | Required presentation; not yet created. The folder currently contains only `.gitkeep`. |
| `contributions/contribution_statements.pdf` | Required combined contribution statements; not yet created. |

## B. Useful working evidence

| Current file or folder | Reason |
|---|---|
| `.gitignore` | Protects raw data, cleaned data, databases, logs, checkpoints, secrets and temporary files from accidental commits. |
| `CONTRIBUTING.md`, `GROUP_WORKFLOW.md`, `data/README.md` | Useful collaboration, daily-run and local-data rules. They do not need prominent placement in the final submission. |
| `contributions/contribution_log_template.md` | Working template for honest individual contribution records. |
| `tests/` and `tests/fixtures/listing_page.html` | Reproducible parser, cleaner and multi-day database tests. They support code quality even if the lecturer does not require them as headline deliverables. |
| `src/live_test.py` | Two-request preflight used to check robots rules and one category page before a real collection. |
| `src/reconnaissance.py` | Reproducible first-page reconnaissance and evidence collection. The PDF is the final reconnaissance deliverable. |
| `reconnaissance/reconnaissance_note.md` | Editable source for the required PDF. Keeping both formats is purposeful, not accidental duplication. |
| `reconnaissance/evidence/robots_*.txt` and `reconnaissance_http_*.json` | Evidence for access rules, status codes, timestamps and the temporary 503/recovery finding. |
| `reconnaissance/evidence/*.html` | Exact large page captures used to verify selectors. They are useful locally but should not be packaged in the final submission. |
| `data/raw/manifest_*.json` and `run_manifest.jsonl` | Daily/sample checksums, request counts, pages, completion status and errors. |
| `data/raw/validation_*.json` | Validation evidence for the sample and accepted runs. |
| `data/checkpoints/*.json` | Recovery state that prevents unnecessary repeat requests. |
| `logs/*.log` | Request, retry and run evidence. These are useful for checking results and incidents. |
| `data/raw/jumia_ng_sample_*.csv` and its sample manifest, validation, checkpoint and log | Evidence that the required sample stage passed before Daily Run 1. It is not one of the seven final daily files. |
| `data/cleaned/two_day_comparison_2026-10-14.json` | Preliminary overlap and change evidence for Runs 1 and 2. |
| `report/day1_quality_report.md` | Concise accepted Day 1 evidence. A Day 2/final report can absorb the useful results later. |
| `PROJECT_SCOPE_AUDIT.md` and `FINAL_SUBMISSION_PLAN.md` | Internal planning and quality-control documents, not assessed final outputs. |

## C. Exclude from final submission

| File or folder | Reason |
|---|---|
| `.git/` | Repository history and internal Git data are not submission content. |
| `.env`, virtual environments and credentials if created later | Private runtime configuration must never be submitted. None is currently tracked. |
| `src/__pycache__/`, `tests/__pycache__/`, `tmp/__pycache__/` and `*.pyc` | Generated Python cache files. |
| `.pytest_cache/` and `.ipynb_checkpoints/` if present later | Generated tool caches, not assignment evidence. |
| `tmp/` | Local notebook builders, validation helpers, PDF render images, two Edge browser profiles and cache files. It currently contains about 14 MB across roughly 485 files. |
| `database/jumia_ng_day2_build.sqlite` | Temporary validated build database. Its SHA-256 matches `database/jumia_ng.sqlite`, so it is a duplicate working copy. |
| `database/.gitkeep`, `logs/.gitkeep`, `notebooks/.gitkeep`, `presentation/.gitkeep`, `contributions/.gitkeep` and the data `.gitkeep` files | Repository folder placeholders. They have no value in the final packaged submission once real files exist. |
| External `BACKUPS/JUMIA_DAY1_2026-10-13` and `BACKUPS/JUMIA_DAY2_2026-10-14` folders | Recovery copies must remain outside the final submission to avoid duplicate datasets and databases. |
| Temporary PDF render PNG files and browser profiles | Visual-quality checking artifacts only. The accepted PDF is the deliverable. |

No file in this section was deleted during the audit.

## D. Possible duplication or excessive complexity

1. `database/jumia_ng_day2_build.sqlite` and `database/jumia_ng.sqlite` are exact duplicates after validation. The build copy is temporary and should be excluded when final packaging begins.
2. `validation_daily_2026-10-14.json` and `validation_daily_2026-10-14_detailed.json` overlap. The detailed file contains the full requested checks; a human should decide whether the smaller file still adds value.
3. The two reconnaissance HTTP JSON files and the two Computing HTML captures are not simple duplicates: one set records the HTTP 503 and the later set records recovery. They should remain working evidence but do not belong in the lean final package.
4. `.gitkeep` files remain in several folders that now contain real files. They are harmless repository scaffolding but unnecessary in the final submission archive.
5. `src/live_test.py`, `src/reconnaissance.py` and `src/scraper.py` share some request and block-checking ideas. Their roles are different and support the required testing sequence, so they should not be merged or removed merely to shorten the project.
6. Static inspection found no unused top-level functions. It found two low-risk unused imports: `Callable` in `src/cleaner.py` and `Path` in `src/reconnaissance.py`. These can be removed later in a focused cleanup, but they do not affect correctness.
7. The scraper is the largest module, but its rate limiting, bounded retries, checkpointing, output protection, logging and block detection all support explicit assignment requirements. These features are justified rather than overengineering.
8. No advanced machine learning, complex design patterns or unnecessary statistical methods are present. The notebook uses straightforward pandas, Matplotlib and Seaborn analysis suitable for Year 2 Semester 1.

## E. Files requiring human review

- Confirm whether the lecturer wants `tests/`, collaboration documents and the editable reconnaissance Markdown included in the final archive or only demonstrated during marking.
- Confirm whether `report/data_dictionary.md` should remain separate or become an appendix/section of the final report.
- Decide whether the final archive should include daily manifests and checksum reports. They are strong evidence but are not listed in the lean target structure.
- Replace all six member placeholders only with confirmed names, student numbers and truthful contribution records.
- Confirm the exact warm-up filenames in the separate warm-up repository before packaging. Do not merge the warm-up and Jumia Git histories.
- Review the final report, notebook PDF and presentation after Runs 3–7 because they do not yet exist.

## Student-scope and writing review

- The code is modular but uses familiar Year 2 Python: functions, classes, CSV processing, Requests, BeautifulSoup, SQLite and pandas.
- Comments and docstrings are generally short and explain purpose rather than obvious Python syntax.
- No wording claims guaranteed marks, perfection, expert status, enterprise/production-grade architecture or lecturer approval.
- No project document says that AI generated the assignment. The only AI-bot names found are quoted from the saved public `robots.txt` evidence.
- Reliability features should remain. Pagination, missing-value handling, retries, logging, rate limiting, request counting, block detection, validation, database constraints and tests directly support the rubric.
- Current notebook wording is cautious: it labels the two-day results preliminary and does not make seven-day conclusions.
