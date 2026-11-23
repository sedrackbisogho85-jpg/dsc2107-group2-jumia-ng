-- schema.sql
-- Member 2 responsibility: SQLite tables, foreign keys and constraints.
-- Full schema for the Campus Pharmacy Inventory, Dispensing and Reporting
-- System. Every invariant from Milestone 1, section 7 is enforced twice:
-- once here (CHECK constraints), and once in domain.py (property setters
-- and method guards). Foreign keys are declared and must be switched on
-- per-connection with "PRAGMA foreign_keys = ON" (done in repository.py).

CREATE TABLE IF NOT EXISTS medicines (
    code            TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    unit_price      REAL NOT NULL CHECK (unit_price > 0),
    reorder_level   INTEGER NOT NULL CHECK (reorder_level >= 0),
    medicine_type   TEXT NOT NULL CHECK (medicine_type IN ('ordinary', 'controlled'))
);

CREATE TABLE IF NOT EXISTS branches (
    code  TEXT PRIMARY KEY,
    name  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stock (
    medicine_code  TEXT NOT NULL REFERENCES medicines(code),
    branch_code    TEXT NOT NULL REFERENCES branches(code),
    quantity       INTEGER NOT NULL CHECK (quantity >= 0),
    PRIMARY KEY (medicine_code, branch_code)
);

CREATE TABLE IF NOT EXISTS prescriptions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id        TEXT NOT NULL,
    branch_code       TEXT NOT NULL REFERENCES branches(code),
    prescriber_code   TEXT NOT NULL,
    status            TEXT NOT NULL CHECK (status IN ('pending', 'dispensed', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS prescription_lines (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id     INTEGER NOT NULL REFERENCES prescriptions(id),
    medicine_code       TEXT NOT NULL REFERENCES medicines(code),
    quantity            INTEGER NOT NULL CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS allowed_prescribers (
    prescriber_code  TEXT PRIMARY KEY
);
