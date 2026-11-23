"""
repository.py
--------------
InventoryRepository is the ONLY class in the project that imports sqlite3.
Every domain class (Medicine, Branch, StockEntry, Prescription, AllowList)
stays ignorant of how -- or whether -- it is persisted. This is the
separation-of-concerns boundary required by NFR4 in Milestone 1.

The one operation that must be atomic -- dispensing -- is implemented as
a single SQLite transaction: either every stock row is reduced AND the
prescription's status becomes 'dispensed', or (on any failure) nothing
in the database changes at all and the prescription stays pending.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from domain import (
    AllowList,
    Branch,
    ControlledMedicine,
    DomainError,
    InsufficientStockError,
    Medicine,
    OrdinaryMedicine,
    Prescription,
    PrescriptionLine,
    PrescriptionStatus,
    StockEntry,
)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class InventoryRepository:
    # Member 2 owns persistence; Member 3 owns inventory queries; Member 4 owns
    # atomic dispensing and rollback; Member 6 owns report queries.
    """SQLite-backed persistence for the whole domain model."""

    def __init__(self, db_path: str = "pharmacy.db"):
        # check_same_thread=False only matters once the Tkinter GUI is added
        # in Milestone 3 (Tkinter and sqlite3 can disagree about threads);
        # it is harmless here.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    # -- setup -----------------------------------------------------------
    def _init_schema(self) -> None:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            self._conn.executescript(f.read())
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- Medicine ----------------------------------------------------------
    def save_medicine(self, medicine: Medicine) -> None:
        try:
            self._conn.execute(
                "INSERT INTO medicines (code, name, unit_price, reorder_level, medicine_type) "
                "VALUES (?, ?, ?, ?, ?)",
                (medicine.code, medicine.name, medicine.unit_price,
                 medicine.reorder_level, medicine.medicine_type()),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise DomainError(f"Could not save medicine {medicine.code!r}: {exc}") from exc

    def get_medicine(self, code: str) -> Optional[Medicine]:
        row = self._conn.execute(
            "SELECT * FROM medicines WHERE code = ?", (code,)
        ).fetchone()
        return self._row_to_medicine(row) if row else None

    def list_medicines(self) -> list[Medicine]:
        rows = self._conn.execute("SELECT * FROM medicines ORDER BY code").fetchall()
        return [self._row_to_medicine(r) for r in rows]

    @staticmethod
    def _row_to_medicine(row: sqlite3.Row) -> Medicine:
        # This is where the medicine_type column decides which Python
        # subclass to reconstruct -- SQLite has no concept of classes,
        # so the repository bridges that gap on every read.
        cls = ControlledMedicine if row["medicine_type"] == "controlled" else OrdinaryMedicine
        return cls(row["code"], row["name"], row["unit_price"], row["reorder_level"])

    # -- Branch ------------------------------------------------------------
    def save_branch(self, branch: Branch) -> None:
        try:
            self._conn.execute(
                "INSERT INTO branches (code, name) VALUES (?, ?)",
                (branch.code, branch.name),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise DomainError(f"Could not save branch {branch.code!r}: {exc}") from exc

    def list_branches(self) -> list[Branch]:
        rows = self._conn.execute("SELECT * FROM branches ORDER BY code").fetchall()
        return [Branch(r["code"], r["name"]) for r in rows]

    # -- Stock -------------------------------------------------------------
    def get_stock(self, medicine_code: str, branch_code: str) -> StockEntry:
        row = self._conn.execute(
            "SELECT * FROM stock WHERE medicine_code = ? AND branch_code = ?",
            (medicine_code, branch_code),
        ).fetchone()
        quantity = row["quantity"] if row else 0
        return StockEntry(medicine_code, branch_code, quantity)

    def receive_stock(self, medicine_code: str, branch_code: str, amount: int) -> StockEntry:
        """FR3: stock arriving at a branch. Uses UPSERT so a first delivery
        of a medicine to a branch does not need a separate "create row" step."""
        entry = self.get_stock(medicine_code, branch_code)
        entry.receive(amount)  # domain-level validation (amount > 0)
        self._conn.execute(
            "INSERT INTO stock (medicine_code, branch_code, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(medicine_code, branch_code) DO UPDATE SET quantity = excluded.quantity",
            (medicine_code, branch_code, entry.quantity),
        )
        self._conn.commit()
        return entry

    def list_low_stock(self, branch_code: str) -> list[tuple[Medicine, int]]:
        """FR11: medicines at or below their reorder level at one branch."""
        rows = self._conn.execute(
            "SELECT m.*, s.quantity AS stock_quantity "
            "FROM medicines m JOIN stock s ON s.medicine_code = m.code "
            "WHERE s.branch_code = ? AND s.quantity <= m.reorder_level "
            "ORDER BY m.code",
            (branch_code,),
        ).fetchall()
        return [(self._row_to_medicine(r), r["stock_quantity"]) for r in rows]

    # -- AllowList -----------------------------------------------------------
    def load_allow_list(self) -> AllowList:
        rows = self._conn.execute("SELECT prescriber_code FROM allowed_prescribers").fetchall()
        return AllowList({r["prescriber_code"] for r in rows})

    def authorise_prescriber(self, prescriber_code: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO allowed_prescribers (prescriber_code) VALUES (?)",
            (prescriber_code,),
        )
        self._conn.commit()

    # -- Prescription --------------------------------------------------------
    def save_prescription(self, prescription: Prescription) -> Prescription:
        """FR4: persists a new pending prescription with all of its lines."""
        cur = self._conn.execute(
            "INSERT INTO prescriptions (patient_id, branch_code, prescriber_code, status) "
            "VALUES (?, ?, ?, ?)",
            (prescription.patient_id, prescription.branch_code,
             prescription.prescriber_code, prescription.status.value),
        )
        prescription.id = cur.lastrowid
        for line in prescription.lines:
            self._conn.execute(
                "INSERT INTO prescription_lines (prescription_id, medicine_code, quantity) "
                "VALUES (?, ?, ?)",
                (prescription.id, line.medicine_code, line.quantity),
            )
        self._conn.commit()
        return prescription

    def get_prescription(self, prescription_id: int) -> Optional[Prescription]:
        row = self._conn.execute(
            "SELECT * FROM prescriptions WHERE id = ?", (prescription_id,)
        ).fetchone()
        if row is None:
            return None

        prescription = Prescription(
            row["patient_id"], row["branch_code"], row["prescriber_code"], prescription_id
        )
        prescription._status = PrescriptionStatus(row["status"])  # reconstructing saved state

        line_rows = self._conn.execute(
            "SELECT * FROM prescription_lines WHERE prescription_id = ?", (prescription_id,)
        ).fetchall()
        for lr in line_rows:
            prescription._lines.append(
                PrescriptionLine(lr["medicine_code"], lr["quantity"])
            )
        return prescription

    def list_pending_prescriptions(self, branch_code: Optional[str] = None) -> list[Prescription]:
        if branch_code:
            rows = self._conn.execute(
                "SELECT id FROM prescriptions WHERE status = 'pending' AND branch_code = ? "
                "ORDER BY id", (branch_code,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id FROM prescriptions WHERE status = 'pending' ORDER BY id"
            ).fetchall()
        return [self.get_prescription(r["id"]) for r in rows]

    # -- the one operation that MUST be atomic (FR5, NFR3) --------------------
    def dispense(self, prescription_id: int) -> Prescription:
        """
        Dispenses a pending prescription.

        All of the following happen inside ONE SQLite transaction:
          1. every domain rule is re-checked (status, allow-list, stock),
          2. every line's stock is reduced,
          3. the prescription's status becomes 'dispensed'.

        If step 1 or 2 fails for ANY line, the transaction is rolled back
        in full: no stock row changes and the prescription is still
        'pending' afterwards. This is what "atomic dispensing" means for
        FR5 / NFR3.
        """
        prescription = self.get_prescription(prescription_id)
        if prescription is None:
            raise DomainError(f"No prescription with id {prescription_id}.")

        allow_list = self.load_allow_list()
        medicines = {m.code: m for m in self.list_medicines()}

        # Domain-level checks BEFORE touching the database at all: status,
        # non-empty, and the allow-list rule for controlled medicines.
        prescription.check_can_dispense(medicines, allow_list)

        cursor = self._conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE")

            for line in prescription.lines:
                row = cursor.execute(
                    "SELECT quantity FROM stock WHERE medicine_code = ? AND branch_code = ?",
                    (line.medicine_code, prescription.branch_code),
                ).fetchone()
                available = row["quantity"] if row else 0

                if line.quantity > available:
                    # Raising here causes the except block below to roll
                    # back everything already written in this transaction,
                    # including any earlier lines of the SAME prescription.
                    raise InsufficientStockError(
                        f"Insufficient stock of {line.medicine_code} at "
                        f"{prescription.branch_code}: need {line.quantity}, have {available}."
                    )

                cursor.execute(
                    "UPDATE stock SET quantity = quantity - ? "
                    "WHERE medicine_code = ? AND branch_code = ?",
                    (line.quantity, line.medicine_code, prescription.branch_code),
                )

            cursor.execute(
                "UPDATE prescriptions SET status = ? WHERE id = ?",
                (PrescriptionStatus.DISPENSED.value, prescription.id),
            )
            self._conn.commit()
            prescription.mark_dispensed()
            return prescription

        except Exception:
            self._conn.rollback()
            raise

    def cancel_prescription(self, prescription_id: int) -> Prescription:
        """FR9 (advanced feature)."""
        prescription = self.get_prescription(prescription_id)
        if prescription is None:
            raise DomainError(f"No prescription with id {prescription_id}.")
        prescription.cancel()  # raises InvalidPrescriptionStateError if not pending
        self._conn.execute(
            "UPDATE prescriptions SET status = ? WHERE id = ?",
            (PrescriptionStatus.CANCELLED.value, prescription_id),
        )
        self._conn.commit()
        return prescription

    def transfer_stock(self, medicine_code: str, from_branch: str, to_branch: str, amount: int) -> None:
        """FR10 (advanced feature). Atomic: both branches change together or neither does."""
        cursor = self._conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE")
            source = self.get_stock(medicine_code, from_branch)
            source.reduce(amount)  # raises InsufficientStockError if short
            dest = self.get_stock(medicine_code, to_branch)
            dest.receive(amount)

            cursor.execute(
                "INSERT INTO stock (medicine_code, branch_code, quantity) VALUES (?, ?, ?) "
                "ON CONFLICT(medicine_code, branch_code) DO UPDATE SET quantity = excluded.quantity",
                (medicine_code, from_branch, source.quantity),
            )
            cursor.execute(
                "INSERT INTO stock (medicine_code, branch_code, quantity) VALUES (?, ?, ?) "
                "ON CONFLICT(medicine_code, branch_code) DO UPDATE SET quantity = excluded.quantity",
                (medicine_code, to_branch, dest.quantity),
            )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
