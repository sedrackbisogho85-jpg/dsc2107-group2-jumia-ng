"""
seed_data.py
------------
Member 6 responsibility: reproducible fictional seed data.
Loads a fixed set of fictional test data into pharmacy.db, for reproducible
manual testing in the Tkinter GUI (or anywhere else). Every patient,
prescriber and medicine below is fictional -- see Milestone 1, NFR5.

Usage:
    python seed_data.py            # seed into the existing/new pharmacy.db
    python seed_data.py --reset    # delete pharmacy.db first, then seed fresh

Re-running without --reset is safe: duplicate branches/medicines are
reported and skipped rather than crashing, so you can re-seed stock
levels on top of an existing database.
"""

from __future__ import annotations

import argparse
import os

from domain import Branch, ControlledMedicine, DomainError, OrdinaryMedicine
from repository import InventoryRepository

DB_PATH = "pharmacy.db"

# ---------------------------------------------------------------------------
# Fixed fictional data set. Keeping it as plain constants (rather than
# randomly generated) is what makes the test data "reproducible": every
# tester who runs this script ends up with exactly the same starting point.
# ---------------------------------------------------------------------------

BRANCHES = [
    ("MAIN", "Main Campus Pharmacy"),
    ("ANNEX", "Annex Clinic Pharmacy"),
]

MEDICINES = [
    # (code, name, unit_price, reorder_level, is_controlled)
    ("PARA500", "Paracetamol 500mg", 200.0, 50, False),
    ("AMOX250", "Amoxicillin 250mg", 450.0, 30, False),
    ("MORPH10", "Morphine 10mg", 1500.0, 10, True),
    ("DIAZE5", "Diazepam 5mg", 900.0, 15, True),
]

# Fictional prescriber codes. Only DR-ALLOWED is on the allow-list, so
# DR-OTHER is deliberately left off it to exercise the rejection case.
AUTHORISED_PRESCRIBERS = ["DR-ALLOWED", "DR-SECOND"]
UNAUTHORISED_PRESCRIBER_FOR_TESTING = "DR-OTHER"  # intentionally NOT added

# (medicine_code, branch_code, quantity)
INITIAL_STOCK = [
    ("PARA500", "MAIN", 100),
    ("PARA500", "ANNEX", 40),
    ("AMOX250", "MAIN", 60),
    ("MORPH10", "MAIN", 20),
    ("MORPH10", "ANNEX", 5),   # at/below its reorder level of 10 -> low stock on purpose
    ("DIAZE5", "MAIN", 12),    # at/below its reorder level of 15 -> low stock on purpose
]

# Fictional patient identifiers, for use when creating test prescriptions
# by hand in the GUI. Not written to the database by this script.
FICTIONAL_PATIENT_IDS = ["PT-FICT-001", "PT-FICT-002", "PT-FICT-003"]


def seed(repo: InventoryRepository) -> None:
    print("Registering branches...")
    for code, name in BRANCHES:
        try:
            repo.save_branch(Branch(code, name))
            print(f"  + {code}: {name}")
        except DomainError:
            print(f"  = {code} already exists, skipped")

    print("Registering medicines...")
    for code, name, price, reorder, controlled in MEDICINES:
        cls = ControlledMedicine if controlled else OrdinaryMedicine
        try:
            repo.save_medicine(cls(code, name, price, reorder))
            print(f"  + {code}: {name} ({'controlled' if controlled else 'ordinary'})")
        except DomainError:
            print(f"  = {code} already exists, skipped")

    print("Authorising prescribers...")
    for code in AUTHORISED_PRESCRIBERS:
        repo.authorise_prescriber(code)
        print(f"  + {code} authorised")
    print(f"  (left off the allow-list on purpose, for testing: "
          f"{UNAUTHORISED_PRESCRIBER_FOR_TESTING})")

    print("Receiving initial stock...")
    for medicine_code, branch_code, quantity in INITIAL_STOCK:
        entry = repo.receive_stock(medicine_code, branch_code, quantity)
        print(f"  + {quantity} x {medicine_code} @ {branch_code} "
              f"(now {entry.quantity})")

    print("\nFictional patient IDs you can use when creating test "
          "prescriptions by hand:")
    for pid in FICTIONAL_PATIENT_IDS:
        print(f"  - {pid}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true",
                         help="delete the existing pharmacy.db before seeding")
    args = parser.parse_args()

    if args.reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}.\n")

    repo = InventoryRepository(DB_PATH)
    seed(repo)
    repo.close()
    print(f"\nDone. {DB_PATH} is ready for manual testing in gui.py.")


if __name__ == "__main__":
    main()
