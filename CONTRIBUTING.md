# Contributing to the Group 2 Jumia Project

This is assessed group work. Contributions must be technically correct,
reviewable and honestly attributed.

## Six-member team placeholders

1. Member 1: `[name and student number]`
2. Member 2: `[name and student number]`
3. Member 3: `[name and student number]`
4. Member 4: `[name and student number]`
5. Member 5: `[name and student number]`
6. Member 6: `[name and student number]`

Replace the placeholders only with confirmed group details.

## Local setup

Each member must use an independent clone and configure their own Git identity:

```powershell
git config user.name "Your Name"
git config user.email "your-own-address@example.com"
```

Do not share one working folder or pretend that another member's commit is your
own. Every member should understand the scraper, raw-file protection, cleaning,
database, validation, notebook and reporting pipeline even when they are not
the primary owner of that task.

## Branch and review rules

- Never work directly on `main`.
- Create one short-lived branch per task, such as `analysis/run1-notebook`.
- Pull the latest reviewed `main` before beginning.
- Run relevant tests and checks before opening a pull request.
- A different member must review the pull request before it is merged.
- Address review comments with additional commits; do not hide authorship.
- Keep commits focused and use messages that describe the completed outcome.
- Do not commit raw or cleaned data, logs, databases, checkpoints, backups,
  secrets, `.env` files or virtual environments.

## Code and evidence quality

- Preserve missing values instead of inventing zeroes.
- Do not fabricate or backdate observations.
- Run `python -m unittest discover -s tests -v` after relevant code changes.
- Verify raw checksums before and after analysis work.
- Require code review for scraper, cleaner, validator and database changes.
- Assign one notebook owner at a time to reduce `.ipynb` merge conflicts.
- Review executed notebook outputs, not code cells alone.
- Record the real work performed in the contribution log.
