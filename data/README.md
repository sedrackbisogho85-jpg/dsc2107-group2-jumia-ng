# Version-controlled data procedure

Accepted contents of `raw/`, `cleaned/` and `checkpoints/` are tracked by Git so
every clone contains the complete evidence for all accepted collection dates.
The `.gitkeep` files preserve the folder structure before the first run.

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

Commit each accepted raw CSV together with its manifest, validation,
checkpoint, run log, cleaned CSV and refreshed database on the daily branch.
The reviewing member must recompute the raw checksum before merging. Never
commit credentials, `.env` files, Git metadata, virtual environments, generated
caches or private browser/session data.

## Current verified data

Three of seven planned daily runs are now accepted:

| Run | Nairobi collection time | Rows | Category counts | HTTP attempts / retries | Raw SHA-256 |
|---|---|---:|---|---:|---|
| 1 | 13 October 2026, 19:22:00-19:26:44 | 639 | Phones & Tablets 239; Computing 200; Electronics 200 | 19 / 2 | `6d33a6b278c7ebc371d233624f94d46dd2222cdc0b71cd2537dc62a48bd52b48` |
| 2 | 14 October 2026, 21:41:34-21:50:28 | 600 | 200 in each category | 22 / 6 | `d0d48535403804ebce0bb63fad837c0c70a52954f47753c2c00c60bd17f2d091` |
| 3 | 15 October 2026, 21:26:16-21:29:55 | 639 | Phones & Tablets 239; Computing 200; Electronics 200 | 18 / 1 | `2e7102f2bd4dbf9d33e8b677640f1dbbc0a844029df88c321768efb68c91cfe5` |

The refreshed database contains 1,878 observations and 727 unique products.
Daily Run 3 passed validation with no duplicate IDs, malformed cards, final
errors or access-denial signals. Missing values remain missing rather than
being changed to zero.
