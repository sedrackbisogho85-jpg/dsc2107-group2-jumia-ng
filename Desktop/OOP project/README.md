# Multi-Branch Campus Pharmacy Inventory, Dispensing and Reporting System

A university OOP-course project for Uganda Christian University Health
Services (fictional client data only). A Tkinter desktop application backed
by SQLite, built around a pure Python domain model.

## Project structure

```
pharmacy_system/
├── medicine.py     # Member 1: Medicine public interface
├── prescription.py # Member 1: Prescription public interface
├── database.py     # Member 2: database/repository public interface
├── schema.sql      # Member 2: SQLite schema and constraints
├── init_db.py      # Member 2: database initialization
├── repositories.py # Member 2: persistence interface
├── inventory.py    # Member 3: branch stock interface
├── dispensing.py   # Member 4: atomic dispensing interface
├── app.py          # Member 5: Tkinter entry point
├── gui/            # Member 5: medicine, stock, prescription and report views
├── reports.py      # Member 6: low-stock reporting
├── seed.sql        # Member 6: simple SQL seed reference
├── seed_data.py    # Member 6: reproducible data loader
├── tests/          # Member 1-6 responsibility test modules
├── domain.py       # OOP domain model: Medicine hierarchy, Branch, StockEntry,
│                   # Prescription, AllowList. No sqlite3 or tkinter imports.
├── schema.sql      # CREATE TABLE statements, loaded automatically on first run
├── repository.py   # InventoryRepository: the only class that imports sqlite3
├── gui.py          # Member 5: Tkinter screens: Main Menu + 8 operation screens
├── demo.py         # Command-line walk-through of the MVP flow (no GUI needed)
└── README.md       # This file
```

## Dependencies

Python 3.10 or later, standard library only:

- `sqlite3` (bundled with Python)
- `tkinter` (bundled with Python on Windows/macOS installers; on Debian/Ubuntu
  Linux it is a separate OS package -- install it with
  `sudo apt-get install python3-tk` if `import tkinter` fails)

No `pip install` is required. There is no `requirements.txt` because nothing
outside the standard library is used, by design (see Milestone 1, NFR7).

## Database schema setup

No manual setup step is needed. `InventoryRepository.__init__()` runs
`schema.sql` automatically (`CREATE TABLE IF NOT EXISTS ...`) the first time
it opens a database file, so the six tables (`medicines`, `branches`,
`stock`, `prescriptions`, `prescription_lines`, `allowed_prescribers`) and
their `CHECK` constraints are created on first launch. If you want to
inspect the schema directly:

```
python3 -c "print(open('schema.sql').read())"
```

or open `pharmacy.db` in any SQLite browser once it has been created.

## Running the application

```
python gui.py
```

This opens the Main Menu. `pharmacy.db` is created in the current directory
on first run and reused on every subsequent run -- closing and reopening the
application does not lose any data (see Milestone 2 and Milestone 3, E6).

## Loading sample/test data

To start from a known, reproducible fictional data set (recommended before
any manual testing or demo):

```
python seed_data.py --reset
```

This deletes any existing `pharmacy.db` and loads two branches, four
medicines (two ordinary, two controlled), two allow-listed prescribers, and
initial stock -- including two items deliberately seeded at or below their
reorder level so the Low Stock Report has something to show immediately.
See the script's own docstring, or Milestone 3's testing doc, for the exact
values and why each one was chosen.

Running `python seed_data.py` again without `--reset` is safe: it reports
already-registered branches/medicines and skips them rather than failing,
while still topping up stock.

To see the same flow from the command line instead of the GUI (useful for
quickly re-confirming the domain logic on its own):

```
python demo.py
```

## Fictional data notice

Every patient identifier, prescriber code, branch, and medicine name in this
project is fictional, created for testing purposes only. No real patient,
prescriber, or proprietary UCU Health Services data is used anywhere in the
codebase, the test data, or the documentation (Milestone 1, NFR5).

## Further documentation

The submission documents are included in `docs/`:

- `Milestone 1 – Requirements & Object-Oriented Design.docx`
- `Milestone 3 – Testing Checklist & Defect Log.docx`
- `Milestone 4 – Live Demonstration & Oral Defence.docx`
- `Milestone 5 – Final Report.docx`

Repository:
https://github.com/sedrackbisogho85-jpg/dsc2107-group2-jumia-ng
