# Generated data procedure

Accepted evidence may be explicitly published after group approval, but new
contents of `raw/`, `cleaned/`, `checkpoints/`, `logs/` and the SQLite database
are protected by `.gitignore` by default. Keep new run artifacts local and in
the approved external backup until a reviewed synchronization task approves
their exact paths. The `.gitkeep` files preserve empty folder structure.

## Raw data

- Keep one accepted raw CSV per genuine collection date.
- Never edit, format, rename or overwrite an accepted raw CSV.
- Calculate SHA-256 immediately after collection and compare it with the run
  manifest before analysis.
- If a same-day rerun is necessary, use a timestamped filename and document
  which run was accepted.
- Do not fabricate, copy forward or backdate observations.

## Cleaned data and checkpoints

Cleaned CSV files are reproducible outputs created by `src/cleaner.py`; they
must never replace raw files. Checkpoints belong in `data/checkpoints/`, not in
`data/raw/`, and may be used to resume without requesting completed pages.

## Sharing with the group

Give the checker the accepted raw CSV, manifest, validation, checkpoint, run
log, cleaned CSV and refreshed database through an approved secure backup. The
reviewing member must recompute the raw checksum before accepting the run.
During an approved evidence-publication task, stage only the verified artifact
paths explicitly; never use a broad add command. Never commit credentials,
`.env` files, Git metadata, virtual environments, generated caches or private
browser/session data.

## Current verified data

Days 1-5 are independently accepted. Runs 6-7 are complete and locally
validated, but their independent checkers are still pending:

| Run | Nairobi collection time | Rows | Category counts | HTTP attempts / retries | Raw SHA-256 |
|---|---|---:|---|---:|---|
| 1 | 13 October 2026, 19:22:00-19:26:44 | 639 | Phones & Tablets 239; Computing 200; Electronics 200 | 19 / 2 | `6d33a6b278c7ebc371d233624f94d46dd2222cdc0b71cd2537dc62a48bd52b48` |
| 2 | 14 October 2026, 21:41:34-21:50:28 | 600 | 200 in each category | 22 / 6 | `d0d48535403804ebce0bb63fad837c0c70a52954f47753c2c00c60bd17f2d091` |
| 3 | 15 October 2026, 21:26:16-21:29:55 | 639 | Phones & Tablets 239; Computing 200; Electronics 200 | 18 / 1 | `2e7102f2bd4dbf9d33e8b677640f1dbbc0a844029df88c321768efb68c91cfe5` |
| 4 | 16 October 2026, 21:26:31-21:28:32 | 600 | 200 in each category | 16 / 0 | `ac3a696a396560e9c123cb710e600fffa8ca365ea83486074316d8cf59aafacd` |
| 5 | 17 October 2026, 22:39:32-22:41:38 | 635 | Phones & Tablets 238; Computing 198; Electronics 199 | 17 / 0 | `182834f7179f00460c485546a62571536c2a324087de830b4082bbba0c881268` |
| 6 | 18 October 2026, 21:39:00-21:41:04 | 600 | 200 in each category | 16 / 0 | `f26eb2081b484b260eb1a8b346f7db36405dd45e177ce452c1afe256d3275c75` |
| 7 | 19 October 2026, 18:23:23-18:27:57, checkpoint resume at 18:25:54 | 600 | 200 in each category | 20 / 2 retries plus 1 resume | `5f3f6fdbfeb81841457cf6a33e944865c7419f4cdb9e5e5e251c7a3a6162df74` |

The refreshed local database contains 4,313 observations and 799 unique
products across 13-19 October. All seven completed daily raw files pass
automated validation with no duplicate IDs or invalid timestamps. Day 7's
initial interrupted attempt, incomplete CSV, manifest, checkpoint and log are
preserved as recovery evidence and are not the accepted candidate. The
completed Day 7 file has no malformed cards or final access-denial signal. Its
26 missing old-price/discount values and 3 missing rating/review values remain
missing rather than being changed to zero.
