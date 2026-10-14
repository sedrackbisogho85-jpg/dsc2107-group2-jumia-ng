# Local data procedure

The contents of `raw/`, `cleaned/` and `checkpoints/` are intentionally ignored
by Git. The `.gitkeep` files preserve the folder structure only.

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

Use the approved private shared-data folder because datasets are not stored in
Git. Copy the accepted raw CSV, manifest, run log and checksum verification.
The receiving member must recompute the checksum before use. Do not share
credentials, `.env` files, Git metadata, virtual environments or private
browser/session data.

## Current verified data

Daily Run 1 is dated 13 October 2026. Its accepted raw checksum is documented
in `report/day1_quality_report.md`. No later daily run should be claimed until
it has genuinely occurred and passed the same checks.
