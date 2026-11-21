"""
test_app.py
-----------
Comprehensive test suite for the Campus Pharmacy Inventory, Dispensing and
Reporting System. Covers the domain model (unit tests) and the repository
layer (integration tests against an in-memory SQLite database).

Run with:
    python -m unittest test_app -v
"""

from __future__ import annotations

import os
import tempfile
import unittest

from domain import (
    AllowList,
    Branch,
    ControlledMedicine,
    DomainError,
    EmptyPrescriptionError,
    InsufficientStockError,
    InvalidPrescriptionStateError,
    Medicine,
    OrdinaryMedicine,
    Prescription,
    PrescriptionLine,
    PrescriptionStatus,
    StockEntry,
    UnauthorisedPrescriberError,
)
from repository import InventoryRepository


# ===========================================================================
# Domain-layer unit tests (no database)
# ===========================================================================


class TestOrdinaryMedicine(unittest.TestCase):
    """Tests for OrdinaryMedicine creation and validation."""

    def test_create_valid(self):
        m = OrdinaryMedicine("CODE1", "Aspirin 100mg", 150.0, 20)
        self.assertEqual(m.code, "CODE1")
        self.assertEqual(m.name, "Aspirin 100mg")
        self.assertEqual(m.unit_price, 150.0)
        self.assertEqual(m.reorder_level, 20)
        self.assertEqual(m.medicine_type(), "ordinary")

    def test_empty_code_rejected(self):
        with self.assertRaises(ValueError):
            OrdinaryMedicine("", "Aspirin", 100.0, 10)

    def test_empty_name_rejected(self):
        with self.assertRaises(ValueError):
            OrdinaryMedicine("X", "", 100.0, 10)

    def test_negative_price_rejected(self):
        with self.assertRaises(ValueError):
            OrdinaryMedicine("X", "Drug", -1.0, 10)

    def test_zero_price_rejected(self):
        with self.assertRaises(ValueError):
            OrdinaryMedicine("X", "Drug", 0.0, 10)

    def test_negative_reorder_level_rejected(self):
        with self.assertRaises(ValueError):
            OrdinaryMedicine("X", "Drug", 10.0, -1)

    def test_zero_reorder_level_accepted(self):
        m = OrdinaryMedicine("X", "Drug", 10.0, 0)
        self.assertEqual(m.reorder_level, 0)

    def test_can_dispense_always_true(self):
        m = OrdinaryMedicine("X", "Drug", 10.0, 5)
        allow_list = AllowList()
        self.assertTrue(m.can_dispense("ANY_PRESCRIBER", allow_list))

    def test_is_low_stock(self):
        m = OrdinaryMedicine("X", "Drug", 10.0, 50)
        self.assertTrue(m.is_low_stock(50))   # equal to reorder level
        self.assertTrue(m.is_low_stock(10))   # below
        self.assertFalse(m.is_low_stock(51))  # above

    def test_price_update(self):
        m = OrdinaryMedicine("X", "Drug", 10.0, 5)
        m.unit_price = 25.0
        self.assertEqual(m.unit_price, 25.0)

    def test_price_update_to_zero_rejected(self):
        m = OrdinaryMedicine("X", "Drug", 10.0, 5)
        with self.assertRaises(ValueError):
            m.unit_price = 0


class TestControlledMedicine(unittest.TestCase):
    """Tests for ControlledMedicine and allow-list enforcement."""

    def test_medicine_type(self):
        m = ControlledMedicine("CTRL", "Morphine", 1500.0, 10)
        self.assertEqual(m.medicine_type(), "controlled")

    def test_can_dispense_authorised(self):
        m = ControlledMedicine("CTRL", "Morphine", 1500.0, 10)
        allow_list = AllowList({"DR-OK"})
        self.assertTrue(m.can_dispense("DR-OK", allow_list))

    def test_cannot_dispense_unauthorised(self):
        m = ControlledMedicine("CTRL", "Morphine", 1500.0, 10)
        allow_list = AllowList({"DR-OK"})
        self.assertFalse(m.can_dispense("DR-BAD", allow_list))

    def test_cannot_dispense_empty_allow_list(self):
        m = ControlledMedicine("CTRL", "Morphine", 1500.0, 10)
        allow_list = AllowList()
        self.assertFalse(m.can_dispense("ANYONE", allow_list))


class TestBranch(unittest.TestCase):
    """Tests for the Branch frozen dataclass."""

    def test_create_valid(self):
        b = Branch("MAIN", "Main Pharmacy")
        self.assertEqual(b.code, "MAIN")
        self.assertEqual(b.name, "Main Pharmacy")

    def test_empty_code_rejected(self):
        with self.assertRaises(ValueError):
            Branch("", "Main")

    def test_empty_name_rejected(self):
        with self.assertRaises(ValueError):
            Branch("MAIN", "")

    def test_immutable(self):
        b = Branch("MAIN", "Main Pharmacy")
        with self.assertRaises(AttributeError):
            b.code = "NEW"


class TestStockEntry(unittest.TestCase):
    """Tests for StockEntry receive/reduce operations."""

    def test_create_default_zero(self):
        s = StockEntry("MED1", "BR1")
        self.assertEqual(s.quantity, 0)

    def test_create_with_quantity(self):
        s = StockEntry("MED1", "BR1", 50)
        self.assertEqual(s.quantity, 50)

    def test_negative_initial_rejected(self):
        with self.assertRaises(ValueError):
            StockEntry("MED1", "BR1", -1)

    def test_receive(self):
        s = StockEntry("MED1", "BR1", 10)
        s.receive(5)
        self.assertEqual(s.quantity, 15)

    def test_receive_zero_rejected(self):
        s = StockEntry("MED1", "BR1", 10)
        with self.assertRaises(ValueError):
            s.receive(0)

    def test_receive_negative_rejected(self):
        s = StockEntry("MED1", "BR1", 10)
        with self.assertRaises(ValueError):
            s.receive(-3)

    def test_reduce(self):
        s = StockEntry("MED1", "BR1", 10)
        s.reduce(3)
        self.assertEqual(s.quantity, 7)

    def test_reduce_to_zero(self):
        s = StockEntry("MED1", "BR1", 10)
        s.reduce(10)
        self.assertEqual(s.quantity, 0)

    def test_reduce_below_zero_rejected(self):
        s = StockEntry("MED1", "BR1", 10)
        with self.assertRaises(InsufficientStockError):
            s.reduce(11)

    def test_reduce_zero_rejected(self):
        s = StockEntry("MED1", "BR1", 10)
        with self.assertRaises(ValueError):
            s.reduce(0)


class TestAllowList(unittest.TestCase):
    """Tests for the AllowList wrapper."""

    def test_empty(self):
        al = AllowList()
        self.assertFalse(al.is_authorised("DR-X"))

    def test_add_and_check(self):
        al = AllowList()
        al.add("DR-X")
        self.assertTrue(al.is_authorised("DR-X"))

    def test_remove(self):
        al = AllowList({"DR-X"})
        al.remove("DR-X")
        self.assertFalse(al.is_authorised("DR-X"))

    def test_remove_nonexistent_safe(self):
        al = AllowList()
        al.remove("GHOST")  # should not raise

    def test_add_empty_rejected(self):
        al = AllowList()
        with self.assertRaises(ValueError):
            al.add("")

    def test_iteration_sorted(self):
        al = AllowList({"C", "A", "B"})
        self.assertEqual(list(al), ["A", "B", "C"])


class TestPrescriptionLine(unittest.TestCase):
    """Tests for the PrescriptionLine dataclass."""

    def test_create_valid(self):
        pl = PrescriptionLine("MED1", 5)
        self.assertEqual(pl.medicine_code, "MED1")
        self.assertEqual(pl.quantity, 5)

    def test_zero_quantity_rejected(self):
        with self.assertRaises(ValueError):
            PrescriptionLine("MED1", 0)

    def test_negative_quantity_rejected(self):
        with self.assertRaises(ValueError):
            PrescriptionLine("MED1", -1)


class TestPrescription(unittest.TestCase):
    """Tests for Prescription state machine and domain checks."""

    def _make_rx(self):
        return Prescription("PT-001", "MAIN", "DR-ALLOWED")

    def test_create_pending(self):
        rx = self._make_rx()
        self.assertEqual(rx.status, PrescriptionStatus.PENDING)
        self.assertEqual(rx.lines, ())

    def test_add_line(self):
        rx = self._make_rx()
        rx.add_line("MED1", 3)
        self.assertEqual(len(rx.lines), 1)
        self.assertEqual(rx.lines[0].medicine_code, "MED1")

    def test_empty_patient_rejected(self):
        with self.assertRaises(ValueError):
            Prescription("", "MAIN", "DR-X")

    def test_lines_read_only(self):
        rx = self._make_rx()
        rx.add_line("MED1", 3)
        lines = rx.lines
        self.assertIsInstance(lines, tuple)  # cannot append to it

    def test_id_set_once(self):
        rx = self._make_rx()
        rx.id = 42
        self.assertEqual(rx.id, 42)
        with self.assertRaises(InvalidPrescriptionStateError):
            rx.id = 99

    # -- status transitions ---

    def test_dispense_success(self):
        rx = self._make_rx()
        rx.add_line("MED1", 2)
        meds = {"MED1": OrdinaryMedicine("MED1", "Drug", 10.0, 5)}
        rx.check_can_dispense(meds, AllowList())
        rx.mark_dispensed()
        self.assertEqual(rx.status, PrescriptionStatus.DISPENSED)

    def test_dispense_empty_prescription_rejected(self):
        rx = self._make_rx()
        meds: dict[str, Medicine] = {}
        with self.assertRaises(EmptyPrescriptionError):
            rx.check_can_dispense(meds, AllowList())

    def test_dispense_unauthorised_prescriber_rejected(self):
        rx = Prescription("PT-001", "MAIN", "DR-BAD")
        rx.add_line("CTRL1", 1)
        meds = {"CTRL1": ControlledMedicine("CTRL1", "Morphine", 1500.0, 10)}
        with self.assertRaises(UnauthorisedPrescriberError):
            rx.check_can_dispense(meds, AllowList())

    def test_dispense_authorised_prescriber_allowed(self):
        rx = Prescription("PT-001", "MAIN", "DR-OK")
        rx.add_line("CTRL1", 1)
        meds = {"CTRL1": ControlledMedicine("CTRL1", "Morphine", 1500.0, 10)}
        al = AllowList({"DR-OK"})
        rx.check_can_dispense(meds, al)  # should not raise

    def test_cancel(self):
        rx = self._make_rx()
        rx.cancel()
        self.assertEqual(rx.status, PrescriptionStatus.CANCELLED)

    def test_cancel_already_dispensed_rejected(self):
        rx = self._make_rx()
        rx.add_line("MED1", 1)
        rx.mark_dispensed()
        with self.assertRaises(InvalidPrescriptionStateError):
            rx.cancel()

    def test_dispense_already_cancelled_rejected(self):
        rx = self._make_rx()
        rx.cancel()
        with self.assertRaises(InvalidPrescriptionStateError):
            rx.mark_dispensed()

    def test_add_line_after_dispense_rejected(self):
        rx = self._make_rx()
        rx.add_line("MED1", 1)
        rx.mark_dispensed()
        with self.assertRaises(InvalidPrescriptionStateError):
            rx.add_line("MED2", 1)

    def test_add_line_after_cancel_rejected(self):
        rx = self._make_rx()
        rx.cancel()
        with self.assertRaises(InvalidPrescriptionStateError):
            rx.add_line("MED2", 1)


# ===========================================================================
# Repository-layer integration tests (in-memory SQLite)
# ===========================================================================


class RepositoryTestCase(unittest.TestCase):
    """Base class: creates a fresh in-memory database for each test."""

    def setUp(self):
        # Use a temporary file so SQLite transactions behave realistically
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.repo = InventoryRepository(self._tmp.name)

    def tearDown(self):
        self.repo.close()
        os.unlink(self._tmp.name)


class TestMedicineRepository(RepositoryTestCase):
    """Saving and loading medicines through the repository."""

    def test_save_and_retrieve(self):
        m = OrdinaryMedicine("PARA500", "Paracetamol 500mg", 200.0, 50)
        self.repo.save_medicine(m)
        loaded = self.repo.get_medicine("PARA500")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.code, "PARA500")
        self.assertEqual(loaded.name, "Paracetamol 500mg")
        self.assertIsInstance(loaded, OrdinaryMedicine)

    def test_save_controlled_and_retrieve(self):
        m = ControlledMedicine("MORPH10", "Morphine 10mg", 1500.0, 10)
        self.repo.save_medicine(m)
        loaded = self.repo.get_medicine("MORPH10")
        self.assertIsInstance(loaded, ControlledMedicine)
        self.assertEqual(loaded.medicine_type(), "controlled")

    def test_duplicate_code_rejected(self):
        self.repo.save_medicine(OrdinaryMedicine("X", "Drug A", 10.0, 5))
        with self.assertRaises(DomainError):
            self.repo.save_medicine(OrdinaryMedicine("X", "Drug B", 20.0, 10))

    def test_list_medicines(self):
        self.repo.save_medicine(OrdinaryMedicine("B", "Beta", 10.0, 1))
        self.repo.save_medicine(OrdinaryMedicine("A", "Alpha", 20.0, 2))
        meds = self.repo.list_medicines()
        self.assertEqual(len(meds), 2)
        self.assertEqual(meds[0].code, "A")  # sorted by code

    def test_get_nonexistent_returns_none(self):
        self.assertIsNone(self.repo.get_medicine("GHOST"))


class TestBranchRepository(RepositoryTestCase):
    """Saving and loading branches through the repository."""

    def test_save_and_list(self):
        self.repo.save_branch(Branch("MAIN", "Main Campus"))
        branches = self.repo.list_branches()
        self.assertEqual(len(branches), 1)
        self.assertEqual(branches[0].code, "MAIN")

    def test_duplicate_branch_rejected(self):
        self.repo.save_branch(Branch("X", "Branch X"))
        with self.assertRaises(DomainError):
            self.repo.save_branch(Branch("X", "Branch X Duplicate"))


class TestStockRepository(RepositoryTestCase):
    """Receiving stock and checking stock levels through the repository."""

    def setUp(self):
        super().setUp()
        self.repo.save_medicine(OrdinaryMedicine("MED1", "Drug 1", 100.0, 20))
        self.repo.save_branch(Branch("BR1", "Branch One"))
        self.repo.save_branch(Branch("BR2", "Branch Two"))

    def test_receive_new(self):
        entry = self.repo.receive_stock("MED1", "BR1", 50)
        self.assertEqual(entry.quantity, 50)

    def test_receive_accumulates(self):
        self.repo.receive_stock("MED1", "BR1", 50)
        entry = self.repo.receive_stock("MED1", "BR1", 30)
        self.assertEqual(entry.quantity, 80)

    def test_get_stock_no_rows(self):
        entry = self.repo.get_stock("MED1", "BR1")
        self.assertEqual(entry.quantity, 0)

    def test_low_stock_report(self):
        m2 = OrdinaryMedicine("MED2", "Drug 2", 50.0, 100)
        self.repo.save_medicine(m2)
        self.repo.receive_stock("MED1", "BR1", 50)   # 50 > reorder 20 => not low
        self.repo.receive_stock("MED2", "BR1", 10)   # 10 <= reorder 100 => low
        low = self.repo.list_low_stock("BR1")
        self.assertEqual(len(low), 1)
        self.assertEqual(low[0][0].code, "MED2")
        self.assertEqual(low[0][1], 10)


class TestPrescriptionRepository(RepositoryTestCase):
    """Creating, dispensing, and cancelling prescriptions through the repository."""

    def setUp(self):
        super().setUp()
        self.repo.save_medicine(OrdinaryMedicine("PARA", "Paracetamol", 200.0, 50))
        self.repo.save_medicine(ControlledMedicine("MORPH", "Morphine", 1500.0, 10))
        self.repo.save_branch(Branch("MAIN", "Main Pharmacy"))
        self.repo.receive_stock("PARA", "MAIN", 100)
        self.repo.receive_stock("MORPH", "MAIN", 20)
        self.repo.authorise_prescriber("DR-OK")

    def _make_rx(self, med="PARA", qty=5, prescriber="DR-OK"):
        rx = Prescription("PT-001", "MAIN", prescriber)
        rx.add_line(med, qty)
        return self.repo.save_prescription(rx)

    # -- save and retrieve ---

    def test_save_and_retrieve(self):
        rx = self._make_rx()
        self.assertIsNotNone(rx.id)
        loaded = self.repo.get_prescription(rx.id)
        self.assertEqual(loaded.patient_id, "PT-001")
        self.assertEqual(loaded.status, PrescriptionStatus.PENDING)
        self.assertEqual(len(loaded.lines), 1)

    def test_get_nonexistent_returns_none(self):
        self.assertIsNone(self.repo.get_prescription(9999))

    def test_list_pending(self):
        self._make_rx()
        self._make_rx()
        pending = self.repo.list_pending_prescriptions()
        self.assertEqual(len(pending), 2)

    def test_list_pending_filtered_by_branch(self):
        self._make_rx()
        pending = self.repo.list_pending_prescriptions("MAIN")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].branch_code, "MAIN")

    # -- dispense ---

    def test_dispense_success(self):
        rx = self._make_rx("PARA", 10)
        dispensed = self.repo.dispense(rx.id)
        self.assertEqual(dispensed.status, PrescriptionStatus.DISPENSED)
        stock = self.repo.get_stock("PARA", "MAIN")
        self.assertEqual(stock.quantity, 90)  # 100 - 10

    def test_dispense_multi_line(self):
        rx = Prescription("PT-001", "MAIN", "DR-OK")
        rx.add_line("PARA", 10)
        rx.add_line("MORPH", 3)
        rx = self.repo.save_prescription(rx)
        self.repo.dispense(rx.id)
        self.assertEqual(self.repo.get_stock("PARA", "MAIN").quantity, 90)
        self.assertEqual(self.repo.get_stock("MORPH", "MAIN").quantity, 17)

    def test_dispense_insufficient_stock_rolls_back(self):
        rx = self._make_rx("PARA", 999)  # more than 100 in stock
        with self.assertRaises(InsufficientStockError):
            self.repo.dispense(rx.id)
        # Stock must be unchanged
        self.assertEqual(self.repo.get_stock("PARA", "MAIN").quantity, 100)
        # Prescription must still be pending
        reloaded = self.repo.get_prescription(rx.id)
        self.assertEqual(reloaded.status, PrescriptionStatus.PENDING)

    def test_dispense_unauthorised_prescriber_rejected(self):
        rx = self._make_rx("MORPH", 1, prescriber="DR-BAD")
        with self.assertRaises(UnauthorisedPrescriberError):
            self.repo.dispense(rx.id)

    def test_dispense_nonexistent_raises(self):
        with self.assertRaises(DomainError):
            self.repo.dispense(9999)

    def test_dispense_already_dispensed_rejected(self):
        rx = self._make_rx("PARA", 1)
        self.repo.dispense(rx.id)
        with self.assertRaises(InvalidPrescriptionStateError):
            self.repo.dispense(rx.id)

    # -- cancel ---

    def test_cancel_success(self):
        rx = self._make_rx()
        cancelled = self.repo.cancel_prescription(rx.id)
        self.assertEqual(cancelled.status, PrescriptionStatus.CANCELLED)

    def test_cancel_then_dispense_rejected(self):
        rx = self._make_rx()
        self.repo.cancel_prescription(rx.id)
        with self.assertRaises(InvalidPrescriptionStateError):
            self.repo.dispense(rx.id)

    def test_cancel_nonexistent_raises(self):
        with self.assertRaises(DomainError):
            self.repo.cancel_prescription(9999)

    def test_cancel_already_cancelled_rejected(self):
        rx = self._make_rx()
        self.repo.cancel_prescription(rx.id)
        with self.assertRaises(InvalidPrescriptionStateError):
            self.repo.cancel_prescription(rx.id)


class TestTransferStock(RepositoryTestCase):
    """Stock transfer between branches."""

    def setUp(self):
        super().setUp()
        self.repo.save_medicine(OrdinaryMedicine("MED1", "Drug 1", 100.0, 10))
        self.repo.save_branch(Branch("A", "Branch A"))
        self.repo.save_branch(Branch("B", "Branch B"))
        self.repo.receive_stock("MED1", "A", 50)

    def test_transfer_success(self):
        self.repo.transfer_stock("MED1", "A", "B", 20)
        self.assertEqual(self.repo.get_stock("MED1", "A").quantity, 30)
        self.assertEqual(self.repo.get_stock("MED1", "B").quantity, 20)

    def test_transfer_insufficient_stock_rolls_back(self):
        with self.assertRaises(InsufficientStockError):
            self.repo.transfer_stock("MED1", "A", "B", 100)
        # Both branches unchanged
        self.assertEqual(self.repo.get_stock("MED1", "A").quantity, 50)
        self.assertEqual(self.repo.get_stock("MED1", "B").quantity, 0)

    def test_transfer_to_branch_with_existing_stock(self):
        self.repo.receive_stock("MED1", "B", 10)
        self.repo.transfer_stock("MED1", "A", "B", 5)
        self.assertEqual(self.repo.get_stock("MED1", "A").quantity, 45)
        self.assertEqual(self.repo.get_stock("MED1", "B").quantity, 15)


class TestAllowListRepository(RepositoryTestCase):
    """Allow-list persistence."""

    def test_authorise_and_load(self):
        self.repo.authorise_prescriber("DR-X")
        al = self.repo.load_allow_list()
        self.assertTrue(al.is_authorised("DR-X"))

    def test_idempotent_insert(self):
        self.repo.authorise_prescriber("DR-X")
        self.repo.authorise_prescriber("DR-X")  # INSERT OR IGNORE
        al = self.repo.load_allow_list()
        self.assertEqual(list(al), ["DR-X"])

    def test_empty_allow_list(self):
        al = self.repo.load_allow_list()
        self.assertFalse(al.is_authorised("ANYONE"))


# ===========================================================================
# Integration / end-to-end scenario tests
# ===========================================================================


class TestEndToEndScenarios(RepositoryTestCase):
    """Full workflow scenarios that exercise multiple layers together."""

    def setUp(self):
        super().setUp()
        self.repo.save_branch(Branch("MAIN", "Main Campus"))
        self.repo.save_branch(Branch("ANNEX", "Annex Clinic"))
        self.repo.save_medicine(OrdinaryMedicine("PARA500", "Paracetamol 500mg", 200.0, 50))
        self.repo.save_medicine(ControlledMedicine("MORPH10", "Morphine 10mg", 1500.0, 10))
        self.repo.receive_stock("PARA500", "MAIN", 100)
        self.repo.receive_stock("MORPH10", "MAIN", 20)
        self.repo.authorise_prescriber("DR-ALLOWED")

    def test_full_dispense_flow(self):
        """Register -> stock -> prescribe -> dispense -> verify stock reduced."""
        rx = Prescription("PT-001", "MAIN", "DR-ALLOWED")
        rx.add_line("PARA500", 10)
        rx.add_line("MORPH10", 2)
        rx = self.repo.save_prescription(rx)
        dispensed = self.repo.dispense(rx.id)
        self.assertEqual(dispensed.status, PrescriptionStatus.DISPENSED)
        self.assertEqual(self.repo.get_stock("PARA500", "MAIN").quantity, 90)
        self.assertEqual(self.repo.get_stock("MORPH10", "MAIN").quantity, 18)

    def test_atomic_rollback_multi_line(self):
        """If 2nd line fails, 1st line's stock reduction is also rolled back."""
        rx = Prescription("PT-001", "MAIN", "DR-ALLOWED")
        rx.add_line("PARA500", 5)     # would succeed on its own
        rx.add_line("MORPH10", 999)   # will fail: insufficient stock
        rx = self.repo.save_prescription(rx)
        with self.assertRaises(InsufficientStockError):
            self.repo.dispense(rx.id)
        # BOTH medicines' stock must be unchanged
        self.assertEqual(self.repo.get_stock("PARA500", "MAIN").quantity, 100)
        self.assertEqual(self.repo.get_stock("MORPH10", "MAIN").quantity, 20)

    def test_transfer_then_low_stock_report(self):
        """Transfer enough stock out to trigger the low-stock report."""
        self.repo.transfer_stock("PARA500", "MAIN", "ANNEX", 70)
        # MAIN now has 30, reorder is 50 => low
        low = self.repo.list_low_stock("MAIN")
        low_codes = [m.code for m, _ in low]
        self.assertIn("PARA500", low_codes)

    def test_cancel_does_not_affect_stock(self):
        """Cancelling a prescription must NOT touch stock levels."""
        rx = Prescription("PT-001", "MAIN", "DR-ALLOWED")
        rx.add_line("PARA500", 10)
        rx = self.repo.save_prescription(rx)
        self.repo.cancel_prescription(rx.id)
        self.assertEqual(self.repo.get_stock("PARA500", "MAIN").quantity, 100)

    def test_dispense_pending_list_shrinks(self):
        """After dispensing, the prescription is no longer in the pending list."""
        rx = Prescription("PT-001", "MAIN", "DR-ALLOWED")
        rx.add_line("PARA500", 1)
        rx = self.repo.save_prescription(rx)
        self.assertEqual(len(self.repo.list_pending_prescriptions()), 1)
        self.repo.dispense(rx.id)
        self.assertEqual(len(self.repo.list_pending_prescriptions()), 0)

    def test_persistence_across_reopen(self):
        """Data survives closing and reopening the repository on the same file."""
        rx = Prescription("PT-001", "MAIN", "DR-ALLOWED")
        rx.add_line("PARA500", 1)
        rx = self.repo.save_prescription(rx)
        self.repo.dispense(rx.id)

        # Close and reopen using the path we saved in setUp
        db_path = self._tmp.name
        self.repo.close()
        repo2 = InventoryRepository(db_path)
        try:
            self.assertEqual(repo2.get_stock("PARA500", "MAIN").quantity, 99)
            reloaded = repo2.get_prescription(rx.id)
            self.assertEqual(reloaded.status, PrescriptionStatus.DISPENSED)
        finally:
            repo2.close()
        # Re-assign so tearDown still works
        self.repo = InventoryRepository(db_path)


if __name__ == "__main__":
    unittest.main()
