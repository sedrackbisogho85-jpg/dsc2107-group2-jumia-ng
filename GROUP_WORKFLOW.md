# Group workflow

## Roles for each daily collection

Use the table below for 13-19 October 2026. Enter names only after members
accept the responsibility.

| Date | Daily owner | Independent checker | Status |
|---|---|---|---|
| 13 October | `[member]` | `[member]` | Completed |
| 14 October | `[member]` | `[member]` | Completed |
| 15 October | `[member]` | `[member]` | Completed |
| 16 October | `[member]` | `[member]` | Not run |
| 17 October | `[member]` | `[member]` | Not run |
| 18 October | `[member]` | `[member]` | Not run |
| 19 October | `[member]` | `[member]` | Not run |

Current progress is 3 of 7 accepted runs. Daily Run 3 occurred from 21:26:16
to 21:29:55 on 15 October 2026 in `Africa/Nairobi`. It produced 639 records
(239 Phones & Tablets, 200 Computing and 200 Electronics) using 18 HTTP
attempts and 1 controlled retry. Its accepted raw SHA-256 is
`2e7102f2bd4dbf9d33e8b677640f1dbbc0a844029df88c321768efb68c91cfe5`.
The refreshed database contains 1,878 observations and 727 products.

There must be exactly one accepted scraper run per collection date. A rerun
must use a timestamped filename and the group must document which file is the
accepted observation.

## Daily owner checklist

1. Confirm the Africa/Nairobi date and current `robots.txt` rules.
2. Pull reviewed code and verify a clean task branch.
3. Supply the contact email at runtime; never write it into source code.
4. Run the scraper once with the approved delay and request limit.
5. Stop on CAPTCHA, denial, HTTP 403 or persistent HTTP 429.
6. Preserve the raw CSV, run log, checkpoint and manifest.
7. Record the raw SHA-256 and do not edit the raw file.
8. Give the checker the manifest, checksum and validation result.

## Independent checker checklist

1. Confirm the raw filename uses the genuine collection date.
2. Recalculate the SHA-256 and compare it with the manifest.
3. Check that all three categories are represented and at least 500 unique
   products were collected.
4. Check duplicates, required columns, timestamps, request count and errors.
5. Confirm missing values remain missing.
6. Mark the run accepted only after all checks pass.

## Version-controlled data procedure

After a run is accepted, commit its raw CSV, cleaned CSV, manifest, validation,
checkpoint, log and refreshed database together on the daily branch. A second
member must recompute the raw SHA-256 and compare it with the manifest before
the branch is merged. A fresh clone of `main` must therefore contain every
accepted run and the evidence needed to verify it.

Never commit `.env`, credentials, browser sessions, Git metadata, virtual
environments, generated caches or external backup folders.

## Branch and notebook coordination

Each task has one branch and one owner. Pull requests require another member's
review and passing tests before merge. Only one assigned member edits
`notebooks/jumia_analysis.ipynb` at a time; other members should review rendered
outputs or propose changes in issues/comments to avoid JSON merge conflicts.

## Honest reporting

Each member keeps an individual Git identity and completes a contribution log.
Commits, reviews, dataset checks and presentation work should be attributed to
the person who actually performed them. Every member must still understand and
be able to explain the complete pipeline during the question-and-answer session.
