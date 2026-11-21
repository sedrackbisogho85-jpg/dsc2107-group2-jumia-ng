"""
demo.py
-------
Runnable walk-through of Milestone 2, using only fictional data:

  * fictional branches: MAIN, ANNEX
  * fictional medicines: PARA500 (ordinary), MORPH10 (controlled)
  * fictional patient id: PT-FICT-001
  * fictional prescriber codes: DR-ALLOWED (on the allow-list), DR-OTHER (not)

Run it twice in a row to see the persistence requirement in action: the
second run finds the medicines/branches already there (and SQLite raises
a DomainError if you try to register the same code again), and the stock
levels from the first run are still on disk.

    python demo.py
"""

from domain import (
    Branch,
    ControlledMedicine,
    DomainError,
    InsufficientStockError,
    OrdinaryMedicine,
    Prescription,
    UnauthorisedPrescriberError,
)
from repository import InventoryRepository


def setup_fictional_data(repo: InventoryRepository) -> None:
    """FR1/FR2: register medicines and branches. Safe to call once only."""
    try:
        repo.save_branch(Branch("MAIN", "Main Campus Pharmacy"))
        repo.save_branch(Branch("ANNEX", "Annex Clinic Pharmacy"))
    except DomainError:
        print("Branches already registered (this is expected on a second run).")

    try:
        repo.save_medicine(OrdinaryMedicine("PARA500", "Paracetamol 500mg", unit_price=200.0, reorder_level=50))
        repo.save_medicine(ControlledMedicine("MORPH10", "Morphine 10mg", unit_price=1500.0, reorder_level=10))
    except DomainError:
        print("Medicines already registered (this is expected on a second run).")

    repo.authorise_prescriber("DR-ALLOWED")  # idempotent: INSERT OR IGNORE


def main() -> None:
    repo = InventoryRepository("pharmacy.db")
    setup_fictional_data(repo)

    print("\n--- FR3: receive stock ---")
    repo.receive_stock("PARA500", "MAIN", 100)
    repo.receive_stock("MORPH10", "MAIN", 20)
    print("PARA500 @ MAIN:", repo.get_stock("PARA500", "MAIN"))
    print("MORPH10 @ MAIN:", repo.get_stock("MORPH10", "MAIN"))

    print("\n--- FR4: create a multi-line prescription (fictional patient) ---")
    rx = Prescription(patient_id="PT-FICT-001", branch_code="MAIN", prescriber_code="DR-ALLOWED")
    rx.add_line("PARA500", 10)
    rx.add_line("MORPH10", 2)
    rx = repo.save_prescription(rx)
    print("Saved:", rx)

    print("\n--- FR5: successful dispense ---")
    dispensed = repo.dispense(rx.id)
    print("Dispensed:", dispensed)
    print("PARA500 @ MAIN after dispense:", repo.get_stock("PARA500", "MAIN"))
    print("MORPH10 @ MAIN after dispense:", repo.get_stock("MORPH10", "MAIN"))

    # ---------------------------------------------------------------
    # The three mandatory rejection cases
    # ---------------------------------------------------------------

    print("\n--- Rejection 1: oversell ---")
    rx_oversell = Prescription("PT-FICT-002", "MAIN", "DR-ALLOWED")
    rx_oversell.add_line("PARA500", 10_000)  # far more than is in stock
    rx_oversell = repo.save_prescription(rx_oversell)
    try:
        repo.dispense(rx_oversell.id)
    except InsufficientStockError as exc:
        print("Correctly rejected:", exc)
    reloaded = repo.get_prescription(rx_oversell.id)
    print("Prescription status is still:", reloaded.status.value)

    print("\n--- Rejection 2: controlled medicine, unauthorised prescriber ---")
    rx_unauth = Prescription("PT-FICT-003", "MAIN", "DR-OTHER")  # NOT on the allow-list
    rx_unauth.add_line("MORPH10", 1)
    rx_unauth = repo.save_prescription(rx_unauth)
    try:
        repo.dispense(rx_unauth.id)
    except UnauthorisedPrescriberError as exc:
        print("Correctly rejected:", exc)
    reloaded = repo.get_prescription(rx_unauth.id)
    print("Prescription status is still:", reloaded.status.value)

    print("\n--- Rejection 3: invalid price ---")
    try:
        OrdinaryMedicine("BADPRICE", "Should Fail", unit_price=-5.0, reorder_level=0)
    except ValueError as exc:
        print("Correctly rejected:", exc)

    print("\n--- FR9 (advanced): cancel a pending prescription ---")
    rx_cancel = Prescription("PT-FICT-004", "MAIN", "DR-ALLOWED")
    rx_cancel.add_line("PARA500", 5)
    rx_cancel = repo.save_prescription(rx_cancel)
    repo.cancel_prescription(rx_cancel.id)
    try:
        repo.dispense(rx_cancel.id)
    except DomainError as exc:
        print("Correctly rejected (cancelled prescription cannot be dispensed):", exc)

    print("\n--- FR10 (advanced): transfer stock between branches ---")
    repo.transfer_stock("PARA500", "MAIN", "ANNEX", 20)
    print("PARA500 @ MAIN:", repo.get_stock("PARA500", "MAIN"))
    print("PARA500 @ ANNEX:", repo.get_stock("PARA500", "ANNEX"))

    print("\n--- FR11: low stock report ---")
    repo.receive_stock("MORPH10", "ANNEX", 5)  # 5 <= reorder_level 10 -> low stock
    low = repo.list_low_stock("ANNEX")
    for medicine, qty in low:
        print(f"LOW STOCK at ANNEX: {medicine.name} ({medicine.code}) -> {qty} left, "
              f"reorder level {medicine.reorder_level}")

    repo.close()
    print("\nDone. Run this script again to confirm the data above persisted.")


if __name__ == "__main__":
    main()
